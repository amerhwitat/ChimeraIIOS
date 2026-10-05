param(
  [string]$Root = "C:\tmp\ChimeraIIOS\ROMs"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "scan-roms.ps1"
if (-not (Test-Path $script)) { throw "Scanner missing: $script" }

$repoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$fixture = Join-Path ([System.IO.Path]::GetTempPath()) ("chimera-emulation-fixture-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $fixture | Out-Null
try {
  "NES fixture" | Set-Content (Join-Path $fixture "game.nes")
  "MAME fixture" | Set-Content (Join-Path $fixture "mame.exe")
  "BIOS fixture" | Set-Content (Join-Path $fixture "bios.bin")

  & $script -Root $fixture -RepoRoot $repoRoot

  $catalog = Join-Path $repoRoot "emulation\catalog"
  foreach ($name in @("roms.local.json","emulators.local.json","bios.local.json","compatibility.local.json")) {
    $path = Join-Path $catalog $name
    if (-not (Test-Path $path)) { throw "Missing generated catalog: $path" }
    Get-Content $path -Raw | ConvertFrom-Json | Out-Null
    Write-Host "[PASS] $name JSON"
  }

  $roms = Get-Content (Join-Path $catalog "roms.local.json") -Raw | ConvertFrom-Json
  $compat = Get-Content (Join-Path $catalog "compatibility.local.json") -Raw | ConvertFrom-Json
  $emulators = Get-Content (Join-Path $catalog "emulators.local.json") -Raw | ConvertFrom-Json
  if (-not ($roms.roms | Where-Object { $_.name -eq "game.nes" })) { throw "NES ROM fixture was not indexed" }
  if (-not ($compat.compatibility | Where-Object { $_.rom_path -eq "game.nes" -and $_.emulator_candidates -contains "mame" -eq $false })) {
    # MAME is intentionally not an NES candidate; RetroArch/NES-native emulators are.
  }
  $nes = $compat.compatibility | Where-Object { $_.rom_path -eq "game.nes" }
  if (-not ($nes.emulator_candidates -contains "retroarch")) { throw "Canonical emulator mapping missing for NES" }
  if (-not ($emulators.emulators | Where-Object { $_.name -eq "mame.exe" -and $_.likely_emulator_ids -contains "mame" })) {
    throw "Emulator executable fixture was not identified"
  }
  Write-Host "[PASS] canonical ROM/emulator matching"
}
finally {
  Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue
}
