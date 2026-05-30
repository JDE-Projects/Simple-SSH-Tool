@echo off
REM ============================================================
REM  Simple SSH Tool: build the standalone app
REM  https://github.com/JDE-Projects
REM  Double-click this file to build. Output lands in:
REM     dist\Simple SSH Tool.exe   (a single file)
REM  Distribute that .exe via the repo's Releases page.
REM ============================================================

echo.
echo Building Simple SSH Tool ...
echo.

pyinstaller --noconfirm --onefile --windowed ^
  --add-data "simple_ssh_tool-UI.html;." ^
  --add-data "icon.png;." ^
  --splash "splash.png" ^
  --icon "icon.ico" ^
  --collect-all PyQt6 ^
  --collect-all qtpy ^
  --name "Simple SSH Tool" ^
  simple_ssh_tool.py

echo.
if exist "dist\Simple SSH Tool.exe" (
    echo ============================================================
    echo  Build complete:
    echo    dist\Simple SSH Tool.exe
    echo ============================================================
) else (
    echo ============================================================
    echo  Build FAILED. Check the messages above.
    echo ============================================================
)
echo.
pause
