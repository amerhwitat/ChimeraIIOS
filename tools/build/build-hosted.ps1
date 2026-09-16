$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Build = Join-Path $Root 'build\hosted-windows'
cmake -S $Root -B $Build -DCMAKE_BUILD_TYPE=Release -DCHIMERA_EDITION=HOSTED
cmake --build $Build --config Release --parallel
ctest --test-dir $Build -C Release --output-on-failure
Write-Host "Hosted Windows build complete: $Build"
