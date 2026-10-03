[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$VmxPath,
    [switch]$FixPageFile,
    [switch]$FixNamedMemoryFile,
    [switch]$OpenMemorySettings
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
$pagePeakGB = [math]::Round((($pageFiles | Measure-Object -Property CurrentUsage -Sum).Sum) / 1024, 2)

Write-Host "`nCHIMERA II OS / VMWARE WORKSTATION PREFLIGHT" -ForegroundColor White
Write-Host "VMX: $VmxPath"
Write-Host "VM memory: $mem MB"
Write-Host "VM drive: $vmDrive"
Write-Host "Free VM drive space: $freeGB GB"
Write-Host "Host physical RAM: $([math]::Round($cs.TotalPhysicalMemory/1GB,2)) GB"
Write-Host "Host currently free RAM: $ramFreeGB GB"
Write-Host "Current Windows pagefile allocation: $pageAllocatedGB GB"
Write-Host "Current pagefile usage: $pagePeakGB GB"

$neededDiskGB = [math]::Round(($mem * 1MB) / 1GB, 2)
if ($disk.FreeSpace -lt ($mem * 1MB)) {
    Fail "VMware needs at least the VM memory amount of free space on the filesystem containing the VMX. Free $freeGB GB < required $neededDiskGB GB."
} else { Ok "VM directory filesystem has enough free space for the configured VM memory." }

if ($ramFreeGB * 1024 -lt $mem) {
    Warn "Current free physical RAM is below the VM allocation. Close applications/other VMs or reduce VM memory before starting it."
} else { Ok "Current free physical RAM is at least the configured VM memory." }

if ($pageAllocatedGB * 1024 -lt $mem) {
    Warn "Current Windows pagefile allocation is below the VM memory request. This matches the attached 'paging file is too small' failure pattern."
} else { Ok "Current pagefile allocation is at least the configured VM memory." }

if ($vmx -match '(?m)^mainmem\.useNamedFile\s*=\s*"([^"]+)"') {
    Info "mainmem.useNamedFile = $($Matches[1])"
} else {
    Info "mainmem.useNamedFile is not explicitly configured."
}

if ($FixNamedMemoryFile) {
    Copy-Item -LiteralPath $VmxPath -Destination "$VmxPath.chimera-backup" -Force
    $new = if ($vmx -match '(?m)^mainmem\.useNamedFile\s*=') {
        [regex]::Replace($vmx,'(?m)^mainmem\.useNamedFile\s*=\s*"[^"]+"','mainmem.useNamedFile = "TRUE"')
    } else {
        $vmx.TrimEnd() + "`r`nmainmem.useNamedFile = \"TRUE\"`r`n"
    }
    Set-Content -LiteralPath $VmxPath -Value $new -Encoding ASCII
    Ok "Set mainmem.useNamedFile=TRUE; backup saved as $VmxPath.chimera-backup"
}

if ($FixPageFile) {
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "-FixPageFile requires an elevated PowerShell window (Run as Administrator)."
    }
    Set-CimInstance -Query "SELECT * FROM Win32_ComputerSystem" -Property @{AutomaticManagedPagefile=$true} | Out-Null
    Ok "Enabled Windows System Managed Pagefile. Reboot Windows before retrying VMware."
}

if ($OpenMemorySettings) {
    Start-Process 'SystemPropertiesAdvanced.exe'
    Info "Opened Windows Advanced System Properties. Use Performance > Settings > Advanced > Virtual memory."
}

Write-Host "`nRecommended recovery sequence:" -ForegroundColor White
Write-Host "1. Power off/suspend other VMs and close memory-heavy applications."
Write-Host "2. Ensure the VM filesystem has free space >= $neededDiskGB GB."
Write-Host "3. Ensure Windows has a sufficiently large/system-managed pagefile."
Write-Host "4. Reboot Windows after changing pagefile settings."
Write-Host "5. Start VMware Workstation and retry the Chimera VM."
Write-Host "6. If the error persists, try -FixNamedMemoryFile and retry."
