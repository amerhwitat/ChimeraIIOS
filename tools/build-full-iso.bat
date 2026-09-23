@echo off
setlocal
cd /d "%~dp0.."
where wsl >nul 2>&1 || (echo WSL is required.& exit /b 2)
wsl bash ./tools/build-chimera-iso.sh
if errorlevel 1 exit /b %errorlevel%
echo Chimera II full ISO build completed.
