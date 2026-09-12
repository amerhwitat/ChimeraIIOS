@echo off
setlocal
set TARGET=%~1
if "%TARGET%"=="" set TARGET=ChimeraServer.cbp
set CONFIG=%~2
if "%CONFIG%"=="" set CONFIG=Release
where codeblocks >nul 2>nul
if errorlevel 1 echo [CHIMERA][DEPENDENCY] Code::Blocks CLI not found; use the workspace manually.
if exist "%~dp0%TARGET%" (
  echo [CHIMERA][CODEBLOCKS] Opening %TARGET% configuration %CONFIG%...
  codeblocks "%~dp0%TARGET%" --target="%CONFIG%" --build --no-batch-window
  exit /b %errorlevel%
)
echo Project not found: %TARGET%
exit /b 2
