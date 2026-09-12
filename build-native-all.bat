@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Release"

echo ============================================================
echo CHIMERA II OS NATIVE BUILD PIPELINE
echo ============================================================
call "%ROOT%cpp\build-msvc.bat" %CONFIG% x64
if errorlevel 1 exit /b %errorlevel%

echo [CHIMERA][NATIVE] Running compiled metadata validators...
if exist "%ROOT%build\%CONFIG%\chimera_native_tools.exe" "%ROOT%build\%CONFIG%\chimera_native_tools.exe" "%ROOT%"
if errorlevel 1 exit /b %errorlevel%

echo [CHIMERA][ISO] Building ISO-Tool...
call "%ROOT%ISO-Tool\build-msvc.bat" %CONFIG%
if errorlevel 1 exit /b %errorlevel%

echo [CHIMERA][FLASH] Building mobile Flash-Tool...
call "%ROOT%Flash-Tool\build.bat" %CONFIG%
if errorlevel 1 exit /b %errorlevel%

echo [CHIMERA][DONE] Native OS + ASM/C/C++ tools + ISO-Tool + Flash-Tool build sequence complete.
