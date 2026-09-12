@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-apple-portfolio.ps1"
exit /b %ERRORLEVEL%
