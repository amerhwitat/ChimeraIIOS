$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if (Get-Command wsl -ErrorAction SilentlyContinue) {
  & wsl bash ./tools/build-full-iso.sh
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else { throw 'WSL is required to compile the bare-metal toolchain and build the ISO.' }
Write-Host 'Chimera II full ISO build completed.'
