@echo off
setlocal
where python >nul 2>nul || (echo Python 3 required.& exit /b 1)
python "%~dp0build_all_editions.py" %*
exit /b %errorlevel%
