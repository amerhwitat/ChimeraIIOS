#!/usr/bin/env pwsh

# =============================================================================
# GITHUB SETUP & PUSH SCRIPT (PowerShell) - CHIMERA II OS
# =============================================================================
# Windows PowerShell version of GitHub repository setup
# 
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويطات
# Contact: amer.hwitat@proton.me
# Usage: .\github-setup.ps1
# =============================================================================

param(
    [switch]$Push = $false,
    [string]$Branch = "main",
    [string]$Remote = "origin"
)

# Colors
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

# Main execution
Print-Header "CHIMERA II OS - GITHUB SETUP (PowerShell)"

# Check git
Write-Info "Checking git installation..."
try {
    $gitVersion = git --version
    Write-Success $gitVersion
}
catch {
    Write-Error-Custom "Git not found. Install from https://git-scm.com"
    exit 1
}

# Check directory
Write-Info "Checking repository directory..."
if (-not (Test-Path "Dockerfile.fixed")) {
    Write-Error-Custom "Dockerfile.fixed not found. Run from ChimeraIIOS directory."
    exit 1
}
Write-Success "Found Dockerfile.fixed"

# Configure git
Write-Info "Configuring git..."
git config --global user.name "Amer Abdullah Suleiman Hwitat" | Out-Null
git config --global user.email "amer.hwitat@proton.me" | Out-Null
Write-Success "Git configured"

# Initialize git if needed
if (-not (Test-Path ".git")) {
    Write-Info "Initializing git repository..."
    git init | Out-Null
    git config user.name "Amer Abdullah Suleiman Hwitat" | Out-Null
    git config user.email "amer.hwitat@proton.me" | Out-Null
    Write-Success "Repository initialized"
}
else {
    Write-Warning-Custom "Repository already initialized"
}

# Create .gitignore
Write-Info "Setting up .gitignore..."
if (-not (Test-Path ".gitignore")) {
    $gitignore = @"
# Build artifacts
*.o
*.a
*.so
*.dylib
*.dll
*.exe
*.out

# Docker
*.tar
*.tar.gz
docker-compose.override.yml

# ISO files
*.iso
*.iso.sha256
*.iso.md5
build-report.txt

# Build directories
build/
dist/
.build/
cmake-build-debug/
cmake-build-release/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Python
__pycache__/
*.py[cod]
.Python
venv/
ENV/
env/

# Node
node_modules/
npm-debug.log
yarn-error.log

# Rust
target/
Cargo.lock

# Environment
.env
.env.local
secrets/
*.key

# OS
Thumbs.db
.DS_Store

# Temporary
*.tmp
*.temp
*.backup
*.bak
*~

# Large files
*.tar.bz2
*.zip
*.rar
"@
    $gitignore | Out-File -Encoding UTF8 ".gitignore"
    Write-Success ".gitignore created"
}

# Add files
Write-Info "Adding files to git..."
git add -A | Out-Null
Write-Host (git status) -ForegroundColor Gray

# Commit
Write-Info "Creating initial commit..."
$commitMessage = @"
Initial commit: Chimera II OS - Comprehensive Docker + ISO Build System

- Multi-stage Dockerfile for complete compilation
- 13 integrated GitHub repositories  
- Complete development toolchain (GCC, Python, Node, Rust, Java, .NET)
- Docker Compose orchestration (5 services)
- ISO builder for bootable images (BIOS/UEFI)
- WSL2 setup guide for Windows users
- Comprehensive documentation

Created by: Amer Abdullah Suleiman Hwitat - عامر الحويطات
Contact: amer.hwitat@proton.me
"@

try {
    git commit -m $commitMessage | Out-Null
    Write-Success "Initial commit created"
}
catch {
    Write-Warning-Custom "No changes to commit (repository may already have commits)"
}

# Set default branch
Write-Info "Setting default branch to $Branch..."
git branch -M $Branch 2>&1 | Out-Null
Write-Success "Branch configured"

# Display instructions
Print-Header "NEXT STEPS - PUSH TO GITHUB"

$instructions = @"
To push this repository to GitHub:

1. CREATE REPOSITORY ON GITHUB:
   - Go to https://github.com/new
   - Repository name: ChimeraIIOS
   - Description: "Comprehensive Docker image and bootable ISO with 13 integrated repos"
   - Visibility: Public
   - Do NOT initialize with README, .gitignore, or license
   - Click "Create repository"

2. COPY & RUN COMMANDS BELOW:

   # Via HTTPS (no SSH key needed):
   git remote add $Remote https://github.com/amerhwitat/ChimeraIIOS.git
   git branch -M $Branch
   git push -u $Remote $Branch

   # Via SSH (requires GitHub SSH key):
   git remote add $Remote git@github.com:amerhwitat/ChimeraIIOS.git
   git branch -M $Branch
   git push -u $Remote $Branch

3. VERIFY:
   - Visit https://github.com/amerhwitat/ChimeraIIOS
   - Confirm all files are present
   - Check: git log --oneline

4. OPTIONAL - CREATE RELEASE:
   git tag -a v1.0.0 -m "Initial release: Chimera II OS v1.0.0"
   git push origin v1.0.0
"@

Write-Host $instructions

Print-Header "SETUP COMPLETE"
Write-Success "Repository is ready to push to GitHub"
Write-Info "Follow instructions above to push to GitHub"
Write-Info "GitHub repository must be created manually at https://github.com/new"
