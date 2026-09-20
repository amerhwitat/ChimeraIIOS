# =============================================================================
# CHIMERA II OS - FIX LINE ENDINGS (PowerShell Wrapper)
# =============================================================================
# Fixes CRLF/LF line ending issues in Docker images
#
# Issue: /usr/bin/env: 'bash\r': No such file or directory
# Solution: Convert CRLF to LF, rebuild images, push to Docker Hub
#
# Usage: .\fix-line-endings-wsl2.ps1
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
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║     CHIMERA II OS - FIX LINE ENDINGS & SHEBANGS                ║" -ForegroundColor Magenta
    Write-Host "║                                                                ║" -ForegroundColor Magenta
    Write-Host "║  Fixing: /usr/bin/env: 'bash\r': No such file or directory   ║" -ForegroundColor Magenta
    Write-Host "║  Rebuilding and pushing corrected Docker images               ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Test-Prerequisites {
    Write-Status "Checking prerequisites..." "Header"
    
    # Check WSL2
    try {
        $wslVersion = wsl --version
        Write-Status "WSL2: OK" "Success"
    }
    catch {
        Write-Status "WSL2 not found" "Error"
        exit 1
    }
    
    # Check Docker
    try {
        $docker = wsl docker --version 2>$null
        Write-Status "Docker: $docker" "Success"
    }
    catch {
        Write-Status "Docker not available" "Error"
        exit 1
    }
    
    # Check Git
    try {
        $git = wsl git --version 2>$null
        Write-Status "Git: OK" "Success"
    }
    catch {
        Write-Status "Git not found" "Error"
        exit 1
    }
    
    Write-Host ""
}

function Show-Info {
    Write-Host "Fix Configuration:" -ForegroundColor Cyan
    Write-Host "  GitHub User: $GitHubUser" -ForegroundColor Gray
    Write-Host "  Docker Hub User: $DockerUser" -ForegroundColor Gray
    Write-Host "  Repositories: 13" -ForegroundColor Gray
    Write-Host "  Images to fix: 39" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "What will be fixed:" -ForegroundColor Cyan
    Write-Host "  ✓ CRLF to LF line endings" -ForegroundColor Yellow
    Write-Host "  ✓ Shebang lines (#!/bin/bash)" -ForegroundColor Yellow
    Write-Host "  ✓ Entrypoint scripts" -ForegroundColor Yellow
    Write-Host "  ✓ Dockerfiles" -ForegroundColor Yellow
    Write-Host "  ✓ All shell scripts" -ForegroundColor Yellow
    Write-Host "  ✓ Rebuild Docker images" -ForegroundColor Yellow
    Write-Host "  ✓ Push to Docker Hub" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Timeline:" -ForegroundColor Cyan
    Write-Host "  Fix files: 5-10 min" -ForegroundColor Gray
    Write-Host "  Rebuild images: 30-60 min" -ForegroundColor Gray
    Write-Host "  Push to Docker Hub: 20-40 min" -ForegroundColor Gray
    Write-Host "  Total: 1-2 hours" -ForegroundColor Gray
    Write-Host ""
}

function Start-Fix {
    Write-Status "Starting line ending fix..." "Header"
    Write-Host ""
    
    $fixScript = "C:\tmp\ChimeraIIOS\fix-line-endings.sh"
    
    if (-not (Test-Path $fixScript)) {
        Write-Status "Fix script not found: $fixScript" "Error"
        exit 1
    }
    
    # Copy to WSL2
    Write-Status "Copying fix script to WSL2..." "Info"
    wsl bash -c "cp /mnt/c/tmp/ChimeraIIOS/fix-line-endings.sh ~/"
    
    # Run the fix
    Write-Status "Running fix script..." "Header"
    Write-Host ""
    
    wsl bash -c "bash ~/fix-line-endings.sh '$GitHubUser' '$DockerUser'"
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Status "Line ending fix completed!" "Success"
        Show-Results
    }
    else {
        Write-Host ""
        Write-Status "Fix completed with warnings (exit code: $exitCode)" "Warning"
    }
}

function Show-Results {
    Write-Host ""
    Write-Status "════════════════════════════════════════════════════════════" "Success"
    Write-Status "FIX COMPLETED - IMAGES REBUILT & PUSHED" "Success"
    Write-Status "════════════════════════════════════════════════════════════" "Success"
    Write-Host ""
    
    Write-Host "✓ Issue Fixed:" -ForegroundColor Green
    Write-Host "  /usr/bin/env: 'bash\r': No such file or directory" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "✓ What was corrected:" -ForegroundColor Green
    Write-Host "  • CRLF to LF line endings" -ForegroundColor Gray
    Write-Host "  • Shebang lines in all scripts" -ForegroundColor Gray
    Write-Host "  • Entrypoint scripts" -ForegroundColor Gray
    Write-Host "  • All Dockerfiles" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "✓ Images available on Docker Hub:" -ForegroundColor Green
    Write-Host "  https://hub.docker.com/u/$DockerUser" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "✓ Pull corrected images:" -ForegroundColor Green
    Write-Host "  docker pull $DockerUser/chimeraiios:latest" -ForegroundColor Gray
    Write-Host "  docker pull $DockerUser/nlp:v1.0.0-fixed" -ForegroundColor Gray
    Write-Host "  docker pull $DockerUser/bizx:stable" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "✓ Test the fix:" -ForegroundColor Green
    Write-Host "  docker run -it $DockerUser/chimeraiios:latest bash" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "✓ Deploy corrected images:" -ForegroundColor Green
    Write-Host "  docker-compose -f docker-compose-full.yml pull" -ForegroundColor Gray
    Write-Host "  docker-compose -f docker-compose-full.yml up -d" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "📋 View fix report:" -ForegroundColor Cyan
    $reportPath = "\\wsl$\Ubuntu\home\$env:USERNAME\docker-fix-chimera\LINE_ENDING_FIX_REPORT.txt"
    Write-Host "  $reportPath" -ForegroundColor Gray
    Write-Host ""
}

# Main
Show-Banner
Test-Prerequisites
Show-Info

$continue = Read-Host "Continue with line ending fix? (yes/no)"
if ($continue -ne "yes") {
    Write-Status "Fix cancelled" "Info"
    exit 0
}

Write-Host ""
Start-Fix
