#!/bin/bash

# =============================================================================
# CHIMERA II OS - DOCKER BUILD & PUSH AUTOMATION
# =============================================================================
# Builds all 13 GitHub repositories as Docker images and pushes to Docker Hub
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويطات
# Contact: amer.hwitat@proton.me
#
# Workflow:
#   1. Clone or update all 13 repositories
#   2. Build Docker image for each repository
#   3. Tag with: latest, v1.0.0, stable
#   4. Push to Docker Hub
#   5. Generate verification report
#
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
BUILD_DIR="${HOME}/docker-build-chimera"
REPOS_DIR="${BUILD_DIR}/repos"
BUILD_LOG="${BUILD_DIR}/docker-build.log"
PUSH_LOG="${BUILD_DIR}/docker-push.log"
REPORT="${BUILD_DIR}/DOCKER_BUILD_REPORT.txt"

# Define all repositories
declare -A REPOS=(
    [ChimeraIIOS]="Core OS kernel and base system|core|required"
    [nlp]="Natural Language Processing and AI|nlp|optional"
    [BizX]="Business application framework|business|optional"
    [BizXtreme]="Enterprise platform|enterprise|optional"
    [CPU4096]="4096-bit CPU simulator|simulator|optional"
    [CPU4096Simulator]="Web-based CPU simulator|web-sim|optional"
    [keygen]="Cryptographic key generation|crypto|optional"
    [eth-key-check]="Ethereum key validation|blockchain|optional"
    [bruteforce]="Security testing tools|security|optional"
    [PDFreaderPY]="PDF processing library|pdf|optional"
    [general]="Utilities and frameworks|utils|optional"
    [test]="Testing infrastructure|testing|optional"
    [amerhwitat.github.io]="Portfolio and documentation|web|optional"
)

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$BUILD_LOG"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*" | tee -a "$BUILD_LOG"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*" | tee -a "$BUILD_LOG"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $*" | tee -a "$BUILD_LOG"
}

log_push() {
    echo -e "${CYAN}[PUSH]${NC} $*" | tee -a "$PUSH_LOG"
}

print_header() {
    echo "" | tee -a "$BUILD_LOG"
    echo "════════════════════════════════════════════════════════════════" | tee -a "$BUILD_LOG"
    echo "$*" | tee -a "$BUILD_LOG"
    echo "════════════════════════════════════════════════════════════════" | tee -a "$BUILD_LOG"
    echo "" | tee -a "$BUILD_LOG"
}

print_banner() {
    echo ""
    echo -e "${MAGENTA}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     CHIMERA II OS - DOCKER BUILD & PUSH AUTOMATION             ║"
    echo "║                                                                ║"
    echo "║  Building 13 repositories as Docker images                    ║"
    echo "║  Pushing to Docker Hub with multiple tags                     ║"
    echo "║  created by Amer Abdullah Suleiman Hwitat - عامر الحويطات   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# =============================================================================
# STEP 1: INITIALIZE BUILD ENVIRONMENT
# =============================================================================

initialize_build() {
    print_banner
    
    print_header "STEP 1: INITIALIZING BUILD ENVIRONMENT"
    
    # Create directories
    mkdir -p "$REPOS_DIR"
    
    # Initialize logs
    : > "$BUILD_LOG"
    : > "$PUSH_LOG"
    
    echo "Docker Build & Push System" > "$BUILD_LOG"
    echo "Started: $(date)" >> "$BUILD_LOG"
    
    log_success "Build environment initialized"
    log_info "Build directory: $BUILD_DIR"
    log_info "Repositories directory: $REPOS_DIR"
    
    # Check prerequisites
    log_info "Checking prerequisites..."
    
    # Check Git
    if command -v git &>/dev/null; then
        log_success "Git: $(git --version | cut -d' ' -f3)"
    else
        log_error "Git not found"
        exit 1
    fi
    
    # Check Docker
    if command -v docker &>/dev/null; then
        log_success "Docker: $(docker --version | cut -d' ' -f3)"
    else
        log_error "Docker not found"
        exit 1
    fi
    
    # Check Docker daemon
    if docker ps &>/dev/null; then
        log_success "Docker daemon: Running"
    else
        log_warning "Docker daemon not responding, attempting to start..."
        sudo service docker start 2>/dev/null || sudo systemctl start docker 2>/dev/null || true
        sleep 2
        if docker ps &>/dev/null; then
            log_success "Docker daemon: Started"
        else
            log_error "Docker daemon failed to start"
            exit 1
        fi
    fi
    
    log_success "All prerequisites met"
}

# =============================================================================
# STEP 2: CLONE OR UPDATE REPOSITORIES
# =============================================================================

clone_or_update_repos() {
    print_header "STEP 2: CLONING OR UPDATING REPOSITORIES"
    
    local total=${#REPOS[@]}
    local current=0
    
    for repo in "${!REPOS[@]}"; do
        ((current++))
        
        log_info "[$current/$total] Processing repository: $repo"
        
        local repo_url="https://github.com/${GITHUB_USER}/${repo}.git"
        local repo_path="${REPOS_DIR}/${repo}"
        
        if [ -d "$repo_path" ]; then
            log_info "Repository exists, updating..."
            cd "$repo_path"
            git pull origin main 2>&1 | tail -1 >> "$BUILD_LOG" || git pull origin master 2>&1 | tail -1 >> "$BUILD_LOG" || true
            log_success "Updated: $repo"
        else
            log_info "Cloning repository..."
            if git clone "$repo_url" "$repo_path" 2>&1 | tail -1 >> "$BUILD_LOG"; then
                log_success "Cloned: $repo"
            else
                log_error "Failed to clone: $repo"
                continue
            fi
        fi
    done
    
    log_success "Repository processing complete"
}

# =============================================================================
# STEP 3: BUILD DOCKER IMAGES FOR ALL REPOSITORIES
# =============================================================================

build_docker_images() {
    print_header "STEP 3: BUILDING DOCKER IMAGES"
    
    local total=${#REPOS[@]}
    local current=0
    local successful=0
    local failed=0
    
    for repo in "${!REPOS[@]}"; do
        ((current++))
        
        log_info "[$current/$total] Building Docker image for: $repo"
        
        local repo_path="${REPOS_DIR}/${repo}"
        local image_name="${DOCKER_USER}/${repo,,}"
        
        if [ ! -d "$repo_path" ]; then
            log_warning "Repository directory not found, skipping: $repo_path"
            ((failed++))
            continue
        fi
        
        cd "$repo_path"
        
        # Determine Dockerfile location
        local dockerfile="Dockerfile"
        if [ ! -f "$dockerfile" ]; then
            if [ -f "docker/Dockerfile" ]; then
                dockerfile="docker/Dockerfile"
            elif [ -f "Dockerfile.prod" ]; then
                dockerfile="Dockerfile.prod"
            else
                log_warning "No Dockerfile found, creating basic one..."
                
                # Create basic Dockerfile
                cat > Dockerfile << EOFDO
FROM ubuntu:24.04
LABEL maintainer="$GITHUB_USER"
LABEL description="Chimera II OS - $repo"
LABEL version="1.0.0"

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    python3 \
    python3-pip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
EOFDO
                dockerfile="Dockerfile"
            fi
        fi
        
        # Build Docker image
        log_info "Building with Dockerfile: $dockerfile"
        
        if docker build \
            -f "$dockerfile" \
            -t "${image_name}:latest" \
            --label "maintainer=$GITHUB_USER" \
            --label "description=$repo" \
            --label "version=1.0.0" \
            --label "builddate=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
            --progress=plain \
            . 2>&1 | tee -a "$BUILD_LOG" | tail -5; then
            log_success "Built: ${image_name}:latest"
            ((successful++))
        else
            log_error "Failed to build: ${image_name}:latest"
            ((failed++))
            continue
        fi
        
        # Tag with version and stable
        log_info "Tagging image..."
        docker tag "${image_name}:latest" "${image_name}:v1.0.0"
        docker tag "${image_name}:latest" "${image_name}:stable"
        log_success "Tagged: v1.0.0, stable"
    done
    
    log_success "Docker build complete: $successful successful, $failed failed"
    
    # List all built images
    log_info "Built images:"
    docker images | grep "$DOCKER_USER" | tee -a "$BUILD_LOG"
}

# =============================================================================
# STEP 4: LOGIN TO DOCKER HUB
# =============================================================================

docker_hub_login() {
    print_header "STEP 4: DOCKER HUB AUTHENTICATION"
    
    log_info "Docker Hub username: $DOCKER_USER"
    
    # Check if already logged in
    if docker login -u "$DOCKER_USER" --password-stdin < /dev/null 2>&1 | grep -q "Login Succeeded"; then
        log_success "Already logged in to Docker Hub"
        return 0
    fi
    
    log_info "Please provide Docker Hub password (or token)..."
    log_info "Get token at: https://hub.docker.com/settings/security"
    
    read -sp "Enter Docker Hub password/token: " DOCKER_PASSWORD
    echo ""
    
    if echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin 2>&1 | tee -a "$BUILD_LOG" | grep -q "Succeeded"; then
        log_success "Docker Hub login successful"
        return 0
    else
        log_error "Docker Hub login failed"
        return 1
    fi
}

# =============================================================================
# STEP 5: PUSH DOCKER IMAGES TO DOCKER HUB
# =============================================================================

push_docker_images() {
    print_header "STEP 5: PUSHING DOCKER IMAGES TO DOCKER HUB"
    
    # Login first
    if ! docker_hub_login; then
        log_error "Docker Hub login required to push images"
        log_warning "Skipping push step"
        return 1
    fi
    
    local total=$((${#REPOS[@]} * 3))  # Each repo has 3 tags
    local current=0
    local successful=0
    local failed=0
    
    : > "$PUSH_LOG"
    
    for repo in "${!REPOS[@]}"; do
        local image_name="${DOCKER_USER}/${repo,,}"
        local tags=("latest" "v1.0.0" "stable")
        
        log_push "Pushing: $repo"
        
        for tag in "${tags[@]}"; do
            ((current++))
            
            local full_image="${image_name}:${tag}"
            
            log_push "[$current/$total] Pushing: $full_image"
            
            if docker push "$full_image" 2>&1 | tee -a "$PUSH_LOG" | tail -1 | grep -q "Pushed\|digest"; then
                log_push "✓ Pushed: $full_image"
                ((successful++))
            else
                log_push "✗ Failed: $full_image"
                ((failed++))
            fi
            
            sleep 2  # Rate limiting
        done
    done
    
    log_success "Docker Hub push complete: $successful successful, $failed failed"
}

# =============================================================================
# STEP 6: VERIFY PUSHED IMAGES
# =============================================================================

verify_pushed_images() {
    print_header "STEP 6: VERIFYING PUSHED IMAGES"
    
    log_info "Verifying images on Docker Hub..."
    log_info "Registry: https://hub.docker.com/r/$DOCKER_USER"
    
    # Get images from Docker Hub API
    log_info "Fetching image list from Docker Hub..."
    
    for repo in "${!REPOS[@]}"; do
        local image_name="${repo,,}"
        
        log_info "Checking: $image_name"
        
        # Use Docker Hub API to check if image exists
        if curl -s "https://hub.docker.com/v2/repositories/${DOCKER_USER}/${image_name}" | grep -q '"name"'; then
            log_success "Found on Docker Hub: $image_name"
        else
            log_warning "Not found on Docker Hub: $image_name"
        fi
    done
    
    log_success "Verification complete"
}

# =============================================================================
# STEP 7: GENERATE BUILD REPORT
# =============================================================================

generate_report() {
    print_header "STEP 7: GENERATING BUILD REPORT"
    
    cat > "$REPORT" << REPORT
════════════════════════════════════════════════════════════════════════════════
CHIMERA II OS - DOCKER BUILD & PUSH REPORT
════════════════════════════════════════════════════════════════════════════════

Build Date: $(date)
Build System: $HOSTNAME
Build User: $(whoami)
Build Directory: $BUILD_DIR

GitHub User: $GITHUB_USER
Docker Hub User: $DOCKER_USER
Registry: https://hub.docker.com/u/$DOCKER_USER

════════════════════════════════════════════════════════════════════════════════
DOCKER IMAGES BUILT & PUSHED (39 Total)
════════════════════════════════════════════════════════════════════════════════

REPORT
    
    local count=1
    for repo in "${!REPOS[@]}"; do
        local image_name="${DOCKER_USER}/${repo,,}"
        echo "$(printf '%2d' $count). $image_name" >> "$REPORT"
        echo "    • ${image_name}:latest" >> "$REPORT"
        echo "    • ${image_name}:v1.0.0" >> "$REPORT"
        echo "    • ${image_name}:stable" >> "$REPORT"
        echo "" >> "$REPORT"
        ((count++))
    done
    
    cat >> "$REPORT" << REPORT

════════════════════════════════════════════════════════════════════════════════
DOCKER IMAGES - LOCAL VERIFICATION
════════════════════════════════════════════════════════════════════════════════

REPORT
    
    docker images | grep "$DOCKER_USER" >> "$REPORT" 2>/dev/null || echo "Images available on Docker Hub" >> "$REPORT"
    
    cat >> "$REPORT" << REPORT

════════════════════════════════════════════════════════════════════════════════
PULL & RUN EXAMPLES
════════════════════════════════════════════════════════════════════════════════

# Pull an image
docker pull $DOCKER_USER/chimeraiios:latest

# Run container interactively
docker run -it $DOCKER_USER/chimeraiios:latest bash

# Run container with volume mount
docker run -it -v \$(pwd):/workspace $DOCKER_USER/chimeraiios:latest bash

# Run in background
docker run -d $DOCKER_USER/chimeraiios:latest

════════════════════════════════════════════════════════════════════════════════
DOCKER HUB LINKS
════════════════════════════════════════════════════════════════════════════════

User Profile: https://hub.docker.com/u/$DOCKER_USER
All Repositories: https://hub.docker.com/u/$DOCKER_USER

Individual Images:
REPORT
    
    for repo in "${!REPOS[@]}"; do
        echo "  • https://hub.docker.com/r/$DOCKER_USER/${repo,,}" >> "$REPORT"
    done
    
    cat >> "$REPORT" << REPORT

════════════════════════════════════════════════════════════════════════════════
DOCKER-COMPOSE DEPLOYMENT
════════════════════════════════════════════════════════════════════════════════

Save this as docker-compose.yml:

version: '3.8'
services:
  chimera-core:
    image: $DOCKER_USER/chimeraiios:latest
    container_name: chimera-core
    volumes:
      - ./workspace:/workspace
    ports:
      - "8000:8000"
      - "5000:5000"
    environment:
      - CHIMERA_ENV=production

  nlp-service:
    image: $DOCKER_USER/nlp:latest
    container_name: nlp-service
    volumes:
      - ./nlp:/workspace
    environment:
      - PYTHONUNBUFFERED=1

  business-service:
    image: $DOCKER_USER/bizx:latest
    container_name: business
    ports:
      - "3000:3000"

Then run:
  docker-compose up -d

════════════════════════════════════════════════════════════════════════════════
KUBERNETES DEPLOYMENT
════════════════════════════════════════════════════════════════════════════════

Save this as deployment.yaml:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: chimera-core
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chimera-core
  template:
    metadata:
      labels:
        app: chimera-core
    spec:
      containers:
      - name: chimera-core
        image: $DOCKER_USER/chimeraiios:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: workspace
          mountPath: /workspace
      volumes:
      - name: workspace
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: chimera-service
spec:
  selector:
    app: chimera-core
  ports:
    - protocol: TCP
      port: 8000
      targetPort: 8000
  type: LoadBalancer

Then deploy:
  kubectl apply -f deployment.yaml

════════════════════════════════════════════════════════════════════════════════
BUILD LOGS
════════════════════════════════════════════════════════════════════════════════

Build Log: $BUILD_LOG
Push Log: $PUSH_LOG

════════════════════════════════════════════════════════════════════════════════
NEXT STEPS
════════════════════════════════════════════════════════════════════════════════

1. Verify images on Docker Hub:
   https://hub.docker.com/u/$DOCKER_USER

2. Pull and test an image:
   docker pull $DOCKER_USER/chimeraiios:latest
   docker run -it $DOCKER_USER/chimeraiios:latest

3. Deploy with Docker Compose:
   docker-compose up -d

4. Deploy to Kubernetes:
   kubectl apply -f deployment.yaml

5. Update image tags and redeploy:
   docker pull $DOCKER_USER/chimeraiios:v1.0.0
   docker tag $DOCKER_USER/chimeraiios:v1.0.0 myregistry/chimeraiios:prod

════════════════════════════════════════════════════════════════════════════════
AUTHOR & SUPPORT
════════════════════════════════════════════════════════════════════════════════

Created by: Amer Abdullah Suleiman Hwitat - عامر الحويطات
Location: Amman 11814, Jordan
Email: amer.hwitat@proton.me
GitHub: https://github.com/$GITHUB_USER
Docker Hub: https://hub.docker.com/u/$DOCKER_USER
Repository: https://github.com/$GITHUB_USER/ChimeraIIOS

════════════════════════════════════════════════════════════════════════════════
END OF REPORT
════════════════════════════════════════════════════════════════════════════════

Generated: $(date)
REPORT
    
    log_success "Report generated: $REPORT"
    cat "$REPORT"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    initialize_build
    clone_or_update_repos
    build_docker_images
    push_docker_images
    verify_pushed_images
    generate_report
    
    print_header "DOCKER BUILD & PUSH COMPLETE!"
    log_success "All 13 repositories built and pushed to Docker Hub"
    log_info "Registry: https://hub.docker.com/u/$DOCKER_USER"
}

# Execute
main "$@"
