@echo off
setlocal
set CONFIG=%~1
if "%CONFIG%"=="" set CONFIG=Release
set ROOT=%~dp0..
if exist "%ROOT%build\msvc\%CONFIG%\chimera_server.exe" (
  echo [CHIMERA][RUN] chimera_server
  "%ROOT%build\msvc\%CONFIG%\chimera_server.exe" %*
  exit /b %errorlevel%
)
if exist "%ROOT%build\gcc\chimera_server.exe" (
  echo [CHIMERA][RUN] chimera_server
  "%ROOT%build\gcc\chimera_server.exe" %*
  exit /b %errorlevel%
)
echo [CHIMERA][RUN] No Windows server executable found. Build first.
exit /b 2
