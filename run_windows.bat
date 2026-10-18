@echo off
setlocal
cd /d "%~dp0"
if exist release\StroyID.exe (
 start "" "%~dp0release\StroyID.exe"
 exit /b 0
)
call build_windows.bat
exit /b %ERRORLEVEL%
