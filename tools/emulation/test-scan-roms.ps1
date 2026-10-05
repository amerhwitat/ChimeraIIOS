param(
  [string]$Root = "C:\tmp\ChimeraIIOS\ROMs"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "scan-roms.ps1"
if (-not (Test-Path $script)) { throw "Scanner missing: $script" }
if (-not (Test-Path $Root -PathType Container)) {
  Write-Warning "ROM root unavailable in this environment: $Root"
  exit 0
}
& $script -Root $Root
$catalog = Join-Path (Resolve-Path "$PSScriptRoot\..\..").Path "emulation\catalog"
foreach ($name in @("roms.local.json","emulators.local.json","bios.local.json","compatibility.local.json")) {
  $path = Join-Path $catalog $name
  if (-not (Test-Path $path)) { throw "Missing generated catalog: $path" }
  Get-Content $path -Raw | ConvertFrom-Json | Out-Null
  Write-Host "[PASS] $name"
}
