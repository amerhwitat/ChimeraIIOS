# =============================================================================
# CHIMERA II OS - DOCKER BUILD & PUSH (PowerShell Wrapper)
# =============================================================================
# Automates building and pushing all Docker images to Docker Hub
#
# Usage: .\docker-build-push-wsl2.ps1 -GitHubUser amerhwitat -DockerUser amerhwitat
# =============================================================================

param(
    [string]$GitHubUser = "amerhwitat",
    [string]$DockerUser = "amerhwitat",
    [string]$DockerHubToken = $null,
    [switch]$SkipPush = $false
)

$ProgressPreference = 'Continue'
$ErrorActionPreference = 'Continue'

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $colors = @{
        "Info"    = "Cyan"
        "Success" = "Green"
        "Error"   = "Red"
        "Warning" = "Yellow"
        "Header"  = "Magenta"
        "Push"    = "Blue"
    }
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -ForegroundColor Gray -NoNewline
    Write-Host $Message -ForegroundColor $colors[$Type]
}

function Show-Banner {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║     CHIMERA II OS - DOCKER BUILD & PUSH AUTOMATION             ║" -ForegroundColor Magenta
    Write-Host "║                                                                ║" -ForegroundColor Magenta
    Write-Host "║  Building 13 Docker images and pushing to Docker Hub          ║" -ForegroundColor Magenta
    Write-Host "║  created by Amer Abdullah Suleiman Hwitat - عامر الحويطات  ║" -ForegroundColor Magenta
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
        Write-Status "WSL2 not found. Install with: wsl --install" "Error"
        exit 1
    }
    
    # Check Docker
    try {
        $dockerVersion = wsl docker --version 2>$null
        if ($dockerVersion) {
            Write-Status "Docker: $dockerVersion" "Success"
        }
        else {
            throw "Docker not available"
        }
    }
    catch {
        Write-Status "Docker not available in WSL2" "Error"
        exit 1
    }
    
    # Check Git
    try {
        $gitVersion = wsl git --version 2>$null
        Write-Status "Git: OK" "Success"
    }
    catch {
        Write-Status "Git not found" "Error"
        exit 1
    }
    
    # Check disk space
    $diskSpace = wsl bash -c "df -h / | tail -1 | awk '{print \$4}'" 2>$null
    Write-Status "Disk space available: $diskSpace" "Info"
    
    Write-Host ""
}

function Show-Info {
    Write-Host "Build Configuration:" -ForegroundColor Cyan
    Write-Host "  GitHub User: $GitHubUser" -ForegroundColor Gray
    Write-Host "  Docker Hub User: $DockerUser" -ForegroundColor Gray
    Write-Host "  Repositories: 13" -ForegroundColor Gray
    Write-Host "  Docker Images: 39 (13 repos × 3 tags)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "Build Steps:" -ForegroundColor Cyan
    Write-Host "  1. Initialize build environment" -ForegroundColor Gray
    Write-Host "  2. Clone/update repositories" -ForegroundColor Gray
    Write-Host "  3. Build Docker images" -ForegroundColor Gray
    Write-Host "  4. Login to Docker Hub" -ForegroundColor Gray
    Write-Host "  5. Push images to Docker Hub" -ForegroundColor Gray
    Write-Host "  6. Verify pushed images" -ForegroundColor Gray
    Write-Host "  7. Generate report" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "Timeline:" -ForegroundColor Cyan
    Write-Host "  Clone repos: 5-10 min" -ForegroundColor Gray
    Write-Host "  Build images: 30-60 min" -ForegroundColor Gray
    Write-Host "  Push to Docker Hub: 20-40 min" -ForegroundColor Gray
    Write-Host "  Total: 1-2 hours" -ForegroundColor Gray
    Write-Host ""
}

function Start-Build {
    Write-Status "Starting Docker build and push..." "Header"
    Write-Host ""
    
    $buildScript = "C:\tmp\ChimeraIIOS\docker-build-push.sh"
    
    if (-not (Test-Path $buildScript)) {
        Write-Status "Build script not found: $buildScript" "Error"
        exit 1
    }
    
    # Copy script to WSL2
    Write-Status "Copying build script to WSL2..." "Info"
    wsl bash -c "cp /mnt/c/tmp/ChimeraIIOS/docker-build-push.sh ~/"
    
    # Prepare command
    $wslCommand = "bash ~/docker-build-push.sh '$GitHubUser' '$DockerUser'"
    
    Write-Status "Running build script..." "Header"
    Write-Host ""
    
    # Run the build
    wsl bash -c $wslCommand
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Status "Docker build and push completed!" "Success"
        Show-Results
    }
    else {
        Write-Host ""
        Write-Status "Build completed with exit code: $exitCode" "Warning"
    }
}

function Show-Results {
    Write-Host ""
    Write-Status "════════════════════════════════════════════════════════════" "Success"
    Write-Status "DOCKER BUILD & PUSH COMPLETE" "Success"
    Write-Status "════════════════════════════════════════════════════════════" "Success"
    Write-Host ""
    
    Write-Host "📦 Docker Hub:" -ForegroundColor Cyan
    Write-Host "  Registry: https://hub.docker.com/u/$DockerUser" -ForegroundColor Gray
    Write-Host "  Total Images: 39 (13 repos × 3 tags)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "🐳 Pull Examples:" -ForegroundColor Cyan
    Write-Host "  docker pull $DockerUser/chimeraiios:latest" -ForegroundColor Gray
    Write-Host "  docker pull $DockerUser/nlp:v1.0.0" -ForegroundColor Gray
    Write-Host "  docker pull $DockerUser/bizx:stable" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "📊 View Build Report:" -ForegroundColor Cyan
    $reportPath = "\\wsl$\Ubuntu\home\$env:USERNAME\docker-build-chimera\DOCKER_BUILD_REPORT.txt"
    Write-Host "  $reportPath" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Test pull: docker pull $DockerUser/chimeraiios:latest" -ForegroundColor Yellow
    Write-Host "  2. Run container: docker run -it $DockerUser/chimeraiios:latest bash" -ForegroundColor Yellow
    Write-Host "  3. Deploy with Docker Compose or Kubernetes" -ForegroundColor Yellow
    Write-Host "  4. Generate deployment manifests" -ForegroundColor Yellow
    Write-Host ""
}

# Main
Show-Banner
Test-Prerequisites
Show-Info

$continue = Read-Host "Continue with Docker build and push? (yes/no)"
if ($continue -ne "yes") {
    Write-Status "Build cancelled" "Info"
    exit 0
}

Write-Host ""
Start-Build
