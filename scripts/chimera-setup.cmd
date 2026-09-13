@echo off
setlocal
set "ROOT=%~dp0.."
where python >nul 2>nul
if errorlevel 1 (set "PY=py -3") else (set "PY=python")
%PY% "%ROOT%\tools\build\orchestrator.py" all %*
if errorlevel 1 exit /b %ERRORLEVEL%
%PY% "%ROOT%\tools\build\orchestrator.py" install %*
exit /b %ERRORLEVEL%
