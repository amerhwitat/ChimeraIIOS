#!/bin/bash

# =============================================================================
# GITHUB TO DOCKER HUB - COMPLETE REPOSITORY BUILDER
# =============================================================================
# Discovers all GitHub repositories, builds Docker images, pushes to Docker Hub
# Handles: Web apps, Mobile apps, Libraries, APIs, Tools, Utilities
#
# Usage: bash build-all-github-repos.sh [github-user] [docker-user] [github-token]
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
GITHUB_USER="${1:-amerhwitat}"
DOCKER_USER="${2:-amerhwitat}"
GITHUB_TOKEN="${3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(pwd)/docker-hub-build"
REPOS_DIR="${BUILD_DIR}/repos"
OUTPUT_DIR="${BUILD_DIR}/output"
BUILD_LOG="${BUILD_DIR}/build-all-repos.log"
REPORT_FILE="${BUILD_DIR}/DOCKER_HUB_BUILD_REPORT.txt"
REGISTRY_INDEX="${BUILD_DIR}/DOCKER_HUB_REGISTRY_INDEX.md"

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$BUILD_LOG"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*" | tee -a "$BUILD_LOG"; }
log_error() { echo -e "${RED}[✗]${NC} $*" | tee -a "$BUILD_LOG"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $*" | tee -a "$BUILD_LOG"; }
log_build() { echo -e "${CYAN}[BUILD]${NC} $*" | tee -a "$BUILD_LOG"; }

print_banner() {
    echo ""
    echo -e "${MAGENTA}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     GITHUB → DOCKER HUB - COMPLETE REPOSITORY BUILDER         ║"
    echo "║                                                                ║"
    echo "║  Auto-discover repos, build images, push to Docker Hub        ║"
    echo "║  Created by Amer Abdullah Suleiman Hwitat - عامر الحويطات  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# =============================================================================
# STEP 1: INITIALIZE
# =============================================================================

initialize() {
    print_banner
    
    mkdir -p "$REPOS_DIR" "$OUTPUT_DIR"
    : > "$BUILD_LOG"
    
    echo "GitHub to Docker Hub Build System" > "$BUILD_LOG"
    echo "Started: $(date)" >> "$BUILD_LOG"
    
    log_success "Build system initialized"
    log_info "GitHub user: $GITHUB_USER"
    log_info "Docker Hub user: $DOCKER_USER"
    log_info "Build directory: $BUILD_DIR"
    
    # Check prerequisites
    command -v docker >/dev/null || { log_error "Docker not found"; exit 1; }
    log_success "Docker: $(docker --version)"
    
    command -v git >/dev/null || { log_error "Git not found"; exit 1; }
    log_success "Git: $(git --version | head -1)"
    
    command -v curl >/dev/null || { log_error "curl not found"; exit 1; }
    log_success "curl available"
}

# =============================================================================
# STEP 2: DISCOVER ALL GITHUB REPOSITORIES
# =============================================================================

discover_repositories() {
    log_info "Discovering all GitHub repositories for user: $GITHUB_USER"
    
    local page=1
    local per_page=100
    local repos_file="${BUILD_DIR}/discovered_repos.txt"
    : > "$repos_file"
    
    local total_discovered=0
    
    while true; do
        log_info "Fetching page $page of repositories..."
        
        local url="https://api.github.com/users/${GITHUB_USER}/repos?page=${page}&per_page=${per_page}&sort=updated"
        
        if [ -n "$GITHUB_TOKEN" ]; then
            url="${url}&access_token=${GITHUB_TOKEN}"
        fi
        
        local response=$(curl -s "$url")
        
        # Check if response is empty
        if echo "$response" | grep -q "\[\]"; then
            break
        fi
        
        # Extract repository names
        local repos=$(echo "$response" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
        
        if [ -z "$repos" ]; then
            break
        fi
        
        while IFS= read -r repo; do
            echo "$repo" >> "$repos_file"
            ((total_discovered++))
        done <<< "$repos"
        
        ((page++))
    done
    
    log_success "Discovered $total_discovered repositories"
    
    # Display discovered repos
    log_info "Repositories found:"
    cat "$repos_file" | nl | head -20
    if [ $total_discovered -gt 20 ]; then
        log_info "... and $((total_discovered - 20)) more repositories"
    fi
    
    echo "$total_discovered"
}

# =============================================================================
# STEP 3: DETECT APPLICATION TYPE
# =============================================================================

detect_app_type() {
    local repo_path="$1"
    local app_type=""
    local framework=""
    local language=""
    
    # Check for Node.js
    if [ -f "$repo_path/package.json" ]; then
        language="Node.js"
        if grep -q '"next"' "$repo_path/package.json"; then
            framework="Next.js"
            app_type="web-nextjs"
        elif grep -q '"react"' "$repo_path/package.json"; then
            framework="React"
            app_type="web-react"
        elif grep -q '"vue"' "$repo_path/package.json"; then
            framework="Vue.js"
            app_type="web-vue"
        elif grep -q '"express"' "$repo_path/package.json"; then
            framework="Express"
            app_type="api-express"
        elif grep -q '"nuxt"' "$repo_path/package.json"; then
            framework="Nuxt"
            app_type="web-nuxt"
        else
            app_type="app-nodejs"
        fi
    fi
    
    # Check for Python
    if [ -f "$repo_path/requirements.txt" ] || [ -f "$repo_path/pyproject.toml" ] || [ -f "$repo_path/setup.py" ]; then
        language="Python"
        if grep -q -r "flask" "$repo_path" 2>/dev/null; then
            framework="Flask"
            app_type="api-flask"
        elif grep -q -r "django" "$repo_path" 2>/dev/null; then
            framework="Django"
            app_type="web-django"
        elif grep -q -r "fastapi" "$repo_path" 2>/dev/null; then
            framework="FastAPI"
            app_type="api-fastapi"
        else
            app_type="app-python"
        fi
    fi
    
    # Check for Go
    if [ -f "$repo_path/go.mod" ] || [ -f "$repo_path/main.go" ]; then
        language="Go"
        app_type="app-go"
    fi
    
    # Check for Java
    if [ -f "$repo_path/pom.xml" ] || [ -f "$repo_path/build.gradle" ]; then
        language="Java"
        if grep -q "spring" "$repo_path/pom.xml" 2>/dev/null; then
            framework="Spring Boot"
        fi
        app_type="app-java"
    fi
    
    # Check for mobile (React Native, Flutter)
    if [ -f "$repo_path/app.json" ] && [ -f "$repo_path/package.json" ]; then
        app_type="mobile-react-native"
        language="React Native"
    fi
    
    if [ -f "$repo_path/pubspec.yaml" ]; then
        app_type="mobile-flutter"
        language="Flutter"
    fi
    
    # Check for static site/documentation
    if [ -f "$repo_path/index.html" ] && [ -f "$repo_path/package.json" ]; then
        app_type="web-static"
        language="HTML/CSS/JS"
    fi
    
    # Check for Dockerfile (already containerized)
    if [ -f "$repo_path/Dockerfile" ]; then
        app_type="app-pre-dockerized"
    fi
    
    # Default
    if [ -z "$app_type" ]; then
        app_type="app-generic"
        language="Unknown"
    fi
    
    echo "${app_type}|${language}|${framework}"
}

# =============================================================================
# STEP 4: GENERATE DOCKERFILE
# =============================================================================

generate_dockerfile() {
    local repo_path="$1"
    local app_type="$2"
    local repo_name="$3"
    
    local dockerfile_path="${repo_path}/Dockerfile"
    
    # Skip if Dockerfile already exists
    if [ -f "$dockerfile_path" ]; then
        return 0
    fi
    
    log_info "Generating Dockerfile for $repo_name ($app_type)"
    
    case "$app_type" in
        web-nextjs)
            cat > "$dockerfile_path" << 'EOF'
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime stage
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]
EOF
            ;;
        web-react)
            cat > "$dockerfile_path" << 'EOF'
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
            ;;
        api-express)
            cat > "$dockerfile_path" << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
EOF
            ;;
        api-flask)
            cat > "$dockerfile_path" << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
EOF
            ;;
        api-fastapi)
            cat > "$dockerfile_path" << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
EOF
            ;;
        web-django)
            cat > "$dockerfile_path" << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi"]
EOF
            ;;
        mobile-react-native)
            cat > "$dockerfile_path" << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 8081
CMD ["npm", "start"]
EOF
            ;;
        mobile-flutter)
            cat > "$dockerfile_path" << 'EOF'
FROM ghcr.io/cirruslabs/flutter:latest
WORKDIR /app
COPY . .
RUN flutter pub get
RUN flutter build web
EXPOSE 5000
CMD ["flutter", "run", "-d", "web-server", "--web-port=5000"]
EOF
            ;;
        app-go)
            cat > "$dockerfile_path" << 'EOF'
# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o app .

# Runtime stage
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/app .
EXPOSE 8080
CMD ["./app"]
EOF
            ;;
        app-python)
            cat > "$dockerfile_path" << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt . 2>/dev/null || echo ""
RUN [ -f requirements.txt ] && pip install --no-cache-dir -r requirements.txt || true
COPY . .
CMD ["python", "main.py"]
EOF
            ;;
        *)
            cat > "$dockerfile_path" << 'EOF'
FROM ubuntu:24.04
LABEL maintainer="amerhwitat"
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y build-essential git curl
CMD ["/bin/bash"]
EOF
            ;;
    esac
    
    log_success "Generated Dockerfile for $repo_name"
}

# =============================================================================
# STEP 5: CLONE REPOSITORIES
# =============================================================================

clone_repositories() {
    local repos_file="${BUILD_DIR}/discovered_repos.txt"
    local repo_count=0
    local total_repos=$(wc -l < "$repos_file")
    
    log_info "Cloning all repositories..."
    
    while IFS= read -r repo_name; do
        ((repo_count++))
        
        log_info "[$repo_count/$total_repos] Cloning: $repo_name"
        
        local repo_url="https://github.com/${GITHUB_USER}/${repo_name}.git"
        local repo_path="${REPOS_DIR}/${repo_name}"
        
        if [ -d "$repo_path" ]; then
            log_info "Repository already exists, updating..."
            cd "$repo_path"
            git pull origin main 2>&1 | tail -1 >> "$BUILD_LOG" || git pull origin master 2>&1 | tail -1 >> "$BUILD_LOG" || true
        else
            if git clone "$repo_url" "$repo_path" 2>&1 | tail -1 >> "$BUILD_LOG"; then
                log_success "Cloned: $repo_name"
            else
                log_warning "Failed to clone: $repo_name"
                continue
            fi
        fi
    done < "$repos_file"
}

# =============================================================================
# STEP 6: BUILD DOCKER IMAGES
# =============================================================================

build_docker_images() {
    local repos_file="${BUILD_DIR}/discovered_repos.txt"
    local repo_count=0
    local total_repos=$(wc -l < "$repos_file")
    local successful=0
    local failed=0
    local images_file="${BUILD_DIR}/built_images.txt"
    : > "$images_file"
    
    log_build "Building Docker images..."
    
    while IFS= read -r repo_name; do
        ((repo_count++))
        
        local repo_path="${REPOS_DIR}/${repo_name}"
        [ -d "$repo_path" ] || continue
        
        log_build "[$repo_count/$total_repos] Building: $repo_name"
        
        cd "$repo_path"
        
        # Detect app type
        local app_info=$(detect_app_type "$repo_path")
        local app_type=$(echo "$app_info" | cut -d'|' -f1)
        local language=$(echo "$app_info" | cut -d'|' -f2)
        
        # Generate Dockerfile if needed
        generate_dockerfile "$repo_path" "$app_type" "$repo_name"
        
        # Build image
        local image_name="${DOCKER_USER}/${repo_name,,}"
        
        docker rmi "${image_name}:latest" 2>/dev/null || true
        
        if docker build \
            -t "${image_name}:latest" \
            --label "maintainer=$GITHUB_USER" \
            --label "description=$repo_name" \
            --label "app_type=$app_type" \
            --label "language=$language" \
            --label "source=https://github.com/${GITHUB_USER}/${repo_name}" \
            . 2>&1 | tail -5 >> "$BUILD_LOG"; then
            
            # Tag versions
            docker tag "${image_name}:latest" "${image_name}:v1.0.0"
            docker tag "${image_name}:latest" "${image_name}:stable"
            
            log_success "Built: $repo_name [$repo_count/$total_repos]"
            
            echo "${image_name}|${app_type}|${language}" >> "$images_file"
            ((successful++))
        else
            log_error "Failed to build: $repo_name"
            ((failed++))
        fi
    done < "$repos_file"
    
    log_build "Build complete: $successful successful, $failed failed"
}

# =============================================================================
# STEP 7: PUSH IMAGES TO DOCKER HUB
# =============================================================================

push_images_to_hub() {
    local images_file="${BUILD_DIR}/built_images.txt"
    
    if [ ! -f "$images_file" ]; then
        log_warning "No images to push"
        return
    fi
    
    log_build "Pushing images to Docker Hub..."
    
    # Login
    docker login -u "$DOCKER_USER" || { log_warning "Docker Hub login skipped"; return; }
    
    local total_images=$(wc -l < "$images_file")
    local current=0
    local successful=0
    
    while IFS='|' read -r image_name app_type language; do
        ((current++))
        
        log_build "[$current/$total_images] Pushing: $image_name"
        
        for tag in latest v1.0.0 stable; do
            if docker push "${image_name}:${tag}" 2>&1 | tail -1 | tee -a "$BUILD_LOG"; then
                ((successful++))
            fi
            sleep 1
        done
    done < "$images_file"
    
    log_success "Push complete: $successful tags pushed"
}

# =============================================================================
# STEP 8: GENERATE REGISTRY DOCUMENTATION
# =============================================================================

generate_registry_docs() {
    local images_file="${BUILD_DIR}/built_images.txt"
    
    if [ ! -f "$images_file" ]; then
        return
    fi
    
    log_info "Generating Docker Hub registry documentation..."
    
    cat > "$REGISTRY_INDEX" << 'EOF'
# Docker Hub Registry Index

Complete list of all Docker images built from GitHub repositories.

**Registry**: https://hub.docker.com/u/amerhwitat

## Quick Links

### Web Applications
EOF
    
    grep "web-" "$images_file" | while IFS='|' read -r image_name app_type language; do
        echo "- [\`${image_name##*/}\`](https://hub.docker.com/r/${image_name})" >> "$REGISTRY_INDEX"
    done
    
    cat >> "$REGISTRY_INDEX" << 'EOF'

### Mobile Applications
EOF
    
    grep "mobile-" "$images_file" | while IFS='|' read -r image_name app_type language; do
        echo "- [\`${image_name##*/}\`](https://hub.docker.com/r/${image_name})" >> "$REGISTRY_INDEX"
    done
    
    cat >> "$REGISTRY_INDEX" << 'EOF'

### APIs & Services
EOF
    
    grep "api-" "$images_file" | while IFS='|' read -r image_name app_type language; do
        echo "- [\`${image_name##*/}\`](https://hub.docker.com/r/${image_name})" >> "$REGISTRY_INDEX"
    done
    
    cat >> "$REGISTRY_INDEX" << 'EOF'

### Applications & Libraries
EOF
    
    grep "app-" "$images_file" | while IFS='|' read -r image_name app_type language; do
        echo "- [\`${image_name##*/}\`](https://hub.docker.com/r/${image_name})" >> "$REGISTRY_INDEX"
    done
    
    cat >> "$REGISTRY_INDEX" << 'EOF'

## Full Image List

| Repository | Type | Language | Docker Image | Tags |
|------------|------|----------|--------------|------|
EOF
    
    while IFS='|' read -r image_name app_type language; do
        local repo_name="${image_name##*/}"
        echo "| [$repo_name](https://github.com/amerhwitat/$repo_name) | $app_type | $language | [\`${image_name}\`](https://hub.docker.com/r/${image_name}) | latest, v1.0.0, stable |" >> "$REGISTRY_INDEX"
    done < "$images_file"
    
    log_success "Registry documentation generated: $REGISTRY_INDEX"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    initialize
    
    local total_repos=$(discover_repositories)
    [ "$total_repos" -gt 0 ] || { log_error "No repositories found"; exit 1; }
    
    clone_repositories
    build_docker_images
    push_images_to_hub
    generate_registry_docs
    
    echo ""
    log_success "ALL REPOSITORIES BUILT AND PUSHED!"
    log_info "Docker Hub: https://hub.docker.com/u/$DOCKER_USER"
    log_info "Registry Index: $REGISTRY_INDEX"
}

main "$@"
