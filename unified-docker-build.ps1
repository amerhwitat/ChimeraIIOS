# =============================================================================
# UNIFIED DOCKER IMAGE - COMPLETE REPOSITORY INTEGRATION (PowerShell)
# =============================================================================
# Combines all GitHub repositories into single unified image

param(
    [string]$GitHubUser = "amerhwitat",
    [string]$DockerUser = "amerhwitat"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildDir = Join-Path (Get-Location) "chimera-unified-build"
$ReposDir = Join-Path $BuildDir "repos"
$IntegrationDir = Join-Path $BuildDir "integrated"
$OutputDir = Join-Path $BuildDir "output"
$LogFile = Join-Path $BuildDir "unified-build-ps1.log"
$ReportFile = Join-Path $BuildDir "UNIFIED_BUILD_REPORT.txt"

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $colors = @{
        "Info"    = "Cyan"
        "Success" = "Green"
        "Error"   = "Red"
        "Warning" = "Yellow"
        "Build"   = "Magenta"
    }
    
    $time = (Get-Date -Format "HH:mm:ss")
    $output = "[$time] $Message"
    
    Write-Host $output -ForegroundColor $colors[$Type]
    Add-Content $LogFile $output
}

function Show-Banner {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║     UNIFIED DOCKER IMAGE - COMPLETE REPOSITORY INTEGRATION    ║" -ForegroundColor Magenta
    Write-Host "║                                                                ║" -ForegroundColor Magenta
    Write-Host "║  Combine, compile, fix, and integrate all GitHub repos       ║" -ForegroundColor Magenta
    Write-Host "║  Created by Amer Abdullah Suleiman Hwitat - عامر الحويطات  ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Initialize-System {
    Show-Banner
    
    @($ReposDir, $IntegrationDir, $OutputDir) | ForEach-Object {
        if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
    }
    
    "Unified Docker Build System" > $LogFile
    Add-Content $LogFile "Started: $(Get-Date)"
    
    Write-Status "Build system initialized" "Success"
    Write-Status "GitHub user: $GitHubUser" "Info"
    Write-Status "Docker Hub user: $DockerUser" "Info"
    Write-Status "Build directory: $BuildDir" "Info"
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Status "Docker: $dockerVersion" "Success"
    }
    catch {
        Write-Status "Docker not found" "Error"
        exit 1
    }
}

function Discover-Repositories {
    Write-Status "Discovering all repositories..." "Info"
    
    $repos = @(
        "ChimeraIIOS",
        "nlp",
        "BizX",
        "BizXtreme",
        "CPU4096",
        "CPU4096Simulator",
        "keygen",
        "eth-key-check",
        "bruteforce",
        "PDFreaderPY",
        "general",
        "test",
        "amerhwitat.github.io"
    )
    
    Write-Status "Discovered $($repos.Count) repositories" "Success"
    
    $repos | ForEach-Object { Write-Status "  - $_" "Info" }
    
    return $repos
}

function Clone-Repositories {
    param([array]$Repos)
    
    Write-Status "Cloning all repositories..." "Info"
    
    $count = 0
    foreach ($repo in $Repos) {
        $count++
        Write-Status "[$count/$($Repos.Count)] Cloning: $repo" "Info"
        
        $repoUrl = "https://github.com/${GitHubUser}/${repo}.git"
        $repoPath = Join-Path $ReposDir $repo
        
        if (Test-Path $repoPath) {
            Write-Status "  Repository exists, updating..." "Info"
            Push-Location $repoPath
            git pull origin main 2>&1 | Out-Null
            Pop-Location
        }
        else {
            if (git clone $repoUrl $repoPath 2>&1 | Out-Null) {
                Write-Status "  Cloned: $repo" "Success"
            }
            else {
                Write-Status "  Failed to clone: $repo" "Warning"
            }
        }
    }
}

function Build-UnifiedImage {
    param([array]$Repos)
    
    Write-Status "Creating unified image structure..." "Build"
    
    # Create directories
    @("$IntegrationDir\app", "$IntegrationDir\app\services", "$IntegrationDir\app\web", "$IntegrationDir\app\bin") | ForEach-Object {
        if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
    }
    
    # Copy repositories
    $count = 0
    foreach ($repo in $Repos) {
        $count++
        Write-Status "[$count/$($Repos.Count)] Integrating: $repo" "Build"
        
        $repoPath = Join-Path $ReposDir $repo
        if (Test-Path $repoPath) {
            if ($repo -match "(web|front|app|next|react|vue|portfolio)") {
                Copy-Item -Path $repoPath -Destination "$IntegrationDir\app\web\$repo" -Recurse -Force -ErrorAction SilentlyContinue
            }
            elseif ($repo -match "(service|api|nlp|data)") {
                Copy-Item -Path $repoPath -Destination "$IntegrationDir\app\services\$repo" -Recurse -Force -ErrorAction SilentlyContinue
            }
            else {
                Copy-Item -Path $repoPath -Destination "$IntegrationDir\app\bin\$repo" -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    Write-Status "Unified structure created" "Success"
}

function Build-DockerImage {
    Write-Status "Building unified Docker image..." "Build"
    
    $imageName = "${DockerUser}/chimera-os"
    
    # Remove old image
    docker rmi "${imageName}:latest" 2>$null | Out-Null
    
    # Build
    Push-Location $IntegrationDir
    
    if (docker build -t "${imageName}:latest" --label "maintainer=$GitHubUser" --label "description=Chimera II OS Unified" . 2>&1 | Out-Null) {
        docker tag "${imageName}:latest" "${imageName}:v1.0.0-unified" 2>&1 | Out-Null
        docker tag "${imageName}:latest" "${imageName}:stable" 2>&1 | Out-Null
        
        Write-Status "Built: $imageName" "Success"
        $imageName | Out-File -FilePath "$BuildDir\built_image.txt"
    }
    else {
        Write-Status "Build failed" "Error"
    }
    
    Pop-Location
}

function Push-ToDockerHub {
    Write-Status "Pushing image to Docker Hub..." "Build"
    
    $imageFile = "$BuildDir\built_image.txt"
    if (-not (Test-Path $imageFile)) { return }
    
    $imageName = Get-Content $imageFile
    
    docker login -u $DockerUser 2>$null | Out-Null
    
    @("latest", "v1.0.0-unified", "stable", "unified") | ForEach-Object {
        Write-Status "Pushing: ${imageName}:$_" "Build"
        docker push "${imageName}:$_" 2>&1 | Out-Null
    }
    
    Write-Status "Push complete" "Success"
}

function Main {
    Initialize-System
    $repos = Discover-Repositories
    Clone-Repositories $repos
    Build-UnifiedImage $repos
    Build-DockerImage
    Push-ToDockerHub
    
    Write-Host ""
    Write-Status "UNIFIED IMAGE BUILD COMPLETE!" "Success"
    Write-Status "Image: ${DockerUser}/chimera-os:latest" "Info"
}

Main
