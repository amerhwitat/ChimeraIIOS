[CmdletBinding()]
param(
  [ValidateSet('interactive','workstation','server','developer','minimal')]
  [string]$Profile = 'interactive',
  [switch]$Execute
)

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PlanArgs = @('--target','windows','--profile',$Profile)
if ($Execute) { $PlanArgs += '--execute' }

python (Join-Path $Root 'tools/installer/installer_plan.py') @PlanArgs

Write-Host ""
Write-Host "Windows adapter policy:"
Write-Host "  - Inventory Plug and Play devices and signed driver packages with pnputil."
Write-Host "  - Resolve candidates from Microsoft Update Catalog / WDK-compatible packages."
Write-Host "  - Prefer signed, hardware-compatible packages; never silently downgrade a driver."
Write-Host "  - Storage changes remain disabled until an explicit destructive confirmation."
Write-Host "  - Windows interoperability uses UEFI/GPT, SMB/SMB3, NTFS/ReFS/Storage Spaces adapters."
Write-Host ""
Write-Host "No driver or disk mutation is performed by this planning layer."
