# =============================================================================
# DOCKER HUB PUSH SCRIPT (PowerShell) - CHIMERA II OS
# =============================================================================
# Pushes all Docker images to Docker Hub
# Usage: .\docker-hub-push.ps1
# =============================================================================

param(
    [string]$Username = "amerhwitat",
    [string]$Registry = "docker.io",
    [switch]$SkipLogin = $false
)


# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '.')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Print-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 66) -ForegroundColor Blue
    Write-Host $Title -ForegroundColor Blue
    Write-Host ("=" * 66) -ForegroundColor Blue
    Write-Host ""
}

# Main
Print-Header "DOCKER HUB PUSH - CHIMERA II OS"

# Check Docker
Write-Info "Checking Docker daemon..."
try {
    $dockerInfo = docker info 2>&1
    Write-Success "Docker daemon is running"
}
catch {
    Write-Error-Custom "Docker daemon is not running. Please start Docker."
    exit 1
}

# Check login
if (-not $SkipLogin) {
    Write-Info "Checking Docker Hub login..."
    $configFile = "$env:USERPROFILE\.docker\config.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Warning-Custom "Not logged in to Docker Hub"
        Write-Info "Please run: docker login -u $Username"
        exit 1
    }
    
    Write-Success "Docker Hub credentials found"
}

# List images
Write-Info "Listing Docker images..."
Write-Host ""
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}" | Where-Object { $_ -like "*chimera*" -or $_ -like "REPOSITORY*" }
Write-Host ""

# Images to push
$imagesToPush = @(
    @{ Source = "chimera2os:latest"; Target = "$Username/chimera2os"; Tag = "latest" },
    @{ Source = "chimera2os:latest"; Target = "$Username/chimera2os"; Tag = "v1.0.0" },
    @{ Source = "chimera2os:latest"; Target = "$Username/chimera2os"; Tag = "comprehensive" },
    @{ Source = "amerhwitat/chimeraiios:iso"; Target = "$Username/chimeraiios"; Tag = "iso" }
)

# Process images
$successCount = 0
$failureCount = 0

foreach ($image in $imagesToPush) {
    Write-Info "Processing: $($image.Source) → $($image.Target):$($image.Tag)"
    
    # Check if source image exists
    $exists = docker image inspect $($image.Source) 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning-Custom "Image not found: $($image.Source), skipping..."
        continue
    }
    
    # Tag image
    Write-Info "Tagging: $($image.Source) → $($image.Target):$($image.Tag)"
    docker tag $($image.Source) "$($image.Target):$($image.Tag)"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to tag image: $($image.Target):$($image.Tag)"
        $failureCount++
        continue
    }
    
    # Push image
    Write-Info "Pushing: $($image.Target):$($image.Tag)"
    docker push "$($image.Target):$($image.Tag)"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Successfully pushed: $($image.Target):$($image.Tag)"
        $successCount++
    }
    else {
        Write-Error-Custom "Failed to push: $($image.Target):$($image.Tag)"
        $failureCount++
    }
    
    Write-Host ""
}

# Summary
Print-Header "PUSH SUMMARY"

Write-Host "✓ Successfully pushed: $successCount" -ForegroundColor Green
Write-Host "✗ Failed: $failureCount" -ForegroundColor Red
Write-Host ""

if ($failureCount -eq 0) {
    Write-Host "All images pushed successfully to Docker Hub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your images are now available:" -ForegroundColor Cyan
    Write-Host "  docker pull $Username/chimera2os:latest"
    Write-Host "  docker pull $Username/chimera2os:v1.0.0"
    Write-Host "  docker pull $Username/chimera2os:comprehensive"
    Write-Host "  docker pull $Username/chimeraiios:iso"
    Write-Host ""
    Write-Host "View on Docker Hub:" -ForegroundColor Cyan
    Write-Host "  https://hub.docker.com/r/$Username/chimera2os"
    Write-Host "  https://hub.docker.com/r/$Username/chimeraiios"
}
else {
    Write-Host "Some images failed to push. Please check the errors above." -ForegroundColor Red
}
