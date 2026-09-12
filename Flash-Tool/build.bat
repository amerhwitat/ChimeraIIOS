@echo off
setlocal
set CONFIG=%~1
if "%CONFIG%"=="" set CONFIG=Release
cd /d "%~dp0"
where cmake >nul 2>nul || (echo [FLASH][DEPENDENCY] CMake missing & exit /b 2)
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
if errorlevel 1 exit /b %errorlevel%
cmake --build build --config %CONFIG% --parallel
if errorlevel 1 exit /b %errorlevel%
echo [FLASH][DONE] Build complete: build\%CONFIG%\chimera_flash_tool.exe
