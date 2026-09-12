@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-apple-toolchain.ps1"
exit /b %ERRORLEVEL%
