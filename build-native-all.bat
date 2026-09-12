@echo off
setlocal EnableExtensions
set ROOT=%~dp0
set CONFIG=%~1
if "%CONFIG%"=="" set CONFIG=Release

echo ============================================================
echo CHIMERA II OS NATIVE BUILD
 echo ============================================================
call "%ROOT%cpp\build-msvc.bat" %CONFIG% x64
if errorlevel 1 exit /b %errorlevel%

echo [CHIMERA][ISO] Building ISO-Tool...
call "%ROOT%ISO-Tool\build-msvc.bat" %CONFIG%
if errorlevel 1 exit /b %errorlevel%

echo [CHIMERA][FLASH] Building mobile Flash-Tool...
call "%ROOT%Flash-Tool\build.bat" %CONFIG%
if errorlevel 1 exit /b %errorlevel%

echo [CHIMERA][DONE] Native OS + ISO-Tool + Flash-Tool build sequence complete.
