param([ValidateSet('Debug','Release')][string]$Configuration='Release',[ValidateSet('x64','Win32','ARM64')][string]$Architecture='x64')
$ErrorActionPreference='Stop'
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
function Step($Name,$Action){ Write-Host "[CHIMERA][$Name]" -ForegroundColor Cyan; & $Action; if($LASTEXITCODE -ne 0){ throw "Stage failed: $Name ($LASTEXITCODE)" } }
Write-Host "[CHIMERA][DEPENDENCY] Checking MSBuild/CMake..."
Get-Command cmake -ErrorAction SilentlyContinue | Out-Null
Get-Command msbuild -ErrorAction SilentlyContinue | Out-Null
if(Get-Command msbuild -ErrorAction SilentlyContinue){ Step 'COMPILE-LINK' { msbuild "$Root\cpp\ChimeraIIOS.sln" /m /p:Configuration=$Configuration /p:Platform=$Architecture } }
Step 'CONFIGURE' { cmake -S $Root -B "$Root\build\msvc" -G 'Visual Studio 17 2022' -A $Architecture }
Step 'BUILD' { cmake --build "$Root\build\msvc" --config $Configuration --parallel }
Write-Host "[CHIMERA][DONE] MSVC build completed." -ForegroundColor Green
