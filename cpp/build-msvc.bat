@echo off
setlocal EnableExtensions EnableDelayedExpansion
set CONFIG=%~1
if "%CONFIG%"=="" set CONFIG=Release
set ARCH=%~2
if "%ARCH%"=="" set ARCH=x64
set ROOT=%~dp0..
cd /d "%ROOT%"
echo [CHIMERA][MSVC] Configuration=%CONFIG% Platform=%ARCH%
where cmake >nul 2>nul && echo [CHIMERA][DEPENDENCY] CMake=OK || echo [CHIMERA][DEPENDENCY] CMake=NOT FOUND
where msbuild >nul 2>nul && echo [CHIMERA][DEPENDENCY] MSBuild=OK || echo [CHIMERA][DEPENDENCY] MSBuild=NOT FOUND
if exist "%ROOT%cpp\ChimeraIIOS.sln" (
  echo [CHIMERA][COMPILE][LINK] Building Visual Studio solution...
  msbuild "%ROOT%cpp\ChimeraIIOS.sln" /m /p:Configuration=%CONFIG% /p:Platform=%ARCH%
  if errorlevel 1 exit /b %errorlevel%
)
echo [CHIMERA][CMAKE] Configuring canonical build...
cmake -S "%ROOT%" -B "%ROOT%build\msvc" -G "Visual Studio 17 2022" -A %ARCH%
if errorlevel 1 exit /b %errorlevel%
echo [CHIMERA][CMAKE][BUILD] Building all targets...
cmake --build "%ROOT%build\msvc" --config %CONFIG% --parallel
if errorlevel 1 exit /b %errorlevel%
echo [CHIMERA][DONE] MSVC build completed.
