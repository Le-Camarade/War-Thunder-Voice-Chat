@echo off
echo === War Thunder Voice Chat - Build ===
echo.

REM Check if pyinstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building executable...
pyinstaller build.spec --noconfirm

echo.
if exist "dist\WT-VoiceChat.exe" (
    echo Build successful!
    echo Executable: dist\WT-VoiceChat.exe
) else (
    echo Build failed!
)

echo.
pause
