#!/bin/bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd)"
cd "$CHIMERA_REPO_ROOT"

# =============================================================================
# GITHUB SETUP & PUSH SCRIPT - CHIMERA II OS
# =============================================================================
# Initializes git repository and pushes to GitHub
# 
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويطات
# Contact: amer.hwitat@proton.me
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_NAME="ChimeraIIOS"
REPO_URL_PATTERN="https://github.com/amerhwitat/ChimeraIIOS.git"
AUTHOR_NAME="Amer Abdullah Suleiman Hwitat"
AUTHOR_EMAIL="amer.hwitat@proton.me"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

print_header() {
    echo ""
    echo "=================================================================="
    echo "$*"
    echo "=================================================================="
    echo ""
}

# =============================================================================
# MAIN SETUP
# =============================================================================

main() {
    print_header "CHIMERA II OS - GITHUB SETUP & PUSH"
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install git first."
        exit 1
    fi
    
    log_info "Git version: $(git --version)"
    
    # Check current directory
    if [ ! -f "Dockerfile.fixed" ]; then
        log_error "Please run this script from the ChimeraIIOS repository directory"
        exit 1
    fi
    
    log_success "Found Dockerfile.fixed - continuing in correct directory"
    
    # Configure git
    log_info "Configuring git..."
    git config --global user.name "$AUTHOR_NAME" || true
    git config --global user.email "$AUTHOR_EMAIL" || true
    log_success "Git configured"
    
    # Initialize repository if not already initialized
    if [ ! -d ".git" ]; then
        log_info "Initializing git repository..."
        git init
        git config user.name "$AUTHOR_NAME"
        git config user.email "$AUTHOR_EMAIL"
        log_success "Repository initialized"
    else
        log_warning "Repository already initialized"
    fi
    
    # Copy .gitignore
    if [ ! -f ".gitignore" ]; then
        log_info "Setting up .gitignore..."
        cp .gitignore_full .gitignore 2>/dev/null || \
        cat > .gitignore << 'GITIGNORE'
*.o
*.a
*.so
*.dylib
*.dll
*.exe
*.tar
*.tar.gz
*.iso
*.iso.sha256
*.iso.md5
build/
dist/
node_modules/
__pycache__/
.vscode/
.idea/
*.swp
.env
secrets/
build.log
*.tmp
GITIGNORE
        log_success ".gitignore created"
    fi
    
    # Add all files
    log_info "Adding files to git..."
    git add -A
    git status
    
    # Commit
    log_info "Creating initial commit..."
    if git commit -m "Initial commit: Chimera II OS - Comprehensive Docker + ISO Build System

- Multi-stage Dockerfile for complete compilation
- 13 integrated GitHub repositories
- Complete development toolchain (GCC, Python, Node, Rust, Java, .NET)
- Docker Compose orchestration (5 services)
- ISO builder for bootable images (BIOS/UEFI)
- WSL2 setup guide for Windows users
- Comprehensive documentation

Created by: Amer Abdullah Suleiman Hwitat - عامر الحويطات
Contact: amer.hwitat@proton.me" 2>/dev/null; then
        log_success "Initial commit created"
    else
        log_warning "No changes to commit (repository may already have commits)"
    fi
    
    # Set default branch
    log_info "Setting default branch to main..."
    git branch -M main 2>/dev/null || true
    log_success "Branch configured"
    
    # Display push instructions
    print_header "NEXT STEPS - PUSH TO GITHUB"
    
    cat << 'INSTRUCTIONS'
To push this repository to GitHub:

1. CREATE REPOSITORY ON GITHUB:
   - Go to https://github.com/new
   - Repository name: ChimeraIIOS
   - Description: "Comprehensive Docker image and bootable ISO with 13 integrated repos"
   - Visibility: Public
   - Do NOT initialize with README, .gitignore, or license
   - Click "Create repository"

2. ADD REMOTE AND PUSH:
   
   # Option A - HTTPS (if no SSH key)
   git remote add origin https://github.com/amerhwitat/ChimeraIIOS.git
   git branch -M main
   git push -u origin main
   
   # Option B - SSH (if SSH key configured)
   git remote add origin git@github.com:amerhwitat/ChimeraIIOS.git
   git branch -M main
   git push -u origin main

3. VERIFY:
   - Visit https://github.com/amerhwitat/ChimeraIIOS
   - Confirm all files are present
   - Check git log: git log --oneline

4. OPTIONAL - ADD TOPICS:
   - Go to repository settings
   - Add topics: docker, chimera, iso, linux, build-system, wsl2

5. OPTIONAL - CREATE RELEASE:
   git tag -a v1.0.0 -m "Initial release: Chimera II OS v1.0.0"
   git push origin v1.0.0

INSTRUCTIONS
    
    print_header "PUSH COMMANDS READY"
    
    log_success "Repository is ready for GitHub"
    log_info "Run the commands above to push to GitHub"
    log_info "GitHub repository must be created manually first"
}

# Execute
main
