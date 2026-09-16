$ErrorActionPreference='Stop'
& "$PSScriptRoot\build-hosted.ps1"
wix build "$PSScriptRoot\..\..\packaging\windows\ChimeraIIOS.wxs" -o "$PSScriptRoot\..\..\dist\ChimeraIIOS-Hosted.msi"
Write-Host 'MSI created under dist/ChimeraIIOS-Hosted.msi'
