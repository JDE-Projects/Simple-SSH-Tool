@echo off
REM ============================================================
REM  Simple SSH Tool: build the standalone app
REM  https://github.com/JDE-Projects
REM  Double-click this file to build. Output lands in:
REM     dist\Simple SSH Tool\Simple SSH Tool.exe   (a FOLDER)
REM  Distribute the whole "dist\Simple SSH Tool" folder (zipped)
REM  via the repo's Releases page.
REM
REM  Qt binding: PySide6 (LGPL). onedir keeps the Qt libraries as
REM  swappable files beside the exe, which satisfies LGPL for a
REM  closed-source build.
REM ============================================================

cd /d "%~dp0"

REM --- skip interactive pauses when running in CI (GitHub Actions sets CI) ---
set "PAUSE=pause"
if defined CI set "PAUSE="

echo.
REM Force qtpy/pywebview to use PySide6 (in case PyQt6 is still installed)
set QT_API=pyside6

REM --- check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python 3 from https://python.org and tick "Add Python to PATH".
    %PAUSE%
    exit /b 1
)

echo Installing pinned dependencies from requirements.txt ...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies from requirements.txt.
    %PAUSE%
    exit /b 1
)

echo.
echo Building Simple SSH Tool ...
echo.

pyinstaller --noconfirm --onedir --windowed ^
  --add-data "simple_ssh_tool-UI.html;." ^
  --add-data "simple_ssh_tool.png;." ^
  --add-data "fonts;fonts" ^
  --splash "simple_ssh_tool-splash.png" ^
  --icon "simple_ssh_tool.ico" ^
  --collect-all PySide6 ^
  --collect-all qtpy ^
  --name "Simple SSH Tool" ^
  simple_ssh_tool.py

echo.
if exist "dist\Simple SSH Tool\Simple SSH Tool.exe" (
    echo ============================================================
    echo  Build complete:
    echo    dist\Simple SSH Tool\Simple SSH Tool.exe
    echo  Distribute the whole "dist\Simple SSH Tool" folder.
    echo ============================================================
) else (
    echo ============================================================
    echo  Build FAILED. Check the messages above.
    echo ============================================================
)
echo.
%PAUSE%
