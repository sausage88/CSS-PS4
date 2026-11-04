# Counter-Strike: Source for PlayStation 4 🎯

**Two legends, finally together: Counter-Strike: Source and PlayStation 4.** The shooter that defined a generation of PC gaming, running natively on the console that defined a generation of living rooms.

Counter-Strike: Source never came to PlayStation. For twenty years the most played Source game stayed behind a keyboard and mouse while console players watched from the other side of the fence. That ends here.

This is an unofficial, native 64-bit port of Counter-Strike: Source for jailbroken PlayStation 4 consoles. Not an emulator, not a stream: the real Source engine and the real CS:S client, running on the PS4's own CPU and GPU. And it is not a museum piece. You join **live community servers**, the same ones PC players are on tonight: de_dust2 at 3 AM, surf, jailbreak, zombie, AWP maps, all of it.

> Built on the same engine work as the [Half-Life 2 port for PS4](https://github.com/sausage88/SourceEngine).

> 🧪 **Early release.** This port has not been through full testing. Expect bugs: crashes, servers that refuse to connect, graphical glitches. Reports help a lot (see *Contact* below), and the game sends anonymous crash reports by itself.

---

## ⚡ Why This One Is Different

* **Real online play.** The CS:S v34 client (protocol 7). The in-game server browser finds hundreds of community servers; pick one and play.
* **Custom content just works.** Servers send their maps, models, sounds and sprites over FastDL, the same way they do on PC. If a map you copied from Steam differs from the server's, the game sets it aside and downloads the server's version by itself.
* **A controller layout made for a shooter.** Your right thumb never leaves the stick:
  * R2 fire, L1 or Cross jump, L2 crouch (snipers scope while held, or toggle the scope; your choice in Options), R3 knife.
  * D-pad picks weapons. Square reloads; hold it to use, defuse or plant.
  * Touchpad: left half shows the scoreboard, right half opens the buy menu. Hold the right half and press the D-pad for **one-touch buy presets**.
  * Tilt the left stick lightly to walk silently.
* **Gyro aiming** with the DualShock 4: always on, or only while L2 is held.
* **Fair play.** No aim assist online. You win with your hands, not with help from the game.
* **Your settings, on the console.** Crosshair thickness, size, colour and dot, stick curve and dead zones, gyro speed, crouch toggle or hold, frame rate, VSync. There is an Options screen with a drawn **Controls** page that shows the whole layout.
* **Your name in the scoreboard.** Typed with the console's own on-screen keyboard.
* **60 fps on most maps.** Very heavy community maps can drop lower; we keep working on it.

---

## ⚠️ Read Before Installing: No Game Content Included

The PKG contains **only** the engine and client binaries, a few configuration files, and the home-screen icon and background.
* **No game content** (maps, models, textures, sounds) from Valve is included.
* You **must** use your own files from legally purchased copies of **Counter-Strike: Source** and **Half-Life 2** on Steam.

---

## 🚀 Installation

You need: a PS4 with **GoldHEN**, a Windows PC or a Mac, and a Steam account that owns **Counter-Strike: Source** and **Half-Life 2**.

### The easy way: the installer (recommended)

1. From the **Releases** section of this repository download `SourceEngCSS.pkg` and the installer for your computer:
   `CSS-PS4-Installer-Windows.exe` or `CSS-PS4-Installer-Mac.zip`.
2. Install the PKG on the PS4 with GoldHEN: **Settings → Debug Settings → Game → Package Installer**.
3. On the PS4, turn on the GoldHEN **FTP server** (GoldHEN menu → Server Settings → FTP).
4. Run the installer on your computer and answer its questions. It:
   * finds your PS4 on the network by itself;
   * downloads the right versions of your games with **SteamCMD**, Valve's official command-line Steam client.
     You type your Steam password and Steam Guard code into SteamCMD itself: the installer never sees or keeps them;
   * checks the files and uploads them to the PS4. If something breaks off, run it again: it continues where it
     stopped.
5. Start **Counter-Strike: Source** on the PS4.

The download is about 10 GB, and the upload over Wi-Fi takes a while. The next time the installer remembers your
answers (never your password).

> **Windows:** SmartScreen may say *"Windows protected your PC"*, because the installer is not signed. Click
> **More info → Run anyway**.
>
> **Mac (Apple Silicon):** unzip, then right-click the file → **Open** → **Open**. If macOS still blocks it:
> System Settings → Privacy & Security → **Open Anyway**. SteamCMD needs Rosetta; the installer tells you if it is
> missing. On an Intel Mac, or if you prefer, run `installer/install_mac.command` from this repository (needs Python 3).

If the PS4 shows its help screen (*"No games found"* or *"… not found"*), scan its QR code with your phone: it opens this page.

### The manual way

You can do the same by hand.

In the end the console must have exactly this:

```
/data/sourceeng/cstrike     ← from Counter-Strike: Source (Steam)
/data/sourceeng/platform    ← from Counter-Strike: Source (Steam)
/data/sourceeng/hl2         ← from Half-Life 2, LINUX version, beta steam_legacy
```

### Step 1. Install Counter-Strike: Source on your PC
1. Install **Counter-Strike: Source** from Steam as usual.
2. In Steam: right-click the game → **Manage → Browse local files**. Keep this folder open. You will need two folders from it: `cstrike` and `platform`.

> ❗ Do **not** use the `hl2` folder you see in there. It belongs to the new 20th Anniversary engine and will not work.

### Step 2. Download the Linux version of Half-Life 2 (steam_legacy)
The PS4 runs the Linux build of the game, and only the Linux `hl2` folder has the shaders it needs. Steam on Windows downloads the Windows files, so use **SteamCMD**, Valve's official command-line Steam client:

1. Download SteamCMD for Windows: <https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip>
2. Unpack it to `C:\steamcmd`.
3. Open **Command Prompt** (press Win+R, type `cmd`, press Enter) and run:
   ```
   cd C:\steamcmd
   steamcmd +@sSteamCmdForcePlatformType linux +force_install_dir C:\hl2_linux +login YOUR_STEAM_LOGIN +app_update 220 -beta steam_legacy validate +quit
   ```
   Replace `YOUR_STEAM_LOGIN` with your Steam login. SteamCMD asks for your password and, if you use it, the Steam Guard code.
4. Wait until it says `Success! App '220' fully installed.` The folder you need is now `C:\hl2_linux\hl2`.

### Step 3. Install the PKG on the PS4
1. Download `SourceEngCSS.pkg` from the **Releases** section of this repository.
2. Put it on a USB stick (FAT32 or exFAT) or send it to the console over FTP.
3. Install it with GoldHEN: **Settings → Debug Settings → Game → Package Installer**.

### Step 4. Copy the game files to the PS4
1. On the PS4, enable the GoldHEN **FTP server** (GoldHEN menu → Server Settings → FTP).
2. Find the console's IP address: **Settings → Network → View Connection Status**.
3. On the PC, open an FTP client such as [FileZilla](https://filezilla-project.org/) and connect:
   * Host: the PS4's IP address
   * Port: `2121`
   * No user name or password.
4. Go to `/data/` and create a folder named **`sourceeng`**.
5. Upload into `/data/sourceeng/`:
   * `cstrike` and `platform` from Step 1;
   * `hl2` from `C:\hl2_linux\hl2` (Step 2).

   This is several gigabytes. Wait until FileZilla reports that every transfer finished.

**Prefer USB?** FTP is not required: the game only needs the folders in `/data/sourceeng/`, however they get there.
Copy them to a USB stick (FAT32 or exFAT), plug it into the PS4 and use a homebrew file manager (for example
Itemzflow) to copy them from `/mnt/usb0/` into `/data/sourceeng/`, keeping the same folder names. The games cannot
run straight from the USB stick. The installer from *The easy way* always uploads over FTP.

### Step 5. Play
1. Start **Counter-Strike: Source** from the PS4 home screen.
2. On the first start the game installs its own `gameinfo.txt`, `steam.inf` and font list into your folders (Steam's originals are kept next to them as `*_steam.*`). You do not need to do anything.
3. Open **Find Servers**, pick a server, and play. Maps, models and sounds the server uses are downloaded automatically.

### Something went wrong?

| What you see | What to do |
|---|---|
| **"Counter-Strike: Source not found"** screen | Read the *Not ready* list on that screen: it names the missing or wrong file. Fix it, press **Cross**, and the game checks again. |
| *"missing … .vpk"* or *"… is short (still copying?)"* | The copy is incomplete. Upload that file again. |
| *"Windows shaders: use the Linux hl2"* | Your `hl2` is the Windows version. Repeat Step 2 and replace the `hl2` folder. |
| *"shaders from the 20th Anniversary version"* | You copied the `hl2` from Counter-Strike: Source. Use the one from Step 2. |
| Black screen in the menu | Same cause: the wrong `hl2`. Repeat Step 2. |

---

## 🛠️ Status & Compatibility

* **PlayStation 4 Slim (GoldHEN):** tested and playable on live servers.
* **Other consoles (original PS4, PS4 Pro, PS5):** not tested. It may work, but nobody has tried yet. If you run it on one of them, please let me know how it went.
* **Known issues:** some community servers disconnect with *"Buffer overflow in net message"*; very heavy maps run below 60 fps; minor graphical glitches on some materials.

---

## 📊 Crash Reports

To find and fix crashes, the game sends **anonymous** crash and hang reports and session counts (launches, play time, crash-free rate) to Sentry. There is no account, console or network information in them: a player is a random ID created on your console.

**To turn it off**, create an empty file `/data/sourceeng/telemetry_off.txt`.

---

## 🗺️ Roadmap

What we want to work on next. These are directions, not promises or dates.

* **Stability on more servers.** Fix the *"Buffer overflow in net message"* disconnect and whatever else the crash reports show.
* **Performance on heavy community maps.** Keep 60 fps where today the busiest maps drop to 20–40.
* **Graphics.** Shading seams on character models at mid distance, light outlines around foliage, flashlight shadows.
* **Trophies.** Counter-Strike: Source achievements as PS4 trophies.
* **More hardware.** Testing on the original PS4, PS4 Pro and PS5; 4K output on PS4 Pro and PS5.
* **Keyboard and mouse** support.
* **Aim assist on servers that allow it.** Only where a server opts in, so nobody gets an edge they did not agree to.

---

## ✉️ Contact
Questions, bug reports, results on other consoles: **apsausage@gmail.com**

---

## ⚖️ Disclaimer
This is a non-commercial fan project. It is not affiliated with, endorsed by, or connected to Valve Corporation or Sony Interactive Entertainment. Counter-Strike, Counter-Strike: Source, Half-Life and Steam are trademarks of Valve Corporation. PlayStation is a trademark of Sony Interactive Entertainment.

---

## Support the Project ☕
If you appreciate my work and want to support the development of this port and future homebrew projects for the PlayStation scene, feel free to drop a donation! It is completely optional but highly appreciated.

* USDT (Network: TRC-20): `TTWDNBNeMJmLyzf5CxhUqrgQynZDgAUZCz`
* Bitcoin (Network: BTC): `1NbMq2pqSR8zdFpLB4H4nQXbxPwzZctaVL`
* Ethereum (Network: ERC-20): `0x93cd7ebc2204a59d6ddd14870470b9069d3666ad`
* Litecoin (Network: LTC): `LN4L3zbrkmGyGKJjG97oWwQXq8ojZSWJAC`

Thank you for supporting the PlayStation Homebrew community! 🎮
