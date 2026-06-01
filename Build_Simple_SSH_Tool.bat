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

echo.
REM Force qtpy/pywebview to use PySide6 (in case PyQt6 is still installed)
set QT_API=pyside6

echo Installing dependencies ...
pip install pyinstaller pywebview PySide6 paramiko

echo.
echo Building Simple SSH Tool ...
echo.

pyinstaller --noconfirm --onedir --windowed ^
  --add-data "simple_ssh_tool-UI.html;." ^
  --add-data "icon.png;." ^
  --splash "splash.png" ^
  --icon "icon.ico" ^
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
pause
