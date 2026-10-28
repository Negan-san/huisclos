@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if exist ".venv-toolkit\Scripts\python.exe" (
    ".venv-toolkit\Scripts\python.exe" "scripts\toolkit_launcher.py" %*
    goto finished
)
py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)" >nul 2>&1
if not errorlevel 1 (
    py -3.12 "scripts\toolkit_launcher.py" %*
    goto finished
)
python -c "import sys; assert sys.version_info[:2] == (3, 12)" >nul 2>&1
if not errorlevel 1 (
    python "scripts\toolkit_launcher.py" %*
    goto finished
)
echo Python 3.12 64-bit is required. Install it from https://www.python.org/downloads/
echo Enable the Python launcher or Add python.exe to PATH, then reopen this file.
echo See START_HERE.md for the installation steps.
pause
exit /b 1
:finished
set "huisclos_exit=%errorlevel%"
if not "%huisclos_exit%"=="0" (
    echo HuisClos stopped with an error. See the message above and START_HERE.md.
    pause
)
exit /b %huisclos_exit%
