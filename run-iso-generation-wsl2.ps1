# =============================================================================
# CHIMERA II OS - ISO GENERATION VIA WSL2
# =============================================================================
# This PowerShell script runs the ISO generation in WSL2 Ubuntu
# 
# Usage: .\run-iso-generation-wsl2.ps1
# =============================================================================

param(
    [string]$WSLDistro = "Ubuntu",
    [string]$DockerImage = "chimera2os:latest"
)


# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '.')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "CHIMERA II OS - ISO GENERATION (via WSL2)" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if WSL2 is available
Write-Host "[INFO] Checking WSL2 installation..." -ForegroundColor Blue
try {
    $wslVersion = wsl --version
    Write-Host "[OK] WSL2 found: $wslVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] WSL2 not found or not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install WSL2:"
    Write-Host "  wsl --install"
    exit 1
}

# Copy script to WSL2
Write-Host ""
Write-Host "[INFO] Copying ISO generation script to WSL2..." -ForegroundColor Blue
$windowsScriptPath = "C:\tmp\ChimeraIIOS\generate-iso-from-docker.sh"
$wslScriptPath = "/tmp/generate-iso-from-docker.sh"

# Convert Windows path to WSL2 path
$wslWindowsPath = wsl wslpath -a C:\tmp\ChimeraIIOS\generate-iso-from-docker.sh

Write-Host "[OK] Copying: $windowsScriptPath -> $wslScriptPath" -ForegroundColor Green

# Copy using WSL
Copy-Item $windowsScriptPath -Destination (wsl wslpath -u "C:\tmp\ChimeraIIOS\generate-iso-from-docker.sh") -Force

# Verify Docker image in WSL2
Write-Host ""
Write-Host "[INFO] Verifying Docker image in WSL2..." -ForegroundColor Blue
$imageCheck = wsl docker images --format "{{.Repository}}:{{.Tag}}" | Select-String "chimera2os"
if ($imageCheck) {
    Write-Host "[OK] Docker image found: $imageCheck" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Docker image not found in WSL2" -ForegroundColor Yellow
    Write-Host "[INFO] The image will be pulled automatically during build" -ForegroundColor Blue
}

# Display disk space in WSL2
Write-Host ""
Write-Host "[INFO] Checking disk space in WSL2..." -ForegroundColor Blue
$diskSpace = wsl df -h / | Select-Object -Last 1
Write-Host "$diskSpace" -ForegroundColor Cyan

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "STARTING ISO GENERATION IN WSL2" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏱️  Estimated time: 30-45 minutes" -ForegroundColor Yellow
Write-Host "📊 This process will:" -ForegroundColor Yellow
Write-Host "  • Export Docker image to rootfs (~2.5GB)" -ForegroundColor Yellow
Write-Host "  • Create bootloaders (BIOS + UEFI)" -ForegroundColor Yellow
Write-Host "  • Create squashfs filesystem (~10-20 min)" -ForegroundColor Yellow
Write-Host "  • Generate bootable ISO (~3GB)" -ForegroundColor Yellow
Write-Host "  • Generate checksums and report" -ForegroundColor Yellow
Write-Host ""

# Run ISO generation in WSL2
Write-Host "[INFO] Running: sudo bash $wslScriptPath" -ForegroundColor Blue
Write-Host ""

wsl sudo bash $wslScriptPath

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "ISO GENERATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    
    # Show output files
    Write-Host "[INFO] ISO files are located at:" -ForegroundColor Blue
    Write-Host "  WSL2: /home/\$USER/projects/ChimeraIIOS/build-iso/output/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Windows (WSL path mapping):" -ForegroundColor Cyan
    Write-Host "  \\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\" -ForegroundColor Cyan
    Write-Host ""
    
    # List output files
    Write-Host "[INFO] Contents:" -ForegroundColor Blue
    wsl ls -lh ~'/projects/ChimeraIIOS/build-iso/output/' 2>/dev/null
    
    Write-Host ""
    Write-Host "📋 Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Verify ISO:" -ForegroundColor Yellow
    Write-Host "     wsl sha256sum -c ~'/projects/ChimeraIIOS/build-iso/output/*.sha256'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Copy to Windows Downloads:" -ForegroundColor Yellow
    Write-Host "     Copy-Item 'WSL path' -Destination \$env:USERPROFILE\Downloads\" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. Burn to USB (Windows):" -ForegroundColor Yellow
    Write-Host "     - Download Rufus: https://rufus.ie/" -ForegroundColor Cyan
    Write-Host "     - Or balena Etcher: https://balena.io/etcher/" -ForegroundColor Cyan
    Write-Host "     - Select ISO and USB drive, click Write" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  4. Boot from USB:" -ForegroundColor Yellow
    Write-Host "     - Insert USB drive" -ForegroundColor Cyan
    Write-Host "     - Restart computer" -ForegroundColor Cyan
    Write-Host "     - Enter BIOS/Boot menu (usually F12 or DEL)" -ForegroundColor Cyan
    Write-Host "     - Select USB drive" -ForegroundColor Cyan
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host "ISO GENERATION FAILED" -ForegroundColor Red
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "[ERROR] Exit code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  • Check WSL2 disk space: wsl df -h /" -ForegroundColor Cyan
    Write-Host "  • Check Docker: wsl docker images" -ForegroundColor Cyan
    Write-Host "  • Run manually: wsl sudo bash /tmp/generate-iso-from-docker.sh" -ForegroundColor Cyan
    exit 1
}
