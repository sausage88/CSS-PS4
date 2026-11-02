#!/bin/sh
# Source games for PS4: installer for macOS. Double-click, or run: sh install_mac.command
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Run: xcode-select --install   (or get it from https://www.python.org/downloads/)"
  exit 1
fi
if [ "$(uname -m)" = arm64 ] && ! /usr/bin/pgrep -q oahd; then
  echo "SteamCMD for Mac needs Rosetta on Apple Silicon. Run: softwareupdate --install-rosetta"
  exit 1
fi
python3 sourceeng_install.py "$@"
