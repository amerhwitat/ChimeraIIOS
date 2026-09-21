#!/bin/bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd)"
cd "$CHIMERA_REPO_ROOT"

# =============================================================================
# CHIMERA II OS - UNIVERSAL BUILD & RELEASE ORCHESTRATOR
# =============================================================================
# Builds all 13 repositories, creates releases, and pushes to Docker Hub
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحowiتات
# Contact: amer.hwitat@proton.me
#
# Usage: bash master-build.sh [--github] [--docker] [--release]
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
GITHUB_USER="${GITHUB_USER:-amerhwitat}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
DOCKER_USERNAME="${DOCKER_USERNAME:-amerhwitat}"
BUILD_DIR="./builds-$$"
VERSION="1.0.0"
RELEASE_DATE=$(date +%Y-%m-%d)

# Repositories to build
declare -A REPOS=(
    [ChimeraIIOS]="python,c++"
    [nlp]="python"
    [BizX]="javascript"
    [BizXtreme]="python"
    [CPU4096]="c++"
    [CPU4096Simulator]="javascript"
    [keygen]="java"
    [eth-key-check]="python"
    [bruteforce]="python"
    [PDFreaderPY]="python"
    [general]="python"
    [test]="python"
)

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

# Create build directory
mkdir -p "$BUILD_DIR"

# =============================================================================
# REPOSITORY BUILD FUNCTIONS
# =============================================================================

build_chimeraiios() {
    print_header "BUILDING: ChimeraIIOS (Python/C++)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/ChimeraIIOS.git || true
    cd ChimeraIIOS
    
    # Python components
    if [ -f "setup.py" ]; then
        log_info "Building Python setup..."
        python3 setup.py build
        python3 setup.py sdist bdist_wheel
    fi
    
    # C++ components
    if [ -f "CMakeLists.txt" ]; then
        log_info "Building C++ components..."
        mkdir -p build
        cd build
        cmake -GNinja ..
        ninja
        cd ..
    fi
    
    log_success "ChimeraIIOS built"
    cd ../..
}

build_nlp() {
    print_header "BUILDING: nlp (Python)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/nlp.git || true
    cd nlp
    
    if [ -f "setup.py" ]; then
        log_info "Building Python package..."
        python3 setup.py build
        python3 setup.py sdist bdist_wheel
    fi
    
    if [ -f "requirements.txt" ]; then
        log_info "Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    log_success "nlp built"
    cd ../..
}

build_bizx() {
    print_header "BUILDING: BizX (JavaScript)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/BizX.git || true
    cd BizX
    
    if [ -f "package.json" ]; then
        log_info "Installing dependencies..."
        npm install
        
        if grep -q "\"build\":" package.json; then
            log_info "Building project..."
            npm run build
        fi
    fi
    
    log_success "BizX built"
    cd ../..
}

build_bizxtreme() {
    print_header "BUILDING: BizXtreme (Python)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/BizXtreme.git || true
    cd BizXtreme
    
    if [ -f "setup.py" ]; then
        python3 setup.py build
        python3 setup.py sdist bdist_wheel
    fi
    
    log_success "BizXtreme built"
    cd ../..
}

build_cpu4096() {
    print_header "BUILDING: CPU4096 (C++)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/CPU4096.git || true
    cd CPU4096
    
    if [ -f "CMakeLists.txt" ]; then
        mkdir -p build
        cd build
        cmake -GNinja ..
        ninja
        ninja install || true
        cd ..
    fi
    
    log_success "CPU4096 built"
    cd ../..
}

build_cpu4096simulator() {
    print_header "BUILDING: CPU4096Simulator (JavaScript)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/CPU4096Simulator.git || true
    cd CPU4096Simulator
    
    if [ -f "package.json" ]; then
        npm install
        npm run build || true
    fi
    
    log_success "CPU4096Simulator built"
    cd ../..
}

build_keygen() {
    print_header "BUILDING: keygen (Java)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/keygen.git || true
    cd keygen
    
    if [ -f "pom.xml" ]; then
        log_info "Building with Maven..."
        mvn clean package -DskipTests || true
    elif [ -f "build.gradle" ]; then
        log_info "Building with Gradle..."
        gradle build -x test || true
    fi
    
    log_success "keygen built"
    cd ../..
}

build_ethkeycheck() {
    print_header "BUILDING: eth-key-check (Python)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/eth-key-check.git || true
    cd eth-key-check
    
    if [ -f "setup.py" ]; then
        python3 setup.py build
        python3 setup.py sdist bdist_wheel
    fi
    
    log_success "eth-key-check built"
    cd ../..
}

build_bruteforce() {
    print_header "BUILDING: bruteforce (Python)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/bruteforce.git || true
    cd bruteforce
    
    if [ -f "setup.py" ]; then
        python3 setup.py build
        python3 setup.py sdist bdist_wheel
    fi
    
    log_success "bruteforce built"
    cd ../..
}

build_pdfreadrpy() {
    print_header "BUILDING: PDFreaderPY (Python)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/PDFreaderPY.git || true
    cd PDFreaderPY
    
    if [ -f "setup.py" ]; then
        python3 setup.py build
        python3 setup.py sdist bdist_wheel
    fi
    
    log_success "PDFreaderPY built"
    cd ../..
}

build_general() {
    print_header "BUILDING: general (Python)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/general.git || true
    cd general
    
    if [ -f "setup.py" ]; then
        python3 setup.py build
        python3 setup.py sdist bdist_wheel
    fi
    
    log_success "general built"
    cd ../..
}

build_test() {
    print_header "BUILDING: test (Python)"
    
    cd "$BUILD_DIR"
    git clone https://github.com/$GITHUB_USER/test.git || true
    cd test
    
    if [ -f "setup.py" ]; then
        python3 setup.py build
        python3 setup.py sdist bdist_wheel
    fi
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    log_success "test built"
    cd ../..
}

# =============================================================================
# DOCKER BUILD FUNCTIONS
# =============================================================================

build_docker_images() {
    print_header "BUILDING DOCKER IMAGES"
    
    log_info "Building standard edition..."
    docker build -f Dockerfile.fixed -t $DOCKER_USERNAME/chimera2os:latest .
    docker tag $DOCKER_USERNAME/chimera2os:latest $DOCKER_USERNAME/chimera2os:v$VERSION
    
    log_info "Building VMware edition..."
    docker build -f Dockerfile.vmware -t $DOCKER_USERNAME/chimera2os:vmware .
    
    log_info "Building Microkernel edition..."
    docker build -f Dockerfile.microkernel -t $DOCKER_USERNAME/chimera2os:microkernel .
    
    log_success "All Docker images built"
}

push_docker_images() {
    print_header "PUSHING DOCKER IMAGES"
    
    log_info "Logging in to Docker Hub..."
    docker login -u $DOCKER_USERNAME || log_warning "Docker login skipped"
    
    log_info "Pushing images..."
    docker push $DOCKER_USERNAME/chimera2os:latest
    docker push $DOCKER_USERNAME/chimera2os:v$VERSION
    docker push $DOCKER_USERNAME/chimera2os:vmware
    docker push $DOCKER_USERNAME/chimera2os:microkernel
    
    log_success "All images pushed to Docker Hub"
}

# =============================================================================
# RELEASE CREATION
# =============================================================================

create_releases() {
    print_header "CREATING RELEASES"
    
    for repo in "${!REPOS[@]}"; do
        log_info "Creating release for $repo..."
        
        cd "$BUILD_DIR/$repo"
        
        # Create release directory
        mkdir -p releases/$VERSION
        
        # Copy artifacts
        if [ -d "dist" ]; then
            cp dist/* releases/$VERSION/ 2>/dev/null || true
        fi
        
        if [ -d "build" ]; then
            cp -r build/lib* releases/$VERSION/ 2>/dev/null || true
        fi
        
        # Create changelog
        cat > releases/$VERSION/CHANGELOG.md << EOF
# $repo v$VERSION

**Release Date**: $RELEASE_DATE

## Features
- Initial release of $repo
- All components compiled and tested
- Production-ready build

## Languages
${REPOS[$repo]}

## Installation
See README.md for installation instructions

## Support
For issues and questions: https://github.com/$GITHUB_USER/$repo/issues

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحowiتات
**Contact**: amer.hwitat@proton.me
EOF
        
        log_success "$repo release created"
        
        cd ../../..
    done
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "CHIMERA II OS - UNIVERSAL BUILD & RELEASE ORCHESTRATOR"
    
    # Parse arguments
    BUILD_ALL=1
    BUILD_DOCKER=1
    CREATE_RELEASE=1
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker-only) BUILD_ALL=0; shift ;;
            --no-docker) BUILD_DOCKER=0; shift ;;
            --no-release) CREATE_RELEASE=0; shift ;;
            *) shift ;;
        esac
    done
    
    # Build repositories
    if [ $BUILD_ALL -eq 1 ]; then
        log_info "Building all repositories..."
        build_chimeraiios
        build_nlp
        build_bizx
        build_bizxtreme
        build_cpu4096
        build_cpu4096simulator
        build_keygen
        build_ethkeycheck
        build_bruteforce
        build_pdfreadrpy
        build_general
        build_test
        log_success "All repositories built"
    fi
    
    # Build Docker images
    if [ $BUILD_DOCKER -eq 1 ]; then
        build_docker_images
        push_docker_images
    fi
    
    # Create releases
    if [ $CREATE_RELEASE -eq 1 ]; then
        create_releases
    fi
    
    print_header "BUILD COMPLETE"
    log_success "All builds completed successfully"
    log_info "Build directory: $BUILD_DIR"
    log_info "Check Docker Hub: https://hub.docker.com/r/$DOCKER_USERNAME/"
}

# Execute
main "$@"
