#!/usr/bin/env python3
"""Installer for the Source games on PS4 (Counter-Strike: Source for PS4, Orange Box SP for PS4).

Runs on the player's PC or Mac, Python 3.8+, standard library only:
  1. gets Valve's SteamCMD (official Steam command-line client) if it is not there yet;
  2. runs SteamCMD to download the player's own games in the versions the port needs (hl2: Linux, steam_legacy).
     The player types the Steam password and Steam Guard code into SteamCMD itself; this script never sees them;
  3. checks the files the way the console does (orbis_gamelist.cpp: whole VPKs, Linux steam_legacy shaders);
  4. uploads the game folders to /data/sourceeng on the PS4 over GoldHEN's FTP, skipping files already there.

  python3 sourceeng_install.py                       asks for everything
  python3 sourceeng_install.py --edition css --ps4 192.168.1.50 --steam-user NAME
"""
import argparse, ftplib, ipaddress, json, os, platform, re, socket, struct, subprocess, sys, tarfile, time
import urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor

STEAMCMD_URL = {
    'Windows': 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip',
    'Darwin': 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_osx.tar.gz',
    'Linux': 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz',
}

# key: (title, Steam app id, platform, beta, folders to upload from the install dir). Half-Life 2 and both episodes
# have steam_legacy ("Pre-20th Anniversary Build"); their public builds are the 20th Anniversary one, which the port
# cannot use, so there is no fallback. Portal and Half-Life: Source have no such branch (app_info_print, 2026-11-02).
# Counter-Strike: Source is Steam's current build: only its cstrike and platform are used.
GAMES = {
    'hl2':     ('Half-Life 2',              220, 'linux',   'steam_legacy', ['hl2', 'platform']),
    'css':     ('Counter-Strike: Source',   240, 'windows', None,           ['cstrike', 'platform']),
    'ep1':     ('Half-Life 2: Episode One', 380, 'linux',   'steam_legacy', ['episodic']),
    'ep2':     ('Half-Life 2: Episode Two', 420, 'linux',   'steam_legacy', ['ep2']),
    'portal':  ('Portal',                   400, 'linux',   None,           ['portal']),
    'hls':     ('Half-Life: Source',        280, 'linux',   None,           ['hl1']),
}
EDITIONS = {
    'css': ('Counter-Strike: Source for PS4', ['css', 'hl2'], []),
    'sp':  ('Orange Box SP for PS4', ['hl2'], ['ep1', 'ep2', 'portal', 'hls']),
}
REMOTE_ROOT = '/data/sourceeng'
FTP_PORT = 2121


def say(*a):
    print(*a, flush=True)


def ask(prompt, default=None):
    s = input('%s%s: ' % (prompt, ' [%s]' % default if default else '')).strip()
    return s or default


def yes(prompt, default=True):
    s = input('%s [%s]: ' % (prompt, 'Y/n' if default else 'y/N')).strip().lower()
    return default if not s else s.startswith('y')


# ---------------------------------------------------------------- SteamCMD

def need_rosetta():
    """SteamCMD for Mac is an Intel program: on Apple Silicon it runs through Rosetta."""
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        return False
    try:
        return subprocess.call(['/usr/bin/arch', '-x86_64', '/usr/bin/true'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0
    except OSError:
        return True


def steamcmd_path(work):
    if need_rosetta():
        sys.exit('SteamCMD needs Rosetta on this Mac. Open Terminal and run:\n'
                 '  softwareupdate --install-rosetta --agree-to-license\n'
                 'then start the installer again.')
    d = os.path.join(work, 'steamcmd')
    exe = os.path.join(d, 'steamcmd.exe' if platform.system() == 'Windows' else 'steamcmd.sh')
    if os.path.exists(exe):
        return exe
    url = STEAMCMD_URL.get(platform.system())
    if not url:
        sys.exit('This system is not supported by SteamCMD: %s' % platform.system())
    os.makedirs(d, exist_ok=True)
    say('Downloading SteamCMD from Valve: %s' % url)
    arc = os.path.join(d, os.path.basename(url))
    urllib.request.urlretrieve(url, arc)
    if arc.endswith('.zip'):
        with zipfile.ZipFile(arc) as z:
            z.extractall(d)
    else:
        with tarfile.open(arc) as t:
            t.extractall(d)
    os.remove(arc)
    if not exe.endswith('.exe'):
        os.chmod(exe, 0o755)
    # The first start updates SteamCMD itself; on macOS the restart after that update can crash (heap corruption in
    # Valve's client), the next start is fine. Do it here, before the player types a password.
    say('Updating SteamCMD (first start)...')
    for _ in range(3):
        if subprocess.call([exe, '+quit'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            break
    return exe


def steamcmd_crashed(rc):
    return rc < 0 or rc in (134, 139)  # killed by a signal (via steamcmd.sh: 128 + SIGABRT / SIGSEGV)


def steamcmd_download(exe, user, key, dest):
    title, appid, plat, beta, folders = GAMES[key]
    args = [exe, '+@sSteamCmdForcePlatformType', plat, '+force_install_dir', os.path.abspath(dest),
            '+login', user, '+app_update', str(appid)]
    if beta:
        args += ['-beta', beta]
    args += ['validate', '+quit']
    say('\n=== %s: SteamCMD (%s%s) ===' % (title, plat, ', ' + beta if beta else ''))
    say('If SteamCMD asks for your password or Steam Guard code, type it there.')
    # SteamCMD talks to the player directly: same terminal, its own prompts.
    rc = subprocess.call(args)
    for _ in range(2):
        if not steamcmd_crashed(rc):
            break
        say('SteamCMD crashed (code %d); starting it again.' % rc)
        rc = subprocess.call(args)
    return rc == 0 and all(os.path.isdir(os.path.join(dest, f)) for f in folders)


# ---------------------------------------------------------------- checks (as orbis_gamelist.cpp on the console)

def vpk_check(dirs, rel, want=None):
    """dirs: {"hl2": local folder, ...}; rel: "hl2/hl2_misc". -> (why or None, entry (arc, off, len) of `want`)."""
    top, name = rel.split('/', 1)
    base = os.path.join(dirs.get(top, os.path.join('__missing__', top)), name)
    path = base + '_dir.vpk'
    if not os.path.exists(path):
        return 'missing %s_dir.vpk' % rel, None
    with open(path, 'rb') as f:
        b = f.read()
    if len(b) < 12:
        return '%s_dir.vpk is damaged' % rel, None
    sig, ver, tree = struct.unpack_from('<III', b)
    start = 28 if ver == 2 else 12
    if sig != 0x55AA1234 or start + tree > len(b):
        return '%s_dir.vpk is damaged' % rel, None
    end_tree = start + tree
    p = start
    ends = {}
    found = None

    def s():
        nonlocal p
        z = b.index(b'\0', p, end_tree) if b'\0' in b[p:end_tree] else end_tree
        r = b[p:z].decode('utf-8', 'replace')
        p = z + 1
        return r
    while p < end_tree:
        ext = s()
        if not ext:
            break
        while p < end_tree:
            d = s()
            if not d:
                break
            while p + 18 <= end_tree:
                name = s()
                if not name or p + 18 > end_tree:
                    break
                pre, arc, off, ln = struct.unpack_from('<HHII', b, p + 4)
                p += 18 + pre
                if want and found is None and not pre and '%s/%s.%s' % (d, name, ext) == want:
                    found = (arc, off, ln)
                if arc != 0x7FFF and ln:
                    ends[arc] = max(ends.get(arc, 0), off + ln)
    for arc, e in sorted(ends.items()):
        a = '%s_%03d.vpk' % (base, arc)
        if not os.path.exists(a):
            return 'missing %s_%03d.vpk' % (rel, arc), found
        if os.path.getsize(a) < e:
            return '%s_%03d.vpk is short (download incomplete?)' % (rel, arc), found
    return None, found


def shaders_check(dirs):
    why, e = vpk_check(dirs, 'hl2/hl2_misc', 'shaders/fxc/vertexlit_and_unlit_generic_vs20.vcs')
    if why or not e:
        return why
    with open(os.path.join(dirs['hl2'], 'hl2_misc_%03d.vpk' % e[0]), 'rb') as f:
        f.seek(e[1])
        head = struct.unpack('<7I', f.read(28))
    if head[1] != 0x18000:
        return 'hl2 shaders are from the 20th Anniversary version: need the steam_legacy hl2'
    if head[6] != 0x25AAA054:
        return 'hl2 shaders are the Windows ones: need the Linux hl2 (steam_legacy)'
    return None


def check(dirs, edition):
    """dirs: {"hl2": folder, "platform": folder, "cstrike": folder, ...} as they will be on the console.
    -> list of problems."""
    if edition == 'css':
        vpks = ['cstrike/cstrike_pak', 'hl2/hl2_textures', 'hl2/hl2_misc', 'hl2/hl2_sound_misc',
                'platform/platform_misc']
    else:
        vpks = ['hl2/hl2_pak', 'hl2/hl2_textures', 'hl2/hl2_misc', 'hl2/hl2_sound_misc',
                'hl2/hl2_sound_vo_english', 'platform/platform_misc']
    bad = [w for w in (vpk_check(dirs, r)[0] for r in vpks) if w]
    if not bad:
        w = shaders_check(dirs)
        if w:
            bad.append(w)
    return bad


# ---------------------------------------------------------------- FTP upload

# ---------------------------------------------------------------- finding the PS4

def local_networks():
    """The /24 networks of this computer's private IPv4 addresses (from ipconfig / ifconfig: a VPN may own the
    default route, so the address of the route to the internet is not enough)."""
    cmd = ['ipconfig'] if platform.system() == 'Windows' else ['ifconfig']
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        out = ''
    nets = []
    for a in re.findall(r'(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])', out):
        try:
            ip = ipaddress.IPv4Address(a)
        except ValueError:
            continue
        if ip in ipaddress.IPv4Network('198.18.0.0/15'):
            continue  # benchmark range VPN clients use for their tunnel, not a home network
        if ip.is_private and not ip.is_loopback and not ip.is_link_local and str(ip).split('.')[-1] not in ('0', '255'):
            n = ipaddress.IPv4Network(str(ip) + '/24', strict=False)
            if n not in nets:
                nets.append(n)
    return nets


def ftp_banner(host, timeout=0.5):
    try:
        with socket.create_connection((host, FTP_PORT), timeout=timeout) as s:
            s.settimeout(1.5)
            return s.recv(200).decode('ascii', 'replace').strip()
    except OSError:
        return None


def find_ps4():
    """-> [(ip, banner)] of the FTP servers on port FTP_PORT in the local networks, GoldHEN's first."""
    hosts = [str(h) for n in local_networks() for h in n.hosts()]
    if not hosts:
        return []
    say('Looking for the PS4 on your network (%d addresses)...' % len(hosts))
    with ThreadPoolExecutor(max_workers=128) as pool:
        banners = list(pool.map(ftp_banner, hosts))
    found = [(h, b) for h, b in zip(hosts, banners) if b and b.startswith('220')]
    found.sort(key=lambda f: 'goldhen' not in f[1].lower())
    return found


def pick_ps4(saved):
    if saved and ftp_banner(saved, 2):
        say('PS4: %s (from the last run)' % saved)
        return saved
    found = find_ps4()
    if len(found) == 1:
        say('PS4 found: %s (%s)' % found[0])
        return found[0][0]
    if len(found) > 1:
        for i, (h, b) in enumerate(found, 1):
            say('  %d. %s  %s' % (i, h, b))
        while True:
            c = ask('Which one is the PS4? Number or IP address', '1')
            if c.isdigit() and 1 <= int(c) <= len(found):
                return found[int(c) - 1][0]
            if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', c):
                return c
    say('No PS4 found. On the PS4 turn on the GoldHEN FTP server (GoldHEN menu > Server Settings > FTP),\n'
        'and check that the PC and the PS4 are on the same network.')
    return ask('PS4 IP address (PS4: Settings > Network > View Connection Status), or Enter to search again') or \
        pick_ps4(None)


# ---------------------------------------------------------------- settings of the last run (no passwords)

def load_settings(work):
    try:
        with open(os.path.join(work, 'settings.json')) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(work, d):
    try:
        os.makedirs(work, exist_ok=True)
        with open(os.path.join(work, 'settings.json'), 'w') as f:
            json.dump(d, f, indent=1)
    except OSError:
        pass


def ftp_connect(host):
    f = ftplib.FTP()
    f.connect(host, FTP_PORT, timeout=30)
    f.login()  # GoldHEN takes any user
    f.set_pasv(True)
    return f


def ftp_size(f, path):
    try:
        f.voidcmd('TYPE I')
        r = f.size(path)
        return r if r is not None else -1
    except ftplib.all_errors:
        return -1


def ftp_mkdirs(f, path, made):
    parts = path.strip('/').split('/')
    cur = ''
    for p in parts:
        cur += '/' + p
        if cur in made:
            continue
        try:
            f.mkd(cur)
        except ftplib.error_perm:
            pass  # already there
        made.add(cur)


def upload(host, uploads):
    """uploads: list of (local folder, remote folder)."""
    files = []
    for local, remote in uploads:
        for d, _, names in os.walk(local):
            for n in names:
                lp = os.path.join(d, n)
                rel = os.path.relpath(lp, local).replace(os.sep, '/')
                files.append((lp, remote + '/' + rel, os.path.getsize(lp)))
    total = sum(s for _, _, s in files)
    say('\nUploading %d files, %.1f GB, to %s:%d%s' % (len(files), total / 1e9, host, FTP_PORT, REMOTE_ROOT))
    f = ftp_connect(host)
    made = set()
    done = sent = skipped = 0
    t0 = time.time()
    for i, (lp, rp, size) in enumerate(files):
        for attempt in range(3):
            try:
                if ftp_size(f, rp) == size:
                    skipped += 1
                    break
                ftp_mkdirs(f, rp.rsplit('/', 1)[0], made)
                with open(lp, 'rb') as fh:
                    f.storbinary('STOR ' + rp, fh, blocksize=1 << 20)
                sent += size
                break
            except (ftplib.all_errors + (OSError,)) as e:
                if attempt == 2:
                    sys.exit('\nUpload of %s failed: %s\nRun the installer again: it continues where it stopped.' % (rp, e))
                time.sleep(2)
                try:
                    f.close()
                except Exception:
                    pass
                f = ftp_connect(host)
        done += size
        rate = sent / max(1e-3, time.time() - t0)
        sys.stdout.write('\r  %5.1f%%  %d/%d files  %.1f MB/s   ' % (100.0 * done / max(1, total), i + 1, len(files),
                                                                 rate / 1e6))
        sys.stdout.flush()
    f.quit()
    say('\nUpload finished (%d files already on the console were skipped).' % skipped)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--edition', choices=EDITIONS)
    ap.add_argument('--ps4', help='PS4 IP address (GoldHEN FTP on port %d)' % FTP_PORT)
    ap.add_argument('--steam-user', help='Steam login name (the password is typed into SteamCMD)')
    ap.add_argument('--games', help='Orange Box SP: extra games, comma separated: ' + ','.join(EDITIONS['sp'][2]))
    ap.add_argument('--work', default=os.path.join(os.path.expanduser('~'), 'SourceEngPS4'),
                    help='where SteamCMD and the downloads go (default: %(default)s)')
    ap.add_argument('--check-only', metavar='DIR', help='only check a folder laid out as /data/sourceeng')
    ap.add_argument('--no-upload', action='store_true', help='download and check, do not upload')
    a = ap.parse_args()

    if a.check_only:
        root = a.check_only
        bad = check({n: os.path.join(root, n) for n in os.listdir(root)}, a.edition or 'sp')
        say('\n'.join(bad) if bad else 'OK')
        return 1 if bad else 0

    say('Source games for PS4: installer\n')
    last = load_settings(a.work)
    edition = a.edition
    while edition not in EDITIONS:
        edition = ask('Which app? css = Counter-Strike: Source, sp = Orange Box SP',
                      last.get('edition') or edition_from_name() or 'css')
    title, need, extra = EDITIONS[edition]
    games = list(need)
    if edition == 'sp':
        if a.games is not None:
            games += [g for g in a.games.split(',') if g in extra]
        else:
            had = last.get('games', [])
            for g in extra:
                if yes('Also %s (you must own it on Steam)?' % GAMES[g][0], g in had):
                    games.append(g)
    host = a.ps4 or (None if a.no_upload else pick_ps4(last.get('ps4')))
    user = a.steam_user or ask('Steam login name', last.get('steam_user'))
    if not user:
        sys.exit('A Steam login name is needed.')

    if host:
        try:
            ftp_connect(host).quit()
        except ftplib.all_errors + (OSError,) as e:
            sys.exit('Cannot reach the PS4 over FTP (%s). Turn on the GoldHEN FTP server and check the IP.' % e)
    save_settings(a.work, {'edition': edition, 'games': games, 'ps4': host or last.get('ps4'), 'steam_user': user})

    os.makedirs(a.work, exist_ok=True)
    exe = steamcmd_path(a.work)
    dirs = {}
    for g in games:
        dest = os.path.join(a.work, 'steam_' + g)
        if not steamcmd_download(exe, user, g, dest):
            sys.exit('\n%s was not downloaded.\n'
                     '  If SteamCMD said "No subscription": this Steam account does not own %s. Buy it on Steam,\n'
                     '  or log in with the account that owns it.\n'
                     '  Otherwise (network, disk space, Steam Guard): run the installer again, it continues.'
                     % (GAMES[g][0], GAMES[g][0]))
        dirs[g] = dest

    # What lands in /data/sourceeng: hl2 and platform from the Linux steam_legacy hl2, the other games' folders from
    # their own downloads. Counter-Strike: Source's own hl2 is the 20th Anniversary engine's and is never used.
    uploads = [(os.path.join(dirs['hl2'], 'hl2'), REMOTE_ROOT + '/hl2')]
    if edition == 'css':
        uploads += [(os.path.join(dirs['css'], 'cstrike'), REMOTE_ROOT + '/cstrike'),
                    (os.path.join(dirs['css'], 'platform'), REMOTE_ROOT + '/platform')]
    else:
        uploads.append((os.path.join(dirs['hl2'], 'platform'), REMOTE_ROOT + '/platform'))
        for g in games:
            if g != 'hl2':
                for folder in GAMES[g][4]:
                    uploads.append((os.path.join(dirs[g], folder), REMOTE_ROOT + '/' + folder))

    # Check the files as the console will see them.
    bad = check({remote.rsplit('/', 1)[1]: local for local, remote in uploads}, edition)
    if bad:
        sys.exit('The downloaded files are not right:\n  ' + '\n  '.join(bad))
    say('\nFiles checked: OK.')

    if host and not a.no_upload:
        upload(host, uploads)
        say('\nDone. Start %s on the PS4.' % title)
    else:
        say('\nDone. Files are in %s' % a.work)
    return 0


def edition_from_name():
    """The release builds are named after their app (CSS-PS4-Installer, OrangeBox-PS4-Installer): that app first."""
    n = os.path.basename(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]).lower()
    return 'sp' if 'orange' in n else 'css' if 'css' in n else None


def run():
    code = 0
    try:
        code = main()
    except KeyboardInterrupt:
        code = '\nStopped. Run the installer again to continue.'
    except SystemExit as e:
        code = e.code
    # A double-clicked build closes its window at exit: keep it open to show how it ended.
    if getattr(sys, 'frozen', False):
        if isinstance(code, str):
            print(code, flush=True)
            code = 1
        try:
            input('\nPress Enter to close.')
        except EOFError:
            pass
    sys.exit(code)


if __name__ == '__main__':
    run()
