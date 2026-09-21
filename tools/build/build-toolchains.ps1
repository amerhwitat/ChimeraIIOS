
# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Build = Join-Path $Root 'build/toolchains'
New-Item -ItemType Directory -Force $Build | Out-Null
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) { throw 'cmake is required' }
cmake -S $Root -B $Build -DCMAKE_BUILD_TYPE=Release
cmake --build $Build --config Release --parallel
Write-Host 'Toolchain host build complete.'
Write-Host 'Install language/compiler packages according to toolchains/tool_registry.json.'
