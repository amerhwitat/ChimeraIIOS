[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$VmxPath,
    [switch]$RemoveSuspendState,
    [switch]$SafeCpuConfig,
    [switch]$Disable3D,
    [switch]$UseBios
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $VmxPath -PathType Leaf)) { throw "VMX not found: $VmxPath" }
$VmxPath = (Resolve-Path -LiteralPath $VmxPath).Path
$dir = Split-Path -Parent $VmxPath
$vmx = Get-Content -LiteralPath $VmxPath -Raw
$backup = "$VmxPath.chimera-recovery-backup"
Copy-Item -LiteralPath $VmxPath -Destination $backup -Force

function Set-VmxValue([string]$key,[string]$value) {
    $pattern = '(?m)^' + [regex]::Escape($key) + '\s*=\s*"[^"]*"\s*$'
    $line = "$key = `"$value`""
    if ($script:vmx -match $pattern) { $script:vmx = [regex]::Replace($script:vmx,$pattern,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $line }) }
    else { $script:vmx = $script:vmx.TrimEnd() + "`r`n" + $line + "`r`n" }
}

if ($RemoveSuspendState) {
    Get-ChildItem -LiteralPath $dir -Filter '*.vmss' -Force -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem -LiteralPath $dir -Filter '*.lck' -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    Set-VmxValue 'checkpoint.vmState' ''
    Write-Host '[OK] Removed VMware suspend/lock state and cleared checkpoint.vmState.' -ForegroundColor Green
}

if ($SafeCpuConfig) {
    Set-VmxValue 'numvcpus' '1'
    Set-VmxValue 'cpuid.coresPerSocket' '1'
    Set-VmxValue 'vhv.enable' 'FALSE'
    Set-VmxValue 'monitor.suspend_on_triplefault' 'TRUE'
    Write-Host '[OK] Set conservative single-vCPU kernel-validation configuration.' -ForegroundColor Green
}

if ($Disable3D) {
    Set-VmxValue 'mks.enable3d' 'FALSE'
    Set-VmxValue 'svga.vramSize' '67108864'
    Write-Host '[OK] Disabled VMware accelerated 3D for troubleshooting.' -ForegroundColor Green
}

if ($UseBios) {
    Set-VmxValue 'firmware' 'bios'
    Set-VmxValue 'efi.secureBoot.enabled' 'FALSE'
    Write-Host '[OK] Switched VM firmware to legacy BIOS for Chimera boot-chain validation.' -ForegroundColor Green
}

Set-VmxValue 'mainmem.useNamedFile' 'TRUE'
[System.IO.File]::WriteAllText($VmxPath,$vmx,(New-Object System.Text.UTF8Encoding($false)))
Write-Host "[OK] Recovery VMX written: $VmxPath" -ForegroundColor Green
Write-Host "[INFO] Backup: $backup" -ForegroundColor Cyan
Write-Host '[INFO] Power the VM off completely before retrying. Do not resume an old suspended state.' -ForegroundColor Cyan
