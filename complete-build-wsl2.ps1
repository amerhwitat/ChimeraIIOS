# =============================================================================
# CHIMERA II OS - COMPLETE BUILD SYSTEM (PowerShell Wrapper)
# =============================================================================
# Automates building all GitHub repositories, Docker images, and bootable ISO
#
# Usage: .\complete-build-wsl2.ps1
# =============================================================================

param(
    [string]$GitHubUser = "amerhwitat",
    [string]$DockerUser = "amerhwitat"
)

$ProgressPreference = 'Continue'

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $colors = @{
        "Info"    = "Cyan"
        "Success" = "Green"
        "Error"   = "Red"
        "Warning" = "Yellow"
        "Header"  = "Magenta"
    }
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -ForegroundColor Gray -NoNewline
    Write-Host $Message -ForegroundColor $colors[$Type]
}

function Show-Banner {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║      CHIMERA II OS - COMPLETE BUILD SYSTEM                    ║" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "║  Building all GitHub repos + Docker images + ISO             ║" -ForegroundColor Cyan
    Write-Host "║  created by Amer Abdullah Suleiman Hwitat - عامر الحويطات  ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Prerequisites {
    Write-Status "Checking prerequisites..." "Header"
    
    # Check WSL2
    try {
        $wslVersion = wsl --version
        Write-Status "WSL2: $wslVersion" "Success"
    }
    catch {
        Write-Status "WSL2 not found. Install with: wsl --install" "Error"
        exit 1
    }
    
    # Check Docker
    $docker = wsl docker --version 2>$null
    if ($docker) {
        Write-Status "Docker: $docker" "Success"
    }
    else {
        Write-Status "Docker not available in WSL2" "Error"
        exit 1
    }
    
    # Check disk space
    $diskSpace = wsl bash -c "df -h / | tail -1 | awk '{print \$4}'" 2>$null
    Write-Status "Disk space available: $diskSpace" "Info"
    
    # Check Git
    $git = wsl git --version 2>$null
    if ($git) {
        Write-Status "Git: $git" "Success"
    }
}

function Start-Build {
    Write-Status "Starting complete build system..." "Header"
    Write-Host ""
    
    $buildScript = "C:\tmp\ChimeraIIOS\complete-build-system.sh"
    
    if (-not (Test-Path $buildScript)) {
        Write-Status "Build script not found: $buildScript" "Error"
        exit 1
    }
    
    Write-Status "Build script: $buildScript" "Info"
    Write-Host ""
    
    # Show what will be built
    Write-Host "Will build:" -ForegroundColor Cyan
    Write-Host "  • 13 GitHub repositories" -ForegroundColor Yellow
    Write-Host "  • Spitfire bootloader" -ForegroundColor Yellow
    Write-Host "  • Aurora desktop environment" -ForegroundColor Yellow
    Write-Host "  • 13+ Docker images" -ForegroundColor Yellow
    Write-Host "  • Complete bootable ISO" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Estimated time: 2-4 hours" -ForegroundColor Yellow
    Write-Host "Requires: 50GB+ disk space" -ForegroundColor Yellow
    Write-Host ""
    
    $continue = Read-Host "Continue? (yes/no)"
    if ($continue -ne "yes") {
        Write-Status "Build cancelled" "Info"
        exit 0
    }
    
    Write-Host ""
    Write-Status "Running build script..." "Header"
    Write-Host ""
    
    # Copy script to WSL2 and run
    wsl bash -c "bash /mnt/c/tmp/ChimeraIIOS/complete-build-system.sh $GitHubUser $DockerUser"
    
    $exitCode = $LASTEXITCODE
    
    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Status "Build completed successfully!" "Success"
        Show-Results
    }
    else {
        Write-Status "Build failed with exit code: $exitCode" "Error"
        exit 1
    }
}

function Show-Results {
    Write-Host ""
    Write-Status "════════════════════════════════════════════════════════════" "Success"
    Write-Status "BUILD COMPLETE - ALL ARTIFACTS READY" "Success"
    Write-Status "════════════════════════════════════════════════════════════" "Success"
    Write-Host ""
    
    Write-Host "📁 Output Files:" -ForegroundColor Cyan
    Write-Host "  • ISO: ~/chimera-build-complete/iso-output/" -ForegroundColor Gray
    Write-Host "  • Docker: ~/chimera-build-complete/docker-output/" -ForegroundColor Gray
    Write-Host "  • Report: ~/chimera-build-complete/BUILD_COMPLETE_REPORT.txt" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "🐳 Docker Hub Images:" -ForegroundColor Cyan
    Write-Host "  • Registry: https://hub.docker.com/u/$DockerUser" -ForegroundColor Gray
    Write-Host "  • All repositories pushed with tags: latest, v1.0.0, stable" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "🔥 Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Burn ISO to USB using Rufus" -ForegroundColor Yellow
    Write-Host "  2. Boot from USB" -ForegroundColor Yellow
    Write-Host "  3. Deploy Docker images" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "📋 Download Files:" -ForegroundColor Cyan
    $wslPath = "\\wsl$\Ubuntu\home\$env:USERNAME\chimera-build-complete\iso-output\"
    Write-Host "  ISO files: $wslPath" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "Copy to Windows:" -ForegroundColor Cyan
    Write-Host 'Copy-Item "' "$wslPath" '*.iso" -Destination $env:USERPROFILE\Downloads\' -ForegroundColor Gray
    Write-Host ""
}

# Main
Show-Banner
Test-Prerequisites
Write-Host ""
Start-Build
