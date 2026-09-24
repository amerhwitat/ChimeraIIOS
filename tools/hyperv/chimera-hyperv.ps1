[CmdletBinding()]
param(
  [string]$Name="Chimera-II-OS",
  [string]$IsoPath="$PSScriptRoot\\..\\..\\build\\iso\\chimera-ii-os.iso",
  [string]$VhdxPath="$env:USERPROFILE\\ChimeraIIOS\\$Name.vhdx",
  [int]$MemoryGB=4,
  [int]$CPUs=2,
  [string]$SwitchName="",
  [switch]$Start,
  [switch]$DisableSecureBoot
)
$ErrorActionPreference="Stop"
Import-Module Hyper-V -ErrorAction Stop
if(-not (Test-Path $IsoPath)){ throw "ISO not found: $IsoPath" }
if(Get-VM -Name $Name -ErrorAction SilentlyContinue){ throw "VM already exists: $Name" }
New-Item -ItemType Directory -Force -Path (Split-Path $VhdxPath)|Out-Null
New-VHD -Path $VhdxPath -SizeBytes 32GB -Dynamic|Out-Null
$params=@{Name=$Name;MemoryStartupBytes=($MemoryGB*1GB);Generation=2;NewVHDPath=$VhdxPath;NewVHDSizeBytes=32GB}
if($SwitchName){$params.Switch=$SwitchName}
New-VM @params|Out-Null
Set-VMProcessor -VMName $Name -Count $CPUs
Add-VMDvdDrive -VMName $Name -Path $IsoPath|Out-Null
Set-VMFirmware -VMName $Name -FirstBootDevice (Get-VMDvdDrive -VMName $Name)
if($DisableSecureBoot){Set-VMFirmware -VMName $Name -EnableSecureBoot Off}else{Set-VMFirmware -VMName $Name -EnableSecureBoot On -SecureBootTemplate MicrosoftUEFICertificateAuthority}
Set-VM -Name $Name -AutomaticStopAction ShutDown|Out-Null
Write-Host "Created Hyper-V Generation 2 VM: $Name"
Write-Host "UEFI + virtual SCSI storage + ISO boot configured."
if($Start){Start-VM -Name $Name|Out-Null;Write-Host "VM started."}
