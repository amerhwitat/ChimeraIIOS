@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"
if "%~1"=="" (%PY% "%ROOT%\tools\build\orchestrator.py" all) else (%PY% "%ROOT%\tools\build\orchestrator.py" %*)
exit /b %ERRORLEVEL%
