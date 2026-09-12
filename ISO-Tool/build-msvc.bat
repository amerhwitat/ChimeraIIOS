@echo off
setlocal
set CONFIG=%~1
if "%CONFIG%"=="" set CONFIG=Release
cd /d "%~dp0"
if not exist "vcpp\ISO-Tool-UnifiedGui.sln" (echo [ISO][ERROR] Visual Studio solution missing&exit /b 2)
where msbuild >nul 2>nul || (echo [ISO][ERROR] MSBuild not found. Run from VS Developer Command Prompt.&exit /b 2)
echo [ISO][COMPILE][LINK] %CONFIG% x64
msbuild "vcpp\ISO-Tool-UnifiedGui.sln" /m /p:Configuration=%CONFIG% /p:Platform=x64
exit /b %errorlevel%
