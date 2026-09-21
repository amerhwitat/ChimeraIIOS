#!/bin/bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd)"
cd "$CHIMERA_REPO_ROOT"

# =============================================================================
# DOCKER HUB PUSH SCRIPT - CHIMERA II OS
# =============================================================================
# Pushes all Docker images to Docker Hub
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويطات
# Contact: amer.hwitat@proton.me
# Usage: bash docker-hub-push.sh
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-amerhwitat}"
REGISTRY="docker.io"

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
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "DOCKER HUB PUSH - CHIMERA II OS"
    
    # Check Docker is running
    log_info "Checking Docker daemon..."
    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    log_success "Docker daemon is running"
    
    # Check Docker Hub credentials
    log_info "Checking Docker Hub login..."
    if ! docker info | grep -q "Username"; then
        log_warning "Not logged in to Docker Hub"
        log_info "Please run: docker login"
        echo ""
        echo "To login to Docker Hub:"
        echo "1. Go to https://hub.docker.com/settings/security"
        echo "2. Create a Personal Access Token"
        echo "3. Run: docker login -u $DOCKER_USERNAME"
        echo "4. Enter your username and token when prompted"
        echo ""
        exit 1
    fi
    log_success "Docker Hub login confirmed"
    
    # Get Docker username from config
    if [ -f ~/.docker/config.json ]; then
        DOCKER_USERNAME=$(grep -o '"credsStore"\|"auths"' ~/.docker/config.json | head -1 || echo "amerhwitat")
    fi
    
    # List all images
    log_info "Listing all Docker images..."
    echo ""
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}"
    echo ""
    
    # Find images to push
    log_info "Finding images to push..."
    
    IMAGES_TO_PUSH=(
        "chimera2os:latest"
        "amerhwitat/chimeraiios:iso"
    )
    
    # Filter existing images
    local images_exist=0
    for img in "${IMAGES_TO_PUSH[@]}"; do
        if docker image inspect "$img" &>/dev/null; then
            log_success "Found image: $img"
            images_exist=$((images_exist + 1))
        fi
    done
    
    if [ $images_exist -eq 0 ]; then
        log_error "No Chimera images found to push"
        log_warning "Build the Docker image first:"
        echo "  docker build -f Dockerfile.fixed -t chimera2os:latest ."
        exit 1
    fi
    
    echo ""
    log_info "Preparing images for Docker Hub..."
    
    # Push or tag images
    push_image() {
        local source_image=$1
        local target_repo=$2
        local target_tag=${3:-latest}
        
        log_info "Processing: $source_image"
        
        if [ "$source_image" = "$target_repo:$target_tag" ]; then
            # Already correctly tagged, just push
            log_info "Image already tagged correctly, pushing directly..."
        else
            # Tag the image
            log_info "Tagging: $source_image → $target_repo:$target_tag"
            docker tag "$source_image" "$target_repo:$target_tag"
        fi
        
        # Push to Docker Hub
        log_info "Pushing: $target_repo:$target_tag"
        docker push "$target_repo:$target_tag"
        
        if [ $? -eq 0 ]; then
            log_success "Successfully pushed: $target_repo:$target_tag"
        else
            log_error "Failed to push: $target_repo:$target_tag"
            return 1
        fi
    }
    
    # Push chimera2os:latest
    if docker image inspect "chimera2os:latest" &>/dev/null; then
        log_info ""
        log_info "Pushing chimera2os:latest to Docker Hub..."
        push_image "chimera2os:latest" "$DOCKER_USERNAME/chimera2os" "latest"
    fi
    
    # Push amerhwitat/chimeraiios:iso
    if docker image inspect "amerhwitat/chimeraiios:iso" &>/dev/null; then
        log_info ""
        log_info "Pushing amerhwitat/chimeraiios:iso to Docker Hub..."
        push_image "amerhwitat/chimeraiios:iso" "$DOCKER_USERNAME/chimeraiios" "iso"
    fi
    
    # Create additional tags
    log_info ""
    log_info "Creating additional version tags..."
    
    # Tag as v1.0.0
    docker tag "chimera2os:latest" "$DOCKER_USERNAME/chimera2os:v1.0.0"
    docker push "$DOCKER_USERNAME/chimera2os:v1.0.0"
    log_success "Pushed: $DOCKER_USERNAME/chimera2os:v1.0.0"
    
    # Tag as comprehensive
    docker tag "chimera2os:latest" "$DOCKER_USERNAME/chimera2os:comprehensive"
    docker push "$DOCKER_USERNAME/chimera2os:comprehensive"
    log_success "Pushed: $DOCKER_USERNAME/chimera2os:comprehensive"
    
    print_header "PUSH COMPLETED SUCCESSFULLY"
    
    echo "Your images are now available on Docker Hub:"
    echo ""
    echo "  docker pull $DOCKER_USERNAME/chimera2os:latest"
    echo "  docker pull $DOCKER_USERNAME/chimera2os:v1.0.0"
    echo "  docker pull $DOCKER_USERNAME/chimera2os:comprehensive"
    echo "  docker pull $DOCKER_USERNAME/chimeraiios:iso"
    echo ""
    echo "View on Docker Hub:"
    echo "  https://hub.docker.com/r/$DOCKER_USERNAME/chimera2os"
    echo "  https://hub.docker.com/r/$DOCKER_USERNAME/chimeraiios"
    echo ""
}

# Execute
main
