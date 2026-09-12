@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-android-sdk.ps1"
if errorlevel 1 exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-portfolio-mobile.ps1"
exit /b %errorlevel%
