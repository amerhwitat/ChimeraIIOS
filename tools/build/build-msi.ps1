
# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
$ErrorActionPreference='Stop'
& "$PSScriptRoot\build-hosted.ps1"
wix build "$PSScriptRoot\..\..\packaging\windows\ChimeraIIOS.wxs" -o "$PSScriptRoot\..\..\dist\ChimeraIIOS-Hosted.msi"
Write-Host 'MSI created under dist/ChimeraIIOS-Hosted.msi'
