
# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
$ErrorActionPreference = 'Stop'
if ($IsMacOS) { & "$PSScriptRoot/build-apple-portfolio.sh"; exit $LASTEXITCODE }
Write-Host 'Apple IPA compilation requires a macOS/Xcode host.'
Write-Host 'This Windows script prepares the repository and can be used by a CI/remote macOS workflow.'
if ($env:APPLE_BUILD_HOST) { Write-Host "Configured Apple build host: $env:APPLE_BUILD_HOST" }
else { Write-Error 'Set APPLE_BUILD_HOST to a macOS build runner or run the Bash script on macOS.' }
