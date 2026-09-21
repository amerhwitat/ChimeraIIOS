
# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Write-Host "Chimera II Windows integration: $Root"
$AppCtl = Join-Path $Root 'appcenter/cli/chimera-appctl.py'
if (Get-Command python.exe -ErrorAction SilentlyContinue) {
  & python.exe $AppCtl list
} elseif (Get-Command py.exe -ErrorAction SilentlyContinue) {
  & py.exe $AppCtl list
} else {
  throw 'Python 3 is required for the application catalog build step.'
}
