@echo off
setlocal
set ROOT=%~dp0..\..
set BUILD=%ROOT%\build\toolchains
if not exist "%BUILD%" mkdir "%BUILD%"
where cmake >nul 2>nul || (echo cmake is required & exit /b 1)
cmake -S "%ROOT%" -B "%BUILD%" -DCMAKE_BUILD_TYPE=Release
if errorlevel 1 exit /b 1
cmake --build "%BUILD%" --config Release --parallel
if errorlevel 1 exit /b 1
echo Toolchain host build complete.
echo Install language/compiler packages according to toolchains\tool_registry.json.
