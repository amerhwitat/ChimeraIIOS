@echo off
setlocal
where python >nul 2>nul || (echo Python 3 is required.& exit /b 1)
python "%~dp0chimera_installer.py" --output "%~dp0..\chimera-install-plan.json" %*
if errorlevel 1 exit /b %errorlevel%
echo Chimera II OS installation plan generated.
