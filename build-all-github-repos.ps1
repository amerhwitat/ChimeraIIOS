# =============================================================================
# GITHUB TO DOCKER HUB - COMPLETE REPOSITORY BUILDER (PowerShell)
# =============================================================================
# Discovers all GitHub repositories, builds Docker images, pushes to Docker Hub

param(
    [string]$GitHubUser = "amerhwitat",
    [string]$DockerUser = "amerhwitat",
    [string]$GitHubToken = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildDir = Join-Path (Get-Location) "docker-hub-build"
$ReposDir = Join-Path $BuildDir "repos"
$OutputDir = Join-Path $BuildDir "output"
$LogFile = Join-Path $BuildDir "build-all-repos-ps1.log"
$ReportFile = Join-Path $BuildDir "DOCKER_HUB_BUILD_REPORT.txt"
$RegistryIndex = Join-Path $BuildDir "DOCKER_HUB_REGISTRY_INDEX.md"

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
    Write-Host "║     GITHUB → DOCKER HUB - COMPLETE REPOSITORY BUILDER         ║" -ForegroundColor Magenta
    Write-Host "║                                                                ║" -ForegroundColor Magenta
    Write-Host "║  Auto-discover repos, build images, push to Docker Hub        ║" -ForegroundColor Magenta
    Write-Host "║  Created by Amer Abdullah Suleiman Hwitat - عامر الحويطات  ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Initialize-System {
    Show-Banner
    
    if (-not (Test-Path $ReposDir)) { New-Item -ItemType Directory -Path $ReposDir -Force | Out-Null }
    if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }
    
    "GitHub to Docker Hub Build System" > $LogFile
    Add-Content $LogFile "Started: $(Get-Date)"
    
    Write-Status "Build system initialized" "Success"
    Write-Status "GitHub user: $GitHubUser" "Info"
    Write-Status "Docker Hub user: $DockerUser" "Info"
    Write-Status "Build directory: $BuildDir" "Info"
    
    # Check prerequisites
    try {
        $dockerVersion = docker --version
        Write-Status "Docker: $dockerVersion" "Success"
    }
    catch {
        Write-Status "Docker not found" "Error"
        exit 1
    }
    
    try {
        $gitVersion = git --version
        Write-Status "Git: $gitVersion" "Success"
    }
    catch {
        Write-Status "Git not found" "Error"
        exit 1
    }
}

function Discover-Repositories {
    Write-Status "Discovering all GitHub repositories for user: $GitHubUser" "Info"
    
    $page = 1
    $perPage = 100
    $reposFile = Join-Path $BuildDir "discovered_repos.txt"
    $null | Out-File -FilePath $reposFile -Force
    
    $totalDiscovered = 0
    
    while ($true) {
        Write-Status "Fetching page $page of repositories..." "Info"
        
        $url = "https://api.github.com/users/${GitHubUser}/repos?page=${page}&per_page=${perPage}&sort=updated"
        
        if ($GitHubToken) {
            $url = "$url&access_token=$GitHubToken"
        }
        
        try {
            $response = Invoke-RestMethod -Uri $url -ErrorAction Stop
            
            if ($response.Count -eq 0) {
                break
            }
            
            foreach ($repo in $response) {
                Add-Content $reposFile $repo.name
                $totalDiscovered++
            }
            
            $page++
        }
        catch {
            Write-Status "Error fetching repositories: $_" "Warning"
            break
        }
    }
    
    Write-Status "Discovered $totalDiscovered repositories" "Success"
    
    Write-Status "Repositories found:" "Info"
    Get-Content $reposFile | Select-Object -First 20 | ForEach-Object { Write-Status "  - $_" "Info" }
    
    if ($totalDiscovered -gt 20) {
        Write-Status "... and $($totalDiscovered - 20) more repositories" "Info"
    }
    
    return $totalDiscovered
}

function Detect-AppType {
    param([string]$RepoPath)
    
    $appType = "app-generic"
    $language = "Unknown"
    $framework = ""
    
    # Node.js
    if (Test-Path "$RepoPath/package.json") {
        $packageContent = Get-Content "$RepoPath/package.json" -Raw
        $language = "Node.js"
        
        if ($packageContent -match '"next"') { $appType = "web-nextjs"; $framework = "Next.js" }
        elseif ($packageContent -match '"react"') { $appType = "web-react"; $framework = "React" }
        elseif ($packageContent -match '"vue"') { $appType = "web-vue"; $framework = "Vue.js" }
        elseif ($packageContent -match '"express"') { $appType = "api-express"; $framework = "Express" }
        elseif ($packageContent -match '"nuxt"') { $appType = "web-nuxt"; $framework = "Nuxt" }
        else { $appType = "app-nodejs" }
    }
    
    # Python
    if ((Test-Path "$RepoPath/requirements.txt") -or (Test-Path "$RepoPath/pyproject.toml") -or (Test-Path "$RepoPath/setup.py")) {
        $language = "Python"
        
        if (Get-ChildItem "$RepoPath" -Recurse -Include "*.py" | Select-String "flask" -Quiet) {
            $appType = "api-flask"; $framework = "Flask"
        }
        elseif (Get-ChildItem "$RepoPath" -Recurse -Include "*.py" | Select-String "django" -Quiet) {
            $appType = "web-django"; $framework = "Django"
        }
        elseif (Get-ChildItem "$RepoPath" -Recurse -Include "*.py" | Select-String "fastapi" -Quiet) {
            $appType = "api-fastapi"; $framework = "FastAPI"
        }
        else { $appType = "app-python" }
    }
    
    # Go
    if ((Test-Path "$RepoPath/go.mod") -or (Test-Path "$RepoPath/main.go")) {
        $language = "Go"
        $appType = "app-go"
    }
    
    # Mobile
    if ((Test-Path "$RepoPath/app.json") -and (Test-Path "$RepoPath/package.json")) {
        $appType = "mobile-react-native"
        $language = "React Native"
    }
    
    if (Test-Path "$RepoPath/pubspec.yaml") {
        $appType = "mobile-flutter"
        $language = "Flutter"
    }
    
    # Dockerfile already exists
    if (Test-Path "$RepoPath/Dockerfile") {
        $appType = "app-pre-dockerized"
    }
    
    return "$appType|$language|$framework"
}

function Generate-Dockerfile {
    param([string]$RepoPath, [string]$AppType, [string]$RepoName)
    
    $dockerfilePath = Join-Path $RepoPath "Dockerfile"
    
    if (Test-Path $dockerfilePath) {
        return
    }
    
    Write-Status "Generating Dockerfile for $RepoName ($AppType)" "Info"
    
    $dockerfileContent = @{
        "web-nextjs" = @"
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]
"@
        "web-react" = @"
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"@
        "api-express" = @"
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
"@
        "api-flask" = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
"@
        "api-fastapi" = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
"@
        "mobile-react-native" = @"
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 8081
CMD ["npm", "start"]
"@
        "app-go" = @"
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o app .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/app .
EXPOSE 8080
CMD ["./app"]
"@
        "app-python" = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt . 2>/dev/null || echo ""
RUN [ -f requirements.txt ] && pip install --no-cache-dir -r requirements.txt || true
COPY . .
CMD ["python", "main.py"]
"@
    }
    
    $content = $dockerfileContent[$AppType] -or @"
FROM ubuntu:24.04
WORKDIR /app
COPY . .
CMD ["/bin/bash"]
"@
    
    Set-Content $dockerfilePath $content
    Write-Status "Generated Dockerfile for $RepoName" "Success"
}

function Clone-Repositories {
    $reposFile = Join-Path $BuildDir "discovered_repos.txt"
    $repos = Get-Content $reposFile
    $repoCount = 0
    $totalRepos = $repos.Count
    
    Write-Status "Cloning all repositories..." "Info"
    
    foreach ($repoName in $repos) {
        $repoCount++
        
        Write-Status "[$repoCount/$totalRepos] Cloning: $repoName" "Info"
        
        $repoUrl = "https://github.com/${GitHubUser}/${repoName}.git"
        $repoPath = Join-Path $ReposDir $repoName
        
        if (Test-Path $repoPath) {
            Write-Status "Repository already exists, updating..." "Info"
            Push-Location $repoPath
            git pull origin main 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) { git pull origin master 2>&1 | Out-Null }
            Pop-Location
        }
        else {
            if (git clone $repoUrl $repoPath 2>&1 | Out-Null) {
                Write-Status "Cloned: $repoName" "Success"
            }
            else {
                Write-Status "Failed to clone: $repoName" "Warning"
            }
        }
    }
}

function Build-DockerImages {
    $reposFile = Join-Path $BuildDir "discovered_repos.txt"
    $repos = Get-Content $reposFile
    $repoCount = 0
    $totalRepos = $repos.Count
    $successful = 0
    $failed = 0
    $imagesFile = Join-Path $BuildDir "built_images.txt"
    $null | Out-File -FilePath $imagesFile -Force
    
    Write-Status "Building Docker images..." "Build"
    
    foreach ($repoName in $repos) {
        $repoCount++
        
        $repoPath = Join-Path $ReposDir $repoName
        if (-not (Test-Path $repoPath)) { continue }
        
        Write-Status "[$repoCount/$totalRepos] Building: $repoName" "Build"
        
        Push-Location $repoPath
        
        # Detect app type
        $appInfo = Detect-AppType $repoPath
        $appType = $appInfo.Split("|")[0]
        $language = $appInfo.Split("|")[1]
        
        # Generate Dockerfile
        Generate-Dockerfile $repoPath $appType $repoName
        
        # Build image
        $imageName = "${DockerUser}/$($repoName.ToLower())"
        
        docker rmi "${imageName}:latest" 2>$null | Out-Null
        
        if (docker build -t "${imageName}:latest" --label "maintainer=$GitHubUser" --label "app_type=$appType" --label "language=$language" . 2>&1 | Out-Null) {
            docker tag "${imageName}:latest" "${imageName}:v1.0.0" 2>&1 | Out-Null
            docker tag "${imageName}:latest" "${imageName}:stable" 2>&1 | Out-Null
            
            Write-Status "Built: $repoName [$repoCount/$totalRepos]" "Success"
            
            Add-Content $imagesFile "${imageName}|${appType}|${language}"
            $successful++
        }
        else {
            Write-Status "Failed to build: $repoName" "Error"
            $failed++
        }
        
        Pop-Location
    }
    
    Write-Status "Build complete: $successful successful, $failed failed" "Build"
}

function Push-ImagesToHub {
    $imagesFile = Join-Path $BuildDir "built_images.txt"
    
    if (-not (Test-Path $imagesFile)) {
        Write-Status "No images to push" "Warning"
        return
    }
    
    Write-Status "Pushing images to Docker Hub..." "Build"
    
    docker login -u $DockerUser 2>&1 | Out-Null
    
    $images = Get-Content $imagesFile
    $totalImages = $images.Count
    $current = 0
    
    foreach ($imageLine in $images) {
        $current++
        $imageName = $imageLine.Split("|")[0]
        
        Write-Status "[$current/$totalImages] Pushing: $imageName" "Build"
        
        foreach ($tag in @("latest", "v1.0.0", "stable")) {
            docker push "${imageName}:${tag}" 2>&1 | Out-Null
            Start-Sleep -Seconds 1
        }
    }
    
    Write-Status "Push complete" "Success"
}

function Main {
    Initialize-System
    
    $totalRepos = Discover-Repositories
    if ($totalRepos -eq 0) {
        Write-Status "No repositories found" "Error"
        exit 1
    }
    
    Clone-Repositories
    Build-DockerImages
    Push-ImagesToHub
    
    Write-Host ""
    Write-Status "ALL REPOSITORIES BUILT AND PUSHED!" "Success"
    Write-Status "Docker Hub: https://hub.docker.com/u/$DockerUser" "Info"
}

Main
