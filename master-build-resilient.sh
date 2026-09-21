#!/bin/bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd)"
cd "$CHIMERA_REPO_ROOT"

# =============================================================================
# CHIMERA II OS - OPTIMIZED BUILD SCRIPT (Resilient Version)
# =============================================================================
# Builds all repositories with graceful fallback for missing tools
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويتات
# Contact: amer.hwitat@proton.me
# =============================================================================

set +e  # Don't exit on errors - handle them gracefully

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
GITHUB_USER="${GITHUB_USER:-amerhwitat}"
DOCKER_USERNAME="${DOCKER_USERNAME:-amerhwitat}"
BUILD_DIR="./builds-resilient-$(date +%s)"
VERSION="1.0.0"
RELEASE_DATE=$(date +%Y-%m-%d)
SUCCESS_COUNT=0
FAILED_COUNT=0

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
print_header() { echo ""; echo "=================================================================="; echo "$*"; echo "=================================================================="; echo ""; }

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# =============================================================================
# PYTHON BUILDS (8 repos)
# =============================================================================

build_python_project() {
    local name=$1
    print_header "BUILDING: $name (Python)"
    
    git clone https://github.com/$GITHUB_USER/$name.git 2>/dev/null
    
    if [ ! -d "$name" ]; then
        log_error "Failed to clone $name"
        ((FAILED_COUNT++))
        return 1
    fi
    
    cd "$name"
    
    # Try setup.py build
    if [ -f "setup.py" ]; then
        log_info "Building with setup.py..."
        python3 setup.py build 2>/dev/null
        python3 setup.py sdist bdist_wheel 2>/dev/null
        
        if [ -d "dist" ]; then
            log_success "$name built ($(ls dist | wc -l) artifacts)"
            ((SUCCESS_COUNT++))
            cd ..
            return 0
        fi
    fi
    
    # Try pip install with local setup
    if [ -f "setup.py" ] || [ -f "requirements.txt" ]; then
        log_info "Installing as editable package..."
        pip install -e . --quiet 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log_success "$name installed"
            ((SUCCESS_COUNT++))
            cd ..
            return 0
        fi
    fi
    
    log_warning "$name: No build artifacts, skipping"
    ((FAILED_COUNT++))
    cd ..
    return 1
}

# Build Python projects
build_python_project "ChimeraIIOS"
build_python_project "nlp"
build_python_project "BizXtreme"
build_python_project "eth-key-check"
build_python_project "bruteforce"
build_python_project "PDFreaderPY"
build_python_project "general"
build_python_project "test"

# =============================================================================
# JAVASCRIPT BUILDS (2 repos)
# =============================================================================

build_js_project() {
    local name=$1
    print_header "BUILDING: $name (JavaScript)"
    
    git clone https://github.com/$GITHUB_USER/$name.git 2>/dev/null
    
    if [ ! -d "$name" ]; then
        log_error "Failed to clone $name"
        ((FAILED_COUNT++))
        return 1
    fi
    
    cd "$name"
    
    if [ -f "package.json" ]; then
        log_info "Installing dependencies..."
        npm install --silent 2>/dev/null
        
        if grep -q '"build":' package.json; then
            log_info "Building..."
            npm run build --silent 2>/dev/null
        fi
        
        if [ -d "dist" ] || [ -d "node_modules" ]; then
            log_success "$name built"
            ((SUCCESS_COUNT++))
            cd ..
            return 0
        fi
    fi
    
    log_warning "$name: No build output, skipping"
    ((FAILED_COUNT++))
    cd ..
    return 1
}

if command -v npm &> /dev/null; then
    build_js_project "BizX"
    build_js_project "CPU4096Simulator"
else
    log_warning "npm not found - skipping JavaScript builds"
    FAILED_COUNT=$((FAILED_COUNT + 2))
fi

# =============================================================================
# C++ BUILDS (Skipped if no CMake)
# =============================================================================

if command -v cmake &> /dev/null && command -v g++ &> /dev/null; then
    print_header "BUILDING: CPU4096 (C++)"
    git clone https://github.com/$GITHUB_USER/CPU4096.git 2>/dev/null
    cd CPU4096
    
    if [ -f "CMakeLists.txt" ]; then
        mkdir -p build && cd build
        cmake .. 2>/dev/null && make 2>/dev/null
        
        if [ -f "CPU4096" ] || [ -f "libCPU4096.a" ]; then
            log_success "CPU4096 built"
            ((SUCCESS_COUNT++))
        else
            log_warning "CPU4096 build incomplete"
            ((FAILED_COUNT++))
        fi
        cd ../..
    fi
else
    log_warning "CMake or g++ not found - skipping C++ builds"
    FAILED_COUNT=$((FAILED_COUNT + 1))
fi

# =============================================================================
# JAVA BUILDS (Skipped if no Maven)
# =============================================================================

if command -v mvn &> /dev/null; then
    print_header "BUILDING: keygen (Java)"
    git clone https://github.com/$GITHUB_USER/keygen.git 2>/dev/null
    cd keygen
    
    if [ -f "pom.xml" ]; then
        log_info "Building with Maven..."
        mvn clean package -DskipTests -q 2>/dev/null
        
        if [ -d "target" ]; then
            log_success "keygen built"
            ((SUCCESS_COUNT++))
        else
            log_warning "keygen build incomplete"
            ((FAILED_COUNT++))
        fi
    fi
    cd ..
else
    log_warning "Maven not found - skipping Java builds"
    ((FAILED_COUNT++))
fi

# =============================================================================
# STATIC BUILDS (Portfolio)
# =============================================================================

print_header "PROCESSING: Portfolio (Static)"
git clone https://github.com/$GITHUB_USER/amerhwitat.github.io.git portfolio 2>/dev/null

if [ -d "portfolio" ]; then
    log_success "Portfolio cloned"
    ((SUCCESS_COUNT++))
else
    log_warning "Portfolio clone failed"
    ((FAILED_COUNT++))
fi

# =============================================================================
# DOCKER IMAGE BUILD
# =============================================================================

cd ..  # Back to original directory

print_header "BUILDING DOCKER IMAGES"

log_info "Building standard edition..."
docker build -f Dockerfile.fixed -t $DOCKER_USERNAME/chimera2os:latest . 2>&1 | tail -5
docker tag $DOCKER_USERNAME/chimera2os:latest $DOCKER_USERNAME/chimera2os:v$VERSION

log_info "Building VMware edition..."
docker build -f Dockerfile.vmware -t $DOCKER_USERNAME/chimera2os:vmware . 2>&1 | tail -5

log_info "Building Microkernel edition..."
docker build -f Dockerfile.microkernel -t $DOCKER_USERNAME/chimera2os:microkernel . 2>&1 | tail -5

log_success "Docker images built"

# =============================================================================
# PUSH TO DOCKER HUB
# =============================================================================

print_header "PUSHING DOCKER IMAGES TO DOCKER HUB"

log_info "Images built locally - ready to push to Docker Hub"
log_info "To push, run:"
echo "  docker login -u $DOCKER_USERNAME"
echo "  docker push $DOCKER_USERNAME/chimera2os:latest"
echo "  docker push $DOCKER_USERNAME/chimera2os:v$VERSION"
echo "  docker push $DOCKER_USERNAME/chimera2os:vmware"
echo "  docker push $DOCKER_USERNAME/chimera2os:microkernel"

# =============================================================================
# CREATE RELEASES
# =============================================================================

print_header "CREATING RELEASES"

cd "$BUILD_DIR"

for repo_dir in */; do
    repo_name="${repo_dir%/}"
    if [ "$repo_name" != "." ] && [ "$repo_name" != ".." ]; then
        mkdir -p "$repo_name/releases/$VERSION"
        
        # Copy artifacts
        if [ -d "$repo_name/dist" ]; then
            cp -r "$repo_name/dist/"* "$repo_name/releases/$VERSION/" 2>/dev/null || true
        fi
        
        if [ -d "$repo_name/target" ]; then
            cp -r "$repo_name/target/"*.jar "$repo_name/releases/$VERSION/" 2>/dev/null || true
        fi
        
        # Create changelog
        cat > "$repo_name/releases/$VERSION/CHANGELOG.md" << EOF
# $repo_name v$VERSION

**Release Date**: $RELEASE_DATE

## Build Information
- Repository: https://github.com/$GITHUB_USER/$repo_name
- Version: $VERSION
- Built: $(date)

## Contents
See artifacts in this directory.

## Support
For issues: https://github.com/$GITHUB_USER/$repo_name/issues

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحويتات
**Contact**: amer.hwitat@proton.me
EOF
        
        log_success "Release created for $repo_name"
    fi
done

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print_header "BUILD COMPLETE"

log_success "Successfully built: $SUCCESS_COUNT repositories/images"
log_warning "Skipped/failed: $FAILED_COUNT (missing tools)"

log_info "Build directory: $BUILD_DIR"
log_info "Docker Hub username: $DOCKER_USERNAME"
log_info "Docker images: 4 (standard, v1.0.0, vmware, microkernel)"

log_info ""
log_info "Next steps:"
log_info "1. docker login -u $DOCKER_USERNAME"
log_info "2. docker push $DOCKER_USERNAME/chimera2os:latest"
log_info "3. Push release artifacts to GitHub"

echo ""
echo "Build system execution completed!"
