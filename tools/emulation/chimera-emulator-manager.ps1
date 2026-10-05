param(
  [string]$CatalogRoot = (Join-Path (Resolve-Path "$PSScriptRoot\..\..").Path "emulation\catalog"),
  [string]$System,
  [switch]$List
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$known = Get-Content (Join-Path $CatalogRoot "known-emulators.json") -Raw | ConvertFrom-Json
if ($List) {
  $known.emulators.psobject.Properties | ForEach-Object {
    "{0}: {1}" -f $_.Name, ($_.Value -join ", ")
  }
  exit 0
}
if (-not $System) { throw "Specify -System or use -List." }
$known.emulators.psobject.Properties | Where-Object { $_.Value -contains $System } | ForEach-Object {
  $_.Name
}
