
# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$arch = $env:PROCESSOR_ARCHITECTURE
[pscustomobject]@{
  Caption = $os.Caption
  Version = $os.Version
  Architecture = $arch
  Is64BitProcess = [Environment]::Is64BitProcess
  DotNetModernEligible = ($os.Version -ge [version]'10.0') -or ($os.Caption -match 'Windows 11') -or ($os.Caption -match 'Windows 10')
} | Format-List
