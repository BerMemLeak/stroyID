@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1"
set "STROYID_BUILD_EXIT=%ERRORLEVEL%"
echo.
if not "%STROYID_BUILD_EXIT%"=="0" echo Build failed. Send the newest file from the logs folder.
pause
exit /b %STROYID_BUILD_EXIT%
