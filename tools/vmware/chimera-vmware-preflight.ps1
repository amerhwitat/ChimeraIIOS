[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$VmxPath,
    [switch]$FixPageFile,
    [switch]$FixNamedMemoryFile,
    [switch]$OpenMemorySettings,
    [switch]$SafeCpuConfig,
    [switch]$Disable3D,
    [switch]$UseBios,
    [switch]$RemoveSuspendState
)

$ErrorActionPreference = 'Stop'
function Fail($m) { Write-Host "[ERROR] $m" -ForegroundColor Red }
function Info($m) { Write-Host "[INFO]  $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function Ok($m) { Write-Host "[OK]    $m" -ForegroundColor Green }

if (-not (Test-Path -LiteralPath $VmxPath -PathType Leaf)) { throw "VMX not found: $VmxPath" }
$VmxPath = (Resolve-Path -LiteralPath $VmxPath).Path
$vmDir = Split-Path -Parent $VmxPath
$vmDrive = (Split-Path -Qualifier $VmxPath)
$vmx = Get-Content -LiteralPath $VmxPath -Raw

$mem = 0
if ($vmx -match '(?m)^memsize\s*=\s*"(\d+)"') { $mem = [int64]$Matches[1] }
if ($mem -le 0) { throw "Could not determine memsize from VMX." }

$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$vmDrive'"
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$pageFiles = @(Get-CimInstance Win32_PageFileUsage -ErrorAction SilentlyContinue)
$freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
$ramFreeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
$pageAllocatedGB = [math]::Round((($pageFiles | Measure-Object -Property AllocatedBaseSize -Sum).Sum) / 1024, 2)

Write-Host "`nCHIMERA II OS / VMWARE WORKSTATION PREFLIGHT" -ForegroundColor White
Write-Host "VMX: $VmxPath"
Write-Host "VM memory: $mem MB"
Write-Host "VM drive: $vmDrive"
Write-Host "Free VM drive space: $freeGB GB"
Write-Host "Host physical RAM: $([math]::Round($cs.TotalPhysicalMemory/1GB,2)) GB"
Write-Host "Host currently free RAM: $ramFreeGB GB"
Write-Host "Current Windows pagefile allocation: $pageAllocatedGB GB"

foreach ($key in 'firmware','numvcpus','mainmem.useNamedFile','monitor.suspend_on_triplefault','mks.enable3d','vhv.enable') {
    if ($vmx -match "(?m)^$([regex]::Escape($key))\s*=\s*\"([^\"]+)\"") { Info "$key = $($Matches[1])" }
}

if (Test-Path -LiteralPath (Join-Path $vmDir '*.vmss')) { Warn 'A VMware suspend state exists. A stale/corrupt VMSS can cause 0xc0000005 when resuming.' }
if (Get-ChildItem -LiteralPath $vmDir -Filter '*.lck' -Force -ErrorAction SilentlyContinue) { Warn 'VMware lock files exist. Ensure Workstation is closed before removing stale locks.' }

$neededDiskGB = [math]::Round(($mem * 1MB) / 1GB, 2)
if ($disk.FreeSpace -lt ($mem * 1MB)) { Fail "VMware needs at least the VM memory amount of free space on the filesystem containing the VMX. Free $freeGB GB < required $neededDiskGB GB." } else { Ok 'VM filesystem has enough free space for configured VM memory.' }
if ($ramFreeGB * 1024 -lt $mem) { Warn 'Current free physical RAM is below VM allocation.' } else { Ok 'Current free physical RAM is at least VM allocation.' }
if ($pageAllocatedGB * 1024 -lt $mem) { Warn 'Windows pagefile allocation is below VM memory request.' } else { Ok 'Windows pagefile allocation is at least VM memory request.' }

function Set-VmxValue([string]$key,[string]$value) {
    $pattern = '(?m)^' + [regex]::Escape($key) + '\s*=\s*"[^"]*"\s*$'
    $line = "$key = `"$value`""
    if ($script:vmx -match $pattern) { $script:vmx = [regex]::Replace($script:vmx,$pattern,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $line }) }
    else { $script:vmx = $script:vmx.TrimEnd() + "`r`n" + $line + "`r`n" }
}

$changed = $false
if ($FixNamedMemoryFile) { Set-VmxValue 'mainmem.useNamedFile' 'TRUE'; $changed=$true }
if ($SafeCpuConfig) { Set-VmxValue 'numvcpus' '1'; Set-VmxValue 'cpuid.coresPerSocket' '1'; Set-VmxValue 'vhv.enable' 'FALSE'; Set-VmxValue 'monitor.suspend_on_triplefault' 'TRUE'; $changed=$true }
if ($Disable3D) { Set-VmxValue 'mks.enable3d' 'FALSE'; Set-VmxValue 'svga.vramSize' '67108864'; $changed=$true }
if ($UseBios) { Set-VmxValue 'firmware' 'bios'; Set-VmxValue 'efi.secureBoot.enabled' 'FALSE'; $changed=$true }
if ($RemoveSuspendState) {
    Get-ChildItem -LiteralPath $vmDir -Filter '*.vmss' -Force -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem -LiteralPath $vmDir -Filter '*.lck' -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    Set-VmxValue 'checkpoint.vmState' ''
    $changed=$true
    Ok 'Removed suspend/lock state and cleared checkpoint.vmState.'
}
if ($changed) {
    Copy-Item -LiteralPath $VmxPath -Destination "$VmxPath.chimera-preflight-backup" -Force
    [System.IO.File]::WriteAllText($VmxPath,$vmx,(New-Object System.Text.UTF8Encoding($false)))
    Ok "Updated VMX; backup: $VmxPath.chimera-preflight-backup"
}

if ($FixPageFile) {
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '-FixPageFile requires an elevated PowerShell window.' }
    Set-CimInstance -Query 'SELECT * FROM Win32_ComputerSystem' -Property @{AutomaticManagedPagefile=$true} | Out-Null
    Ok 'Enabled Windows System Managed Pagefile. Reboot Windows before retrying VMware.'
}
if ($OpenMemorySettings) { Start-Process 'SystemPropertiesAdvanced.exe'; Info 'Opened Windows Advanced System Properties.' }

Write-Host "`nRecommended recovery:" -ForegroundColor White
Write-Host '1. Power off the VM completely; do not resume the old state.'
Write-Host '2. For the attached vCPU/triple-fault error, start with one vCPU, BIOS, 3D disabled and nested virtualization disabled.'
Write-Host '3. If 0xc0000005 followed a suspend/resume, remove VMSS/LCK state and clear checkpoint.vmState.'
Write-Host '4. Verify host RAM/pagefile/disk space before starting Workstation.'
Write-Host '5. Once BIOS boot succeeds, test UEFI separately with CHIMERA_VM_FIRMWARE=efi.'
