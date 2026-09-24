[CmdletBinding()]param([switch]$Apply,[string]$Esp="$env:SystemDrive\EFI")
$ErrorActionPreference="Stop"
Write-Host "Chimera II Windows dual-boot planner"
Get-Disk|Format-Table Number,FriendlyName,PartitionStyle,Size
Get-Partition|Format-Table DiskNumber,PartitionNumber,DriveLetter,Size,Type
if(-not$Apply){Write-Host "DRY RUN: no disk, partition, EFI, or BCD changes.";exit 0}
if(-not([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw "Run as Administrator."}
if(-not(Test-Path $Esp)){throw "EFI path not found: $Esp"}
if(-not $env:CHIMERA_INSTALL_ROOT){throw "Set CHIMERA_INSTALL_ROOT to the staged EFI payload."}
$dest=Join-Path $Esp "CHIMERA";New-Item -ItemType Directory -Force -Path $dest|Out-Null
Copy-Item "$env:CHIMERA_INSTALL_ROOT\*" $dest -Recurse -Force
Write-Host "Payload staged at $dest; Windows partitions and BCD were not modified."
