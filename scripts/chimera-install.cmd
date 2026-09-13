@echo off
setlocal
set "ROOT=%~dp0.."
where python >nul 2>nul
if not errorlevel 1 (python "%ROOT%\tools\build\orchestrator.py" install %*) else (py -3 "%ROOT%\tools\build\orchestrator.py" install %*)
exit /b %ERRORLEVEL%
