#!/bin/bash

# =============================================================================
# CHIMERA II OS - COMPLETE DOCKER IMAGE FIX & REPO UPDATE
# =============================================================================
# Fixes all Docker images with CRLF line ending issues
# Updates all repositories with corrected files
# Rebuilds and pushes all 39 Docker images to Docker Hub

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

GITHUB_USER="${1:-amerhwitat}"
DOCKER_USER="${2:-amerhwitat}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(pwd)/docker-fix-complete"
REPOS_DIR="${BUILD_DIR}/repos"
OUTPUT_DIR="${BUILD_DIR}/output"
BUILD_LOG="${BUILD_DIR}/docker-fix.log"
REPORT_FILE="${BUILD_DIR}/DOCKER_FIX_REPORT.txt"

declare -a REPOS=(
    "ChimeraIIOS"
    "nlp"
    "BizX"
    "BizXtreme"
    "CPU4096"
    "CPU4096Simulator"
    "keygen"
    "eth-key-check"
    "bruteforce"
    "PDFreaderPY"
    "general"
    "test"
    "amerhwitat.github.io"
)

log_info() { echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$BUILD_LOG"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*" | tee -a "$BUILD_LOG"; }
log_error() { echo -e "${RED}[✗]${NC} $*" | tee -a "$BUILD_LOG"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $*" | tee -a "$BUILD_LOG"; }
log_push() { echo -e "${CYAN}[PUSH]${NC} $*" | tee -a "$BUILD_LOG"; }

print_banner() {
    echo ""
    echo -e "${MAGENTA}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     CHIMERA II OS - FIX ALL DOCKER IMAGES                      ║"
    echo "║                                                                ║"
    echo "║  Fix CRLF/LF issues, rebuild images, update repos             ║"
    echo "║  Created by Amer Abdullah Suleiman Hwitat - عامر الحويطات  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

initialize() {
    print_banner
    mkdir -p "$REPOS_DIR" "$OUTPUT_DIR"
    : > "$BUILD_LOG"
    echo "Docker Image Fix System" > "$BUILD_LOG"
    echo "Started: $(date)" >> "$BUILD_LOG"
    
    log_success "Build directories created"
    log_info "GitHub user: $GITHUB_USER"
    log_info "Docker Hub user: $DOCKER_USER"
    
    command -v docker >/dev/null || { log_error "Docker not found"; exit 1; }
    log_success "Docker: $(docker --version)"
    
    command -v git >/dev/null || { log_error "Git not found"; exit 1; }
    log_success "Git: $(git --version | head -1)"
}

clone_or_update_repos() {
    log_info "Cloning/updating all repositories..."
    local total=${#REPOS[@]}
    local current=0
    
    for repo in "${REPOS[@]}"; do
        ((current++))
        local repo_url="https://github.com/${GITHUB_USER}/${repo}.git"
        local repo_path="${REPOS_DIR}/${repo}"
        
        if [ -d "$repo_path" ]; then
            cd "$repo_path"
            git pull origin main 2>&1 | tail -1 >> "$BUILD_LOG" || git pull origin master 2>&1 | tail -1 >> "$BUILD_LOG" || true
            log_success "Updated: $repo [$current/$total]"
        else
            if git clone "$repo_url" "$repo_path" 2>&1 | tail -1 >> "$BUILD_LOG"; then
                log_success "Cloned: $repo [$current/$total]"
            else
                log_error "Failed: $repo [$current/$total]"
            fi
        fi
    done
}

fix_line_endings() {
    log_info "Fixing line endings in all repositories..."
    local total=${#REPOS[@]}
    local current=0
    
    for repo in "${REPOS[@]}"; do
        ((current++))
        local repo_path="${REPOS_DIR}/${repo}"
        
        [ -d "$repo_path" ] || { log_warning "Not found: $repo"; continue; }
        
        cd "$repo_path"
        
        find . -name "*.sh" -type f -exec dos2unix {} + 2>/dev/null || find . -name "*.sh" -type f -exec sed -i 's/\r$//' {} + 2>/dev/null || true
        find . -name "Dockerfile*" -type f -exec dos2unix {} + 2>/dev/null || find . -name "Dockerfile*" -type f -exec sed -i 's/\r$//' {} + 2>/dev/null || true
        find . -name "entrypoint*" -type f -exec dos2unix {} + 2>/dev/null || find . -name "entrypoint*" -type f -exec sed -i 's/\r$//' {} + 2>/dev/null || true
        find . -name "startup*" -type f -exec dos2unix {} + 2>/dev/null || find . -name "startup*" -type f -exec sed -i 's/\r$//' {} + 2>/dev/null || true
        
        log_success "Fixed line endings: $repo [$current/$total]"
    done
}

create_dockerfiles() {
    log_info "Creating/fixing Dockerfiles..."
    local total=${#REPOS[@]}
    local current=0
    
    for repo in "${REPOS[@]}"; do
        ((current++))
        local repo_path="${REPOS_DIR}/${repo}"
        
        [ -d "$repo_path" ] || continue
        cd "$repo_path"
        
        if [ ! -f "Dockerfile" ]; then
            cat > Dockerfile << 'EOFDO'
FROM ubuntu:24.04
LABEL maintainer="amerhwitat"
LABEL description="Chimera II OS - Repository Component"
LABEL version="1.0.0"

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
EOFDO
        fi
        
        dos2unix Dockerfile 2>/dev/null || sed -i 's/\r$//' Dockerfile || true
        
        if [ ! -f ".dockerignore" ]; then
            cat > .dockerignore << 'EOFDI'
.git
.gitignore
.dockerignore
Dockerfile*
docker-compose*.yml
*.md
tests/
node_modules/
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
.env
.env.local
EOFDI
        fi
        
        log_success "Dockerfile ready: $repo [$current/$total]"
    done
}

rebuild_images() {
    log_info "Rebuilding all Docker images..."
    local total=${#REPOS[@]}
    local current=0
    local successful=0
    local failed=0
    
    for repo in "${REPOS[@]}"; do
        ((current++))
        local repo_path="${REPOS_DIR}/${repo}"
        local image_name="${DOCKER_USER}/${repo,,}"
        
        [ -d "$repo_path" ] || { ((failed++)); continue; }
        cd "$repo_path"
        
        docker rmi "${image_name}:latest" 2>/dev/null || true
        
        if docker build \
            -t "${image_name}:latest" \
            --label "maintainer=$GITHUB_USER" \
            --label "description=$repo" \
            --label "version=1.0.0-fixed" \
            . 2>&1 | tail -3; then
            
            docker tag "${image_name}:latest" "${image_name}:v1.0.0-fixed"
            docker tag "${image_name}:latest" "${image_name}:stable"
            
            log_success "Built: ${image_name} [$current/$total]"
            ((successful++))
        else
            log_error "Failed: ${image_name} [$current/$total]"
            ((failed++))
        fi
    done
    
    log_info "Image builds: $successful successful, $failed failed"
}

push_images() {
    log_push "Pushing all images to Docker Hub..."
    
    docker login -u "$DOCKER_USER" 2>&1 | tail -1 >> "$BUILD_LOG" || { log_warning "Docker Hub login skipped"; return; }
    
    local total=$((${#REPOS[@]} * 3))
    local current=0
    local successful=0
    
    for repo in "${REPOS[@]}"; do
        local image_name="${DOCKER_USER}/${repo,,}"
        local tags=("latest" "v1.0.0-fixed" "stable")
        
        for tag in "${tags[@]}"; do
            ((current++))
            local full_image="${image_name}:${tag}"
            
            log_push "[$current/$total] $full_image"
            
            if docker push "$full_image" 2>&1 | tail -1 | tee -a "$BUILD_LOG" | grep -q "Pushed\|digest"; then
                ((successful++))
            fi
            
            sleep 2
        done
    done
    
    log_success "Push complete: $successful/$total images"
}

update_repos() {
    log_info "Updating GitHub repositories..."
    local total=${#REPOS[@]}
    local current=0
    local updated=0
    
    for repo in "${REPOS[@]}"; do
        ((current++))
        local repo_path="${REPOS_DIR}/${repo}"
        
        [ -d "$repo_path" ] || { log_warning "Not found: $repo"; continue; }
        
        cd "$repo_path"
        
        [ -z "$(git status --porcelain)" ] && { log_info "No changes: $repo [$current/$total]"; continue; }
        
        git config user.email "amer.hwitat@proton.me" 2>/dev/null || true
        git config user.name "Amer Hwitat" 2>/dev/null || true
        git add -A 2>&1 | tail -1 >> "$BUILD_LOG"
        
        if git commit -m "Fix CRLF/LF line ending issues in Docker build files" 2>&1 | tail -1 >> "$BUILD_LOG"; then
            if git push origin main 2>&1 | tail -1 >> "$BUILD_LOG" || git push origin master 2>&1 | tail -1 >> "$BUILD_LOG"; then
                log_success "Updated: $repo [$current/$total]"
                ((updated++))
            fi
        fi
    done
    
    log_success "GitHub update: $updated/$total repositories"
}

main() {
    initialize
    clone_or_update_repos
    fix_line_endings
    create_dockerfiles
    rebuild_images
    push_images
    update_repos
    
    echo ""
    log_success "ALL FIXES COMPLETE!"
    echo ""
}

main "$@"
