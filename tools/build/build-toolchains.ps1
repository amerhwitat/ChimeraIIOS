$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Build = Join-Path $Root 'build/toolchains'
New-Item -ItemType Directory -Force $Build | Out-Null
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) { throw 'cmake is required' }
cmake -S $Root -B $Build -DCMAKE_BUILD_TYPE=Release
cmake --build $Build --config Release --parallel
Write-Host 'Toolchain host build complete.'
Write-Host 'Install language/compiler packages according to toolchains/tool_registry.json.'
