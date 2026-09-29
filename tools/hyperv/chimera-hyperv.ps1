[CmdletBinding()]
param(
  [string]$Name="Chimera-II-OS",
  [string]$IsoPath="$PSScriptRoot\\..\\..\\build\\ChimeraIIOS-comprehensive-1.0.0-x86_64.iso",
  [string]$VhdxPath="$env:USERPROFILE\\ChimeraIIOS\\$Name.vhdx",
  [ValidateSet(1,2)][int]$Generation=2,
  [int]$MemoryGB=4,
  [int]$CPUs=2,
  [string]$SwitchName="",
  [switch]$Start,
  [switch]$EnableSecureBoot
)
$ErrorActionPreference="Stop"
Import-Module Hyper-V -ErrorAction Stop

if(-not (Test-Path -LiteralPath $IsoPath)){ throw "ISO not found: $IsoPath. Build it first with build-chimera-iso.sh." }
if(Get-VM -Name $Name -ErrorAction SilentlyContinue){ throw "VM already exists: $Name" }

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $VhdxPath) | Out-Null
New-VHD -Path $VhdxPath -SizeBytes 32GB -Dynamic | Out-Null

$params=@{
  Name=$Name
  MemoryStartupBytes=($MemoryGB*1GB)
  Generation=$Generation
  NewVHDPath=$VhdxPath
  NewVHDSizeBytes=32GB
}
if($SwitchName){ $params.Switch=$SwitchName }
New-VM @params | Out-Null
Set-VMProcessor -VMName $Name -Count $CPUs

$dvd = Add-VMDvdDrive -VMName $Name -Path $IsoPath

if($Generation -eq 2){
  Set-VMFirmware -VMName $Name -FirstBootDevice $dvd
  if($EnableSecureBoot){
    # Chimera's current BOOTX64.EFI is not Microsoft-signed. Keep Secure Boot
    # disabled by default so the research ISO boots without requiring a signed
    # shim. The Microsoft UEFI CA template is appropriate only after a signed
    # Chimera shim/bootloader is supplied.
    Set-VMFirmware -VMName $Name -EnableSecureBoot On -SecureBootTemplate MicrosoftUEFICertificateAuthority
    Write-Warning "Secure Boot was explicitly enabled. An unsigned Chimera BOOTX64.EFI may be rejected by Hyper-V." 
  } else {
    Set-VMFirmware -VMName $Name -EnableSecureBoot Off
  }
  Write-Host "Hyper-V Generation 2: UEFI DVD boot configured; Secure Boot=$([bool]$EnableSecureBoot)"
} else {
  Set-VMBios -VMName $Name -StartupOrder @("CD","IDE","LegacyNetworkAdapter","Floppy")
  Write-Host "Hyper-V Generation 1: legacy BIOS CD/DVD boot configured"
}

Set-VM -Name $Name -AutomaticStopAction ShutDown | Out-Null
Write-Host "Created Hyper-V VM: $Name"
Write-Host "ISO: $IsoPath"
Write-Host "Generation: $Generation"
Write-Host "Memory: ${MemoryGB}GB  CPUs: $CPUs"
if($Start){ Start-VM -Name $Name | Out-Null; Write-Host "VM started." }
