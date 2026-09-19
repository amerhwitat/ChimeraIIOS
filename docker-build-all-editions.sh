#!/bin/bash

# =============================================================================
# CHIMERA II OS - DOCKER IMAGE BUILD & PUSH SCRIPT
# =============================================================================
# Builds all Docker editions and pushes to Docker Hub
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويتات
# Contact: amer.hwitat@proton.me
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-amerhwitat}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
VERSION="1.0.0"
RELEASE_DATE=$(date +%Y-%m-%d)

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
print_header() { echo ""; echo "=================================================================="; echo "$*"; echo "=================================================================="; echo ""; }

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install Docker."
    exit 1
fi

print_header "CHIMERA II OS - DOCKER BUILD & PUSH"

# Get current directory (should have Dockerfiles)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check for Dockerfiles
if [ ! -f "Dockerfile.fixed" ]; then
    log_error "Dockerfile.fixed not found in $SCRIPT_DIR"
    exit 1
fi

# =============================================================================
# BUILD IMAGES
# =============================================================================

log_info "Building standard edition (Dockerfile.fixed)..."
docker build -f Dockerfile.fixed -t $DOCKER_USERNAME/chimera2os:latest \
    --build-arg BUILD_DATE="$RELEASE_DATE" \
    --build-arg VERSION="$VERSION" \
    . 2>&1 | tail -10

docker tag $DOCKER_USERNAME/chimera2os:latest $DOCKER_USERNAME/chimera2os:v$VERSION
log_success "Standard edition built: latest, v$VERSION"

# VMware edition
if [ -f "Dockerfile.vmware" ]; then
    log_info "Building VMware edition (Dockerfile.vmware)..."
    docker build -f Dockerfile.vmware -t $DOCKER_USERNAME/chimera2os:vmware \
        --build-arg BUILD_DATE="$RELEASE_DATE" \
        --build-arg VERSION="$VERSION" \
        . 2>&1 | tail -10
    log_success "VMware edition built: vmware"
fi

# Microkernel edition
if [ -f "Dockerfile.microkernel" ]; then
    log_info "Building Microkernel edition (Dockerfile.microkernel)..."
    docker build -f Dockerfile.microkernel -t $DOCKER_USERNAME/chimera2os:microkernel \
        --build-arg BUILD_DATE="$RELEASE_DATE" \
        --build-arg VERSION="$VERSION" \
        . 2>&1 | tail -10
    log_success "Microkernel edition built: microkernel"
fi

# Mobile edition (ARM64)
if [ -f "Dockerfile.mobile" ]; then
    log_info "Building Mobile edition (Dockerfile.mobile, ARM64)..."
    
    if command -v docker buildx &> /dev/null; then
        docker buildx build --platform linux/arm64 \
            -f Dockerfile.mobile \
            -t $DOCKER_USERNAME/chimera2os:mobile \
            --build-arg BUILD_DATE="$RELEASE_DATE" \
            --build-arg VERSION="$VERSION" \
            . 2>&1 | tail -10
        log_success "Mobile edition built: mobile (ARM64)"
    else
        log_info "docker buildx not available - building for native platform"
        docker build -f Dockerfile.mobile -t $DOCKER_USERNAME/chimera2os:mobile \
            --build-arg BUILD_DATE="$RELEASE_DATE" \
            --build-arg VERSION="$VERSION" \
            . 2>&1 | tail -10
        log_success "Mobile edition built: mobile"
    fi
fi

# =============================================================================
# DISPLAY IMAGES
# =============================================================================

print_header "DOCKER IMAGES CREATED"

docker images | grep "chimera2os"

# =============================================================================
# PUSH TO DOCKER HUB
# =============================================================================

print_header "DOCKER HUB PUSH"

log_info "To push to Docker Hub, run:"
echo ""
echo "  # 1. Login (if not already logged in)"
echo "  docker login -u $DOCKER_USERNAME"
echo ""
echo "  # 2. Push standard edition"
echo "  docker push $DOCKER_USERNAME/chimera2os:latest"
echo "  docker push $DOCKER_USERNAME/chimera2os:v$VERSION"
echo ""
echo "  # 3. Push VMware edition"
echo "  docker push $DOCKER_USERNAME/chimera2os:vmware"
echo ""
echo "  # 4. Push Microkernel edition"
echo "  docker push $DOCKER_USERNAME/chimera2os:microkernel"
echo ""
echo "  # 5. Push Mobile edition (if built)"
echo "  docker push $DOCKER_USERNAME/chimera2os:mobile"
echo ""
echo "  # Or push all at once:"
echo "  docker push $DOCKER_USERNAME/chimera2os:latest && \\"
echo "  docker push $DOCKER_USERNAME/chimera2os:v$VERSION && \\"
echo "  docker push $DOCKER_USERNAME/chimera2os:vmware && \\"
echo "  docker push $DOCKER_USERNAME/chimera2os:microkernel"
echo ""

# Try to push if already logged in
if docker info 2>/dev/null | grep -q "Username"; then
    print_header "PUSHING TO DOCKER HUB"
    
    log_info "Pushing latest..."
    docker push $DOCKER_USERNAME/chimera2os:latest 2>&1 | tail -5
    
    log_info "Pushing v$VERSION..."
    docker push $DOCKER_USERNAME/chimera2os:v$VERSION 2>&1 | tail -5
    
    if docker images | grep -q "chimera2os.*vmware"; then
        log_info "Pushing vmware..."
        docker push $DOCKER_USERNAME/chimera2os:vmware 2>&1 | tail -5
    fi
    
    if docker images | grep -q "chimera2os.*microkernel"; then
        log_info "Pushing microkernel..."
        docker push $DOCKER_USERNAME/chimera2os:microkernel 2>&1 | tail -5
    fi
    
    if docker images | grep -q "chimera2os.*mobile"; then
        log_info "Pushing mobile..."
        docker push $DOCKER_USERNAME/chimera2os:mobile 2>&1 | tail -5
    fi
    
    log_success "All images pushed to Docker Hub!"
else
    log_info "Not currently logged in to Docker Hub"
    log_info "Run 'docker login -u $DOCKER_USERNAME' first, then push manually"
fi

print_header "BUILD & PUSH COMPLETE"

log_success "Docker build complete!"
log_info "Docker Hub: https://hub.docker.com/r/$DOCKER_USERNAME/chimera2os"
log_info "All images are ready for use."
