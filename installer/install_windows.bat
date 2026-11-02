@echo off
rem Source games for PS4: installer for Windows. Needs Python 3 (https://www.python.org/downloads/).
cd /d "%~dp0"
where py >nul 2>nul && (py -3 sourceeng_install.py %* & goto done)
where python >nul 2>nul && (python sourceeng_install.py %* & goto done)
echo Python 3 is not installed. Get it from https://www.python.org/downloads/
echo (tick "Add python.exe to PATH" during setup), then run this file again.
:done
pause
