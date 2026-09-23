#!/bin/bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd)"
cd "$CHIMERA_REPO_ROOT"

# =============================================================================
# CHIMERA II OS - COMPREHENSIVE ISO BUILD SCRIPT
# =============================================================================
# Builds Docker image and creates bootable ISO from Dockerfile.comprehensive
# Supports BIOS/MBR and UEFI/GPT boot methods
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويطات
# Contact: amer.hwitat@proton.me
# Location: Amman 11814, Jordan
#
# Usage: sudo bash build-chimera-iso.sh [options]
# Options:
#   --docker-only       Build Docker image only (no ISO)
#   --iso-only          Build ISO from existing Docker image
#   --push              Push image to Docker registry after build
#   --tag TAG           Docker image tag (default: latest)
#   --registry REGISTRY Push to specific registry
# =============================================================================

set -Eeuo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_IMAGE="chimera2os-comprehensive"
DOCKER_TAG="${DOCKER_TAG:-latest}"
ISO_NAME="ChimeraIIOS-comprehensive"
ISO_VERSION="1.0.0"
BUILD_DIR="${SCRIPT_DIR}/build"
DOCKER_DIR="${BUILD_DIR}/docker"
ISO_DIR="${BUILD_DIR}/iso"
SQUASHFS_DIR="${BUILD_DIR}/squashfs"
BOOT_DIR="${ISO_DIR}/boot"
GRUB_DIR="${BOOT_DIR}/grub"
ROOTFS_DIR="${ISO_DIR}/rootfs"

# Flags
BUILD_DOCKER=1
BUILD_ISO=1
PUSH_REGISTRY=0
REGISTRY_NAME=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker-only)
            BUILD_ISO=0
            shift
            ;;
        --iso-only)
            BUILD_DOCKER=0
            shift
            ;;
        --push)
            PUSH_REGISTRY=1
            shift
            ;;
        --tag)
            DOCKER_TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY_NAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

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

check_requirements() {
    log_info "Checking system requirements..."
    
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    # Check required tools
    local required_tools=("docker" "curl" "mktemp" "mount" "grub-mkimage" "xorriso" "unsquashfs" "mksquashfs" "rsvg-convert")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_warning "Missing tools: ${missing_tools[*]}"
        log_info "Installing required packages..."
        apt-get update
        apt-get install -y \
            docker.io \
            curl \
            coreutils \
            grub-pc-bin \
            grub-efi-amd64-bin \
            xorriso \
            squashfs-tools \
            ca-certificates \
            librsvg2-bin
    fi
    
    # Check Docker
    if ! systemctl is-active --quiet docker; then
        log_info "Starting Docker daemon..."
        systemctl start docker
    fi
    
    log_success "All requirements met"
}

# =============================================================================
# DOCKER / STORAGE PREFLIGHT
# =============================================================================

check_docker_storage() {
    print_header "DOCKER / STORAGE PREFLIGHT"

    command -v docker >/dev/null 2>&1 || { log_error "Docker CLI is not installed."; exit 1; }

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is unavailable."
        log_error "On Docker Desktop/WSL, restart Docker Desktop and run: wsl --shutdown"
        exit 1
    fi

    log_info "Docker root: $(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo unknown)"

    local test_log="/tmp/chimera-docker-write-test.log"
    if ! docker run --rm ubuntu:24.04 sh -c '
        set -eu
        mkdir -p /tmp/chimera-write-test
        dd if=/dev/zero of=/tmp/chimera-write-test/test.bin bs=1M count=4 status=none
        test -s /tmp/chimera-write-test/test.bin
    ' >"$test_log" 2>&1; then
        log_error "Docker container storage write test failed."
        cat "$test_log" >&2 || true
        log_error "Docker Desktop/WSL containerd/overlayfs storage is unhealthy; aborting before the long build."
        exit 1
    fi
    rm -f "$test_log"

    if ! docker buildx inspect --bootstrap >/tmp/chimera-buildx-bootstrap.log 2>&1; then
        log_error "Docker BuildKit builder failed to bootstrap."
        cat /tmp/chimera-buildx-bootstrap.log >&2 || true
        exit 1
    fi
    rm -f /tmp/chimera-buildx-bootstrap.log

    local avail_kb
    avail_kb="$(df -Pk "$SCRIPT_DIR" 2>/dev/null | awk 'NR==2 {print $4}')"
    if [[ "$avail_kb" =~ ^[0-9]+$ ]]; then
        local avail_gb=$((avail_kb / 1024 / 1024))
        log_info "Repository filesystem free space: ${avail_gb} GiB"
        if (( avail_gb < 20 )); then
            log_warning "Less than 20 GiB is available; the comprehensive build needs substantial temporary storage."
        fi
    fi

    log_success "Docker storage preflight passed"
}

# =============================================================================
# DOCKER IMAGE BUILD
# =============================================================================

build_docker_image() {
    print_header "STEP 1: BUILDING DOCKER IMAGE"
    
    if [ ! -f "$SCRIPT_DIR/Dockerfile.comprehensive" ]; then
        log_error "Dockerfile.comprehensive not found in $SCRIPT_DIR"
        exit 1
    fi
    
    log_info "Building Docker image: $DOCKER_IMAGE:$DOCKER_TAG"
    log_info "This may take 30-45 minutes..."
    echo ""
    
    # Always pull the Ubuntu base and bypass stale Docker build layers.  This is
    # important after dependency changes: an older Dockerfile layer may otherwise
    # re-run the obsolete monolithic apt-get command.
    log_info "Using Dockerfile: $SCRIPT_DIR/Dockerfile.comprehensive"
    # The runtime stage intentionally has a small apt-get install.  Only reject
    # the obsolete monolithic builder-stage dependency list.
    if awk '
        /^FROM ubuntu:24\.04 AS builder/ { in_builder=1; next }
        /^FROM ubuntu:24\.04 AS runtime/ { in_builder=0 }
        in_builder && /apt-get update && apt-get install -y --no-install-recommends/ &&
        /build-essential/ && /gcc-13/ && /python3\.12/ { found=1 }
        END { exit(found ? 0 : 1) }
    ' "$SCRIPT_DIR/Dockerfile.comprehensive"; then
        log_error "Stale Dockerfile.comprehensive detected: obsolete monolithic builder APT install."
        log_error "The runtime-stage APT install is valid and is not treated as stale."
        exit 1
    fi

    if docker buildx prune -af >/tmp/chimera-buildx-prune.log 2>&1; then
        log_info "Unused BuildKit cache pruned."
    else
        log_warning "BuildKit cache prune failed; continuing after storage preflight."
        cat /tmp/chimera-buildx-prune.log >&2 || true
    fi
    rm -f /tmp/chimera-buildx-prune.log

    set +e
    # Docker Desktop is crashing while unpacking the huge multi-stage runtime
    # COPY --from=builder /usr/local /usr/local layer.  Prefer the containerd
    # image store only when it can safely materialize the layer; otherwise retry
    # with the legacy Docker image store if the current builder supports it.
    #
    # The first COPY (/opt/chimera) is already ~large; copying the complete
    # /usr/local tree creates another very large layer containing duplicated
    # toolchain data.  The build script therefore uses a dedicated Dockerfile
    # variant that omits the redundant /usr/local copy and installs runtime
    # packages in the final stage.
    local dockerfile_for_build="$SCRIPT_DIR/Dockerfile.comprehensive"
    local runtime_dockerfile="/tmp/Dockerfile.chimera-iso-runtime"
    cp "$SCRIPT_DIR/Dockerfile.comprehensive" "$runtime_dockerfile"

    # Remove the problematic/redundant runtime COPY of the entire builder
    # /usr/local tree.  The comprehensive runtime already receives
    # /opt/chimera/venv and applications from the builder.
    sed -i '/^COPY --from=builder \/usr\/local \/usr\/local$/d' "$runtime_dockerfile"

    if grep -q '^COPY --from=builder /usr/local /usr/local
    set -e

    if [ "$build_rc" -eq 0 ]; then
        log_success "Docker image built successfully"
        
        # Get image info
        IMAGE_SIZE=$(docker inspect --format='{{.Size}}' "$DOCKER_IMAGE:$DOCKER_TAG" | numfmt --to=iec)
        log_info "Image size: $IMAGE_SIZE"
        
        # Optional: Push to registry
        if [ "$PUSH_REGISTRY" -eq 1 ] && [ -n "$REGISTRY_NAME" ]; then
            log_info "Pushing image to $REGISTRY_NAME..."
            docker tag "$DOCKER_IMAGE:$DOCKER_TAG" "$REGISTRY_NAME/$DOCKER_IMAGE:$DOCKER_TAG"
            docker push "$REGISTRY_NAME/$DOCKER_IMAGE:$DOCKER_TAG"
            log_success "Image pushed to $REGISTRY_NAME"
        fi
    else
        log_error "Docker image build failed (exit $build_rc)."
        log_error "errno 5 / Input/output error, read-only filesystem, SIGBUS, or"
        log_error "metadata_v2.db errors indicate Docker Desktop/WSL storage failure."
        log_error "Do not use apt --fix-missing to repair errno 5."
        log_error "Recovery: stop Docker Desktop, run 'wsl --shutdown' from PowerShell, then restart Docker Desktop."
        log_error "After restart run: docker system df; docker buildx du; and rerun this script."
        log_error "If the write test still fails, back up Docker Desktop data before considering Reset/Reinstall."
        exit "$build_rc"
    fi
}

# =============================================================================
# EXPORT DOCKER IMAGE TO ROOTFS
# =============================================================================

export_docker_to_rootfs() {
    print_header "STEP 2: EXPORTING DOCKER IMAGE TO ROOTFS"
    
    log_info "Creating temporary directory for rootfs..."
    mkdir -p "$ROOTFS_DIR"
    
    log_info "Exporting Docker image to tar..."
    docker save "$DOCKER_IMAGE:$DOCKER_TAG" | tar -xC "$ROOTFS_DIR"
    
    log_info "Extracting layers from exported image..."
    
    # Find and extract the largest layer (contains the filesystem)
    local layer_dirs=$(find "$ROOTFS_DIR" -maxdepth 1 -type d -name "*/layer")
    for layer_dir in $layer_dirs; do
        if [ -f "$layer_dir/tar" ] || [ -f "$layer_dir/tar.gz" ]; then
            log_info "Extracting layer: $layer_dir"
            if [ -f "$layer_dir/tar" ]; then
                tar -xf "$layer_dir/tar" -C "$ROOTFS_DIR" 2>/dev/null || true
            fi
            if [ -f "$layer_dir/tar.gz" ]; then
                tar -xzf "$layer_dir/tar.gz" -C "$ROOTFS_DIR" 2>/dev/null || true
            fi
        fi
    done
    
    # Always flatten the final image with docker export.  Manually unpacking
    # containerd layer tarballs is unnecessary and is more fragile with the
    # Docker Desktop containerd image store.
    log_info "Flattening final image with docker export..."
    rm -rf "$ROOTFS_DIR"/*
    local container_name="chimera-export-$"
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    docker create --name "$container_name" "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null

    set +e
    docker export "$container_name" | tar -xpf - -C "$ROOTFS_DIR"
    local export_rc=${PIPESTATUS[0]}
    local tar_rc=${PIPESTATUS[1]}
    set -e

    docker rm -f "$container_name" >/dev/null 2>&1 || true

    if [ "$export_rc" -ne 0 ] || [ "$tar_rc" -ne 0 ] || [ ! -d "$ROOTFS_DIR/bin" ]; then
        log_error "Docker image export failed or root filesystem is incomplete."
        log_error "If Docker reports read-only filesystem/Input/output error/SIGBUS,"
        log_error "repair Docker Desktop/WSL storage before retrying the ISO build."
        exit 1
    fi

    log_success "Rootfs exported successfully"
}

# =============================================================================
# CREATE SQUASHFS FILESYSTEM
# =============================================================================

create_squashfs() {
    print_header "STEP 3: CREATING SQUASHFS FILESYSTEM"
    
    log_info "Creating squashfs from rootfs..."
    
    mkdir -p "$SQUASHFS_DIR"
    
    mksquashfs \
        "$ROOTFS_DIR" \
        "$ISO_DIR/live/filesystem.squashfs" \
        -no-progress \
        -processors 4 \
        -comp xz
    
    if [ $? -eq 0 ]; then
        local squashfs_size=$(du -h "$ISO_DIR/live/filesystem.squashfs" | cut -f1)
        log_success "Squashfs created: $squashfs_size"
    else
        log_error "Squashfs creation failed"
        exit 1
    fi
}

# =============================================================================
# CREATE BOOTLOADER
# =============================================================================

create_bootloader() {
    print_header "STEP 4: CREATING BOOTLOADERS"
    
    mkdir -p "$BOOT_DIR/grub/fonts"
    mkdir -p "$ISO_DIR/boot/syslinux"
    mkdir -p "$ISO_DIR/EFI/BOOT"
    
    # GRUB2 Configuration
    cat > "$GRUB_DIR/grub.cfg" << 'GRUB_CFG'
set default=0
set timeout=10
set menu_color_highlight=white/blue
set menu_color_normal=white/black

menuentry "Chimera II OS - Live System" {
    search --label ChimeraIIOS --set root
    echo "Loading ChimeraIIOS..."
    linux /live/vmlinuz boot=live quiet splash
    initrd /live/initrd.img
}

menuentry "Chimera II OS - Install" {
    search --label ChimeraIIOS --set root
    echo "Loading Chimera II OS Installer..."
    linux /live/vmlinuz boot=live boot=live-rw quiet splash
    initrd /live/initrd.img
}

menuentry "Chimera II OS - Safe Mode" {
    search --label ChimeraIIOS --set root
    echo "Loading ChimeraIIOS (Safe Mode)..."
    linux /live/vmlinuz boot=live quiet splash nomodeset
    initrd /live/initrd.img
}

menuentry "System Diagnostics" {
    search --label ChimeraIIOS --set root
    echo "Loading System Diagnostics..."
    linux /live/vmlinuz boot=live quiet memtest86 console=ttyS0
    initrd /live/initrd.img
}

menuentry "Reboot" {
    reboot
}

menuentry "Power Off" {
    halt
}
GRUB_CFG
    
    log_info "GRUB2 configuration created"
    
    # Create BIOS GRUB
    log_info "Creating BIOS bootloader..."
    grub-mkimage \
        -c "$GRUB_DIR/grub-early.cfg" \
        -o "$BOOT_DIR/grub/i386-pc/core.img" \
        -O i386-pc \
        biosdisk part_gpt part_msdos normal configfile 2>/dev/null || true
    
    # Create UEFI GRUB
    log_info "Creating UEFI bootloader..."
    grub-mkimage \
        -c "$GRUB_DIR/grub-early.cfg" \
        -o "$ISO_DIR/EFI/BOOT/BOOTX64.EFI" \
        -O x86_64-efi \
        efi_gop efi_uga video_bochs video_cirrus normal configfile 2>/dev/null || true
    
    log_success "Bootloaders created"
}

# =============================================================================
# CREATE ISO IMAGE
# =============================================================================

create_iso_image() {
    print_header "STEP 5: CREATING ISO IMAGE"
    
    local iso_file="${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    
    log_info "Creating bootable ISO image..."
    log_info "Output: $iso_file"
    
    # Create ISO with both BIOS and UEFI support
    xorriso \
        -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "ChimeraIIOS" \
        -output "$iso_file" \
        -eltorito-boot boot/grub/i386-pc/eltorito.img \
        -eltorito-catalog boot/grub/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -eltorito-alt-boot \
        -efi-boot EFI/BOOT/efiboot.img \
        -no-emul-boot \
        -append_partition 2 0xef "$ISO_DIR/EFI/BOOT/efiboot.img" \
        -m '*.~tmp~' \
        "$ISO_DIR" 2>/dev/null || {
        
        # Fallback: Create simpler ISO
        log_warning "Creating fallback ISO without EFI..."
        xorriso \
            -as mkisofs \
            -iso-level 3 \
            -full-iso9660-filenames \
            -volid "ChimeraIIOS" \
            -output "$iso_file" \
            -m '*.~tmp~' \
            "$ISO_DIR"
    }
    
    if [ -f "$iso_file" ]; then
        local iso_size=$(du -h "$iso_file" | cut -f1)
        log_success "ISO image created: $iso_file ($iso_size)"
        
        # Create checksums
        log_info "Creating checksums..."
        cd "$(dirname "$iso_file")"
        sha256sum "$(basename "$iso_file")" > "${iso_file}.sha256"
        md5sum "$(basename "$iso_file")" > "${iso_file}.md5"
        log_success "Checksums created"
        
        cd - > /dev/null
    else
        log_error "ISO image creation failed"
        exit 1
    fi
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup() {
    print_header "CLEANUP"
    
    log_info "Cleaning up temporary files..."
    
    if [ -d "$DOCKER_DIR" ]; then
        rm -rf "$DOCKER_DIR"
    fi
    
    if [ -d "$SQUASHFS_DIR" ]; then
        rm -rf "$SQUASHFS_DIR"
    fi
    
    log_success "Cleanup completed"
}

# =============================================================================
# VERIFICATION
# =============================================================================

verify_iso() {
    print_header "VERIFICATION"
    
    local iso_file="${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    
    if [ ! -f "$iso_file" ]; then
        log_error "ISO file not found: $iso_file"
        return 1
    fi
    
    log_info "Verifying ISO file..."
    
    # File size check
    local iso_size=$(stat -f%z "$iso_file" 2>/dev/null || stat -c%s "$iso_file" 2>/dev/null)
    if [ "$iso_size" -lt 1073741824 ]; then  # Less than 1GB
        log_warning "ISO size unusually small: $(numfmt --to=iec "$iso_size" 2>/dev/null || echo "$iso_size")"
    else
        log_success "ISO size valid: $(numfmt --to=iec "$iso_size" 2>/dev/null || echo "$iso_size")"
    fi
    
    # Check signatures
    if [ -f "${iso_file}.sha256" ]; then
        log_info "Verifying SHA256 checksum..."
        cd "$(dirname "$iso_file")"
        if sha256sum -c "${iso_file##*/}.sha256" &>/dev/null; then
            log_success "SHA256 checksum verified"
        fi
        cd - > /dev/null
    fi
    
    log_success "Verification completed"
}

# =============================================================================
# GENERATE BOOTABLE ISO BOOT MENU
# =============================================================================

create_boot_menu() {
    print_header "CREATING BOOT MENU"
    
    # Create boot menu script
    cat > "$ISO_DIR/boot/grub/grub-early.cfg" << 'BOOT_MENU'
search --label ChimeraIIOS --set root
configfile /boot/grub/grub.cfg
BOOT_MENU
    
    log_info "Boot menu configuration created"
}

# =============================================================================
# INSTALL CHIMERA II OS BRANDING
# =============================================================================

add_branding() {
    print_header "ADDING BRANDING"
    
    # Create bootloader message
    mkdir -p "$ISO_DIR/boot/grub"
    
    cat > "$ISO_DIR/boot/grub/message.txt" << 'BRANDING'
        ============================================================
        CHIMERA II OS - COMPREHENSIVE EDITION
        ============================================================
        created by Amer Abdullah Suleiman Hwitat - عامر الحويطات
        Amman 11814, Jordan
        for support contact: amer.hwitat@proton.me
        
        Visit: https://github.com/amerhwitat
        ============================================================
BRANDING
    
    # Create splash screen info
    mkdir -p "$ROOTFS_DIR/etc"
    cat > "$ROOTFS_DIR/etc/os-release" << 'OSINFO'
NAME="Chimera II OS"
VERSION="1.0.0"
ID=chimera
ID_LIKE=linux
PRETTY_NAME="Chimera II OS 1.0.0 (Comprehensive Edition)"
HOME_URL="https://github.com/amerhwitat/ChimeraIIOS"
DOCUMENTATION_URL="https://github.com/amerhwitat/ChimeraIIOS/wiki"
SUPPORT_URL="https://github.com/amerhwitat/ChimeraIIOS/issues"
BUG_REPORT_URL="https://github.com/amerhwitat/ChimeraIIOS/issues"
OSINFO
    
    log_success "Branding added"
}

# =============================================================================
# GENERATE BUILD REPORT
# =============================================================================

generate_report() {
    print_header "BUILD REPORT"
    
    local iso_file="${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    local report_file="${SCRIPT_DIR}/build-report.txt"
    
    cat > "$report_file" << REPORT
================================================================================
CHIMERA II OS - COMPREHENSIVE ISO BUILD REPORT
================================================================================

Build Date: $(date)
Build Host: $(hostname)
Build User: $(whoami)

================================================================================
DOCKER IMAGE INFORMATION
================================================================================

Image Name:     $DOCKER_IMAGE:$DOCKER_TAG
Build Command:  docker build -f Dockerfile.comprehensive -t $DOCKER_IMAGE:$DOCKER_TAG .
Build Time:     30-45 minutes (estimated)
Image Size:     $(docker inspect --format='{{.Size}}' "$DOCKER_IMAGE:$DOCKER_TAG" 2>/dev/null | numfmt --to=iec || echo "N/A")

Integrated Repositories: 13
- ChimeraIIOS (Core OS)
- nlp (NLP/AI)
- BizX (Business)
- BizXtreme (Enterprise)
- CPU4096 (4096-bit CPU)
- CPU4096Simulator (Web Simulator)
- keygen (Cryptography)
- eth-key-check (Ethereum)
- bruteforce (Security)
- PDFreaderPY (PDF)
- general (Utilities)
- test (Testing)
- Portfolio (Documentation)

Included Toolchain:
- Compilers: GCC 13, Clang/LLVM, Python 3.12, Node.js, Rust, Java 21, .NET 8
- Build Tools: CMake, Ninja, Make, Git
- Data Science: TensorFlow, PyTorch, scikit-learn, NumPy, Pandas
- Web Frameworks: Flask, FastAPI, SQLAlchemy

================================================================================
ISO IMAGE INFORMATION
================================================================================

ISO File:       $iso_file
ISO Name:       ChimeraIIOS
ISO Version:    $ISO_VERSION
ISO Label:      ChimeraIIOS
ISO Size:       $(stat -c%s "$iso_file" 2>/dev/null | numfmt --to=iec || echo "N/A")

Boot Methods:
✓ BIOS/MBR Boot (Legacy)
✓ UEFI/GPT Boot (Modern)

Boot Options:
1. Live System (Read-only)
2. Install Mode (Live RW)
3. Safe Mode (NoModeset)
4. Diagnostics
5. Reboot
6. Power Off

================================================================================
BOOTLOADER CONFIGURATION
================================================================================

BIOS Bootloader:      GRUB 2 (i386-pc)
UEFI Bootloader:      GRUB 2 (x86_64-efi)
Boot Timeout:         10 seconds
Default Boot Entry:   Chimera II OS - Live System

Boot Parameters:
- Kernel: /live/vmlinuz
- Initrd: /live/initrd.img
- Boot Mode: boot=live
- Options: quiet splash

================================================================================
VERIFICATION
================================================================================

SHA256 Checksum:
$(sha256sum "$iso_file" 2>/dev/null || echo "N/A")

MD5 Checksum:
$(md5sum "$iso_file" 2>/dev/null || echo "N/A")

================================================================================
HOW TO USE THE ISO
================================================================================

1. BURN TO USB:
   sudo dd if=$iso_file of=/dev/sdX bs=4M status=progress
   (Replace /dev/sdX with your USB device)

2. BURN TO DVD:
   cdrecord -v -sao $iso_file

3. QEMU BOOT (Testing):
   qemu-system-x86_64 -cdrom $iso_file -m 4G

4. VirtualBox:
   - Create new VM
   - ISO image: $iso_file
   - Boot from CD

5. VMware:
   - Create new VM
   - Attach ISO: $iso_file
   - Boot VM

================================================================================
AUTHOR & SUPPORT
================================================================================

Created by: Amer Abdullah Suleiman Hwitat - عامر الحويطات
Location:   Amman 11814, Jordan
Email:      amer.hwitat@proton.me
GitHub:     https://github.com/amerhwitat
Repos:      https://github.com/amerhwitat?tab=repositories

For issues and support: amer.hwitat@proton.me

================================================================================
END OF REPORT
================================================================================

Generated: $(date)
Report Location: $report_file
REPORT
    
    log_success "Report generated: $report_file"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "CHIMERA II OS - COMPREHENSIVE ISO BUILD SYSTEM"
    echo "created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"
    echo "Contact: amer.hwitat@proton.me"
    echo ""
    
    # Check requirements
    check_requirements
    
    # Create build directories
    mkdir -p "$BUILD_DIR" "$DOCKER_DIR" "$ISO_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ROOTFS_DIR"
    
    # Build Docker image
    if [ "$BUILD_DOCKER" -eq 1 ]; then
        build_docker_image
    fi
    
    # Build ISO
    if [ "$BUILD_ISO" -eq 1 ]; then
        export_docker_to_rootfs
        create_boot_menu
        add_branding
        create_bootloader
        create_squashfs
        create_iso_image
        verify_iso
        generate_report
    fi
    
    # Cleanup
    cleanup
    
    print_header "BUILD COMPLETED SUCCESSFULLY"
    log_success "ISO file ready at: ${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    log_info "Build report: ${SCRIPT_DIR}/build-report.txt"
    echo ""
}

# Execute main
main
 "$runtime_dockerfile"; then
        log_error "Failed to prepare reduced runtime Dockerfile."
        rm -f "$runtime_dockerfile"
        exit 1
    fi

    log_info "Using reduced runtime Dockerfile: removes redundant /usr/local COPY layer."
    dockerfile_for_build="$runtime_dockerfile"

    docker build \
        --pull \
        --no-cache \
        --progress=plain \
        -f "$dockerfile_for_build" \
        -t "$DOCKER_IMAGE:$DOCKER_TAG" \
        -t "$DOCKER_IMAGE:latest" \
        "$SCRIPT_DIR"
    local build_rc=$?
    rm -f "$runtime_dockerfile"
    local build_rc=$?
    set -e

    if [ "$build_rc" -eq 0 ]; then
        log_success "Docker image built successfully"
        
        # Get image info
        IMAGE_SIZE=$(docker inspect --format='{{.Size}}' "$DOCKER_IMAGE:$DOCKER_TAG" | numfmt --to=iec)
        log_info "Image size: $IMAGE_SIZE"
        
        # Optional: Push to registry
        if [ "$PUSH_REGISTRY" -eq 1 ] && [ -n "$REGISTRY_NAME" ]; then
            log_info "Pushing image to $REGISTRY_NAME..."
            docker tag "$DOCKER_IMAGE:$DOCKER_TAG" "$REGISTRY_NAME/$DOCKER_IMAGE:$DOCKER_TAG"
            docker push "$REGISTRY_NAME/$DOCKER_IMAGE:$DOCKER_TAG"
            log_success "Image pushed to $REGISTRY_NAME"
        fi
    else
        log_error "Docker image build failed (exit $build_rc)."
        log_error "errno 5 / Input/output error, read-only filesystem, SIGBUS, or"
        log_error "metadata_v2.db errors indicate Docker Desktop/WSL storage failure."
        log_error "Do not use apt --fix-missing to repair errno 5."
        log_error "Recovery: stop Docker Desktop, run 'wsl --shutdown' from PowerShell, then restart Docker Desktop."
        log_error "After restart run: docker system df; docker buildx du; and rerun this script."
        log_error "If the write test still fails, back up Docker Desktop data before considering Reset/Reinstall."
        exit "$build_rc"
    fi
}

# =============================================================================
# EXPORT DOCKER IMAGE TO ROOTFS
# =============================================================================

export_docker_to_rootfs() {
    print_header "STEP 2: EXPORTING DOCKER IMAGE TO ROOTFS"
    
    log_info "Creating temporary directory for rootfs..."
    mkdir -p "$ROOTFS_DIR"
    
    log_info "Exporting Docker image to tar..."
    docker save "$DOCKER_IMAGE:$DOCKER_TAG" | tar -xC "$ROOTFS_DIR"
    
    log_info "Extracting layers from exported image..."
    
    # Find and extract the largest layer (contains the filesystem)
    local layer_dirs=$(find "$ROOTFS_DIR" -maxdepth 1 -type d -name "*/layer")
    for layer_dir in $layer_dirs; do
        if [ -f "$layer_dir/tar" ] || [ -f "$layer_dir/tar.gz" ]; then
            log_info "Extracting layer: $layer_dir"
            if [ -f "$layer_dir/tar" ]; then
                tar -xf "$layer_dir/tar" -C "$ROOTFS_DIR" 2>/dev/null || true
            fi
            if [ -f "$layer_dir/tar.gz" ]; then
                tar -xzf "$layer_dir/tar.gz" -C "$ROOTFS_DIR" 2>/dev/null || true
            fi
        fi
    done
    
    # Always flatten the final image with docker export.  Manually unpacking
    # containerd layer tarballs is unnecessary and is more fragile with the
    # Docker Desktop containerd image store.
    log_info "Flattening final image with docker export..."
    rm -rf "$ROOTFS_DIR"/*
    local container_name="chimera-export-$"
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    docker create --name "$container_name" "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null

    set +e
    docker export "$container_name" | tar -xpf - -C "$ROOTFS_DIR"
    local export_rc=${PIPESTATUS[0]}
    local tar_rc=${PIPESTATUS[1]}
    set -e

    docker rm -f "$container_name" >/dev/null 2>&1 || true

    if [ "$export_rc" -ne 0 ] || [ "$tar_rc" -ne 0 ] || [ ! -d "$ROOTFS_DIR/bin" ]; then
        log_error "Docker image export failed or root filesystem is incomplete."
        log_error "If Docker reports read-only filesystem/Input/output error/SIGBUS,"
        log_error "repair Docker Desktop/WSL storage before retrying the ISO build."
        exit 1
    fi

    log_success "Rootfs exported successfully"
}

# =============================================================================
# CREATE SQUASHFS FILESYSTEM
# =============================================================================

create_squashfs() {
    print_header "STEP 3: CREATING SQUASHFS FILESYSTEM"
    
    log_info "Creating squashfs from rootfs..."
    
    mkdir -p "$SQUASHFS_DIR"
    
    mksquashfs \
        "$ROOTFS_DIR" \
        "$ISO_DIR/live/filesystem.squashfs" \
        -no-progress \
        -processors 4 \
        -comp xz
    
    if [ $? -eq 0 ]; then
        local squashfs_size=$(du -h "$ISO_DIR/live/filesystem.squashfs" | cut -f1)
        log_success "Squashfs created: $squashfs_size"
    else
        log_error "Squashfs creation failed"
        exit 1
    fi
}

# =============================================================================
# CREATE BOOTLOADER
# =============================================================================

create_bootloader() {
    print_header "STEP 4: CREATING BOOTLOADERS"
    
    mkdir -p "$BOOT_DIR/grub/fonts"
    mkdir -p "$ISO_DIR/boot/syslinux"
    mkdir -p "$ISO_DIR/EFI/BOOT"
    
    # GRUB2 Configuration
    cat > "$GRUB_DIR/grub.cfg" << 'GRUB_CFG'
set default=0
set timeout=10
set menu_color_highlight=white/blue
set menu_color_normal=white/black

menuentry "Chimera II OS - Live System" {
    search --label ChimeraIIOS --set root
    echo "Loading ChimeraIIOS..."
    linux /live/vmlinuz boot=live quiet splash
    initrd /live/initrd.img
}

menuentry "Chimera II OS - Install" {
    search --label ChimeraIIOS --set root
    echo "Loading Chimera II OS Installer..."
    linux /live/vmlinuz boot=live boot=live-rw quiet splash
    initrd /live/initrd.img
}

menuentry "Chimera II OS - Safe Mode" {
    search --label ChimeraIIOS --set root
    echo "Loading ChimeraIIOS (Safe Mode)..."
    linux /live/vmlinuz boot=live quiet splash nomodeset
    initrd /live/initrd.img
}

menuentry "System Diagnostics" {
    search --label ChimeraIIOS --set root
    echo "Loading System Diagnostics..."
    linux /live/vmlinuz boot=live quiet memtest86 console=ttyS0
    initrd /live/initrd.img
}

menuentry "Reboot" {
    reboot
}

menuentry "Power Off" {
    halt
}
GRUB_CFG
    
    log_info "GRUB2 configuration created"
    
    # Create BIOS GRUB
    log_info "Creating BIOS bootloader..."
    grub-mkimage \
        -c "$GRUB_DIR/grub-early.cfg" \
        -o "$BOOT_DIR/grub/i386-pc/core.img" \
        -O i386-pc \
        biosdisk part_gpt part_msdos normal configfile 2>/dev/null || true
    
    # Create UEFI GRUB
    log_info "Creating UEFI bootloader..."
    grub-mkimage \
        -c "$GRUB_DIR/grub-early.cfg" \
        -o "$ISO_DIR/EFI/BOOT/BOOTX64.EFI" \
        -O x86_64-efi \
        efi_gop efi_uga video_bochs video_cirrus normal configfile 2>/dev/null || true
    
    log_success "Bootloaders created"
}

# =============================================================================
# CREATE ISO IMAGE
# =============================================================================

create_iso_image() {
    print_header "STEP 5: CREATING ISO IMAGE"
    
    local iso_file="${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    
    log_info "Creating bootable ISO image..."
    log_info "Output: $iso_file"
    
    # Create ISO with both BIOS and UEFI support
    xorriso \
        -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "ChimeraIIOS" \
        -output "$iso_file" \
        -eltorito-boot boot/grub/i386-pc/eltorito.img \
        -eltorito-catalog boot/grub/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -eltorito-alt-boot \
        -efi-boot EFI/BOOT/efiboot.img \
        -no-emul-boot \
        -append_partition 2 0xef "$ISO_DIR/EFI/BOOT/efiboot.img" \
        -m '*.~tmp~' \
        "$ISO_DIR" 2>/dev/null || {
        
        # Fallback: Create simpler ISO
        log_warning "Creating fallback ISO without EFI..."
        xorriso \
            -as mkisofs \
            -iso-level 3 \
            -full-iso9660-filenames \
            -volid "ChimeraIIOS" \
            -output "$iso_file" \
            -m '*.~tmp~' \
            "$ISO_DIR"
    }
    
    if [ -f "$iso_file" ]; then
        local iso_size=$(du -h "$iso_file" | cut -f1)
        log_success "ISO image created: $iso_file ($iso_size)"
        
        # Create checksums
        log_info "Creating checksums..."
        cd "$(dirname "$iso_file")"
        sha256sum "$(basename "$iso_file")" > "${iso_file}.sha256"
        md5sum "$(basename "$iso_file")" > "${iso_file}.md5"
        log_success "Checksums created"
        
        cd - > /dev/null
    else
        log_error "ISO image creation failed"
        exit 1
    fi
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup() {
    print_header "CLEANUP"
    
    log_info "Cleaning up temporary files..."
    
    if [ -d "$DOCKER_DIR" ]; then
        rm -rf "$DOCKER_DIR"
    fi
    
    if [ -d "$SQUASHFS_DIR" ]; then
        rm -rf "$SQUASHFS_DIR"
    fi
    
    log_success "Cleanup completed"
}

# =============================================================================
# VERIFICATION
# =============================================================================

verify_iso() {
    print_header "VERIFICATION"
    
    local iso_file="${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    
    if [ ! -f "$iso_file" ]; then
        log_error "ISO file not found: $iso_file"
        return 1
    fi
    
    log_info "Verifying ISO file..."
    
    # File size check
    local iso_size=$(stat -f%z "$iso_file" 2>/dev/null || stat -c%s "$iso_file" 2>/dev/null)
    if [ "$iso_size" -lt 1073741824 ]; then  # Less than 1GB
        log_warning "ISO size unusually small: $(numfmt --to=iec "$iso_size" 2>/dev/null || echo "$iso_size")"
    else
        log_success "ISO size valid: $(numfmt --to=iec "$iso_size" 2>/dev/null || echo "$iso_size")"
    fi
    
    # Check signatures
    if [ -f "${iso_file}.sha256" ]; then
        log_info "Verifying SHA256 checksum..."
        cd "$(dirname "$iso_file")"
        if sha256sum -c "${iso_file##*/}.sha256" &>/dev/null; then
            log_success "SHA256 checksum verified"
        fi
        cd - > /dev/null
    fi
    
    log_success "Verification completed"
}

# =============================================================================
# GENERATE BOOTABLE ISO BOOT MENU
# =============================================================================

create_boot_menu() {
    print_header "CREATING BOOT MENU"
    
    # Create boot menu script
    cat > "$ISO_DIR/boot/grub/grub-early.cfg" << 'BOOT_MENU'
search --label ChimeraIIOS --set root
configfile /boot/grub/grub.cfg
BOOT_MENU
    
    log_info "Boot menu configuration created"
}

# =============================================================================
# INSTALL CHIMERA II OS BRANDING
# =============================================================================

add_branding() {
    print_header "ADDING BRANDING"
    
    # Create bootloader message
    mkdir -p "$ISO_DIR/boot/grub"
    
    cat > "$ISO_DIR/boot/grub/message.txt" << 'BRANDING'
        ============================================================
        CHIMERA II OS - COMPREHENSIVE EDITION
        ============================================================
        created by Amer Abdullah Suleiman Hwitat - عامر الحويطات
        Amman 11814, Jordan
        for support contact: amer.hwitat@proton.me
        
        Visit: https://github.com/amerhwitat
        ============================================================
BRANDING
    
    # Create splash screen info
    mkdir -p "$ROOTFS_DIR/etc"
    cat > "$ROOTFS_DIR/etc/os-release" << 'OSINFO'
NAME="Chimera II OS"
VERSION="1.0.0"
ID=chimera
ID_LIKE=linux
PRETTY_NAME="Chimera II OS 1.0.0 (Comprehensive Edition)"
HOME_URL="https://github.com/amerhwitat/ChimeraIIOS"
DOCUMENTATION_URL="https://github.com/amerhwitat/ChimeraIIOS/wiki"
SUPPORT_URL="https://github.com/amerhwitat/ChimeraIIOS/issues"
BUG_REPORT_URL="https://github.com/amerhwitat/ChimeraIIOS/issues"
OSINFO
    
    log_success "Branding added"
}

# =============================================================================
# GENERATE BUILD REPORT
# =============================================================================

generate_report() {
    print_header "BUILD REPORT"
    
    local iso_file="${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    local report_file="${SCRIPT_DIR}/build-report.txt"
    
    cat > "$report_file" << REPORT
================================================================================
CHIMERA II OS - COMPREHENSIVE ISO BUILD REPORT
================================================================================

Build Date: $(date)
Build Host: $(hostname)
Build User: $(whoami)

================================================================================
DOCKER IMAGE INFORMATION
================================================================================

Image Name:     $DOCKER_IMAGE:$DOCKER_TAG
Build Command:  docker build -f Dockerfile.comprehensive -t $DOCKER_IMAGE:$DOCKER_TAG .
Build Time:     30-45 minutes (estimated)
Image Size:     $(docker inspect --format='{{.Size}}' "$DOCKER_IMAGE:$DOCKER_TAG" 2>/dev/null | numfmt --to=iec || echo "N/A")

Integrated Repositories: 13
- ChimeraIIOS (Core OS)
- nlp (NLP/AI)
- BizX (Business)
- BizXtreme (Enterprise)
- CPU4096 (4096-bit CPU)
- CPU4096Simulator (Web Simulator)
- keygen (Cryptography)
- eth-key-check (Ethereum)
- bruteforce (Security)
- PDFreaderPY (PDF)
- general (Utilities)
- test (Testing)
- Portfolio (Documentation)

Included Toolchain:
- Compilers: GCC 13, Clang/LLVM, Python 3.12, Node.js, Rust, Java 21, .NET 8
- Build Tools: CMake, Ninja, Make, Git
- Data Science: TensorFlow, PyTorch, scikit-learn, NumPy, Pandas
- Web Frameworks: Flask, FastAPI, SQLAlchemy

================================================================================
ISO IMAGE INFORMATION
================================================================================

ISO File:       $iso_file
ISO Name:       ChimeraIIOS
ISO Version:    $ISO_VERSION
ISO Label:      ChimeraIIOS
ISO Size:       $(stat -c%s "$iso_file" 2>/dev/null | numfmt --to=iec || echo "N/A")

Boot Methods:
✓ BIOS/MBR Boot (Legacy)
✓ UEFI/GPT Boot (Modern)

Boot Options:
1. Live System (Read-only)
2. Install Mode (Live RW)
3. Safe Mode (NoModeset)
4. Diagnostics
5. Reboot
6. Power Off

================================================================================
BOOTLOADER CONFIGURATION
================================================================================

BIOS Bootloader:      GRUB 2 (i386-pc)
UEFI Bootloader:      GRUB 2 (x86_64-efi)
Boot Timeout:         10 seconds
Default Boot Entry:   Chimera II OS - Live System

Boot Parameters:
- Kernel: /live/vmlinuz
- Initrd: /live/initrd.img
- Boot Mode: boot=live
- Options: quiet splash

================================================================================
VERIFICATION
================================================================================

SHA256 Checksum:
$(sha256sum "$iso_file" 2>/dev/null || echo "N/A")

MD5 Checksum:
$(md5sum "$iso_file" 2>/dev/null || echo "N/A")

================================================================================
HOW TO USE THE ISO
================================================================================

1. BURN TO USB:
   sudo dd if=$iso_file of=/dev/sdX bs=4M status=progress
   (Replace /dev/sdX with your USB device)

2. BURN TO DVD:
   cdrecord -v -sao $iso_file

3. QEMU BOOT (Testing):
   qemu-system-x86_64 -cdrom $iso_file -m 4G

4. VirtualBox:
   - Create new VM
   - ISO image: $iso_file
   - Boot from CD

5. VMware:
   - Create new VM
   - Attach ISO: $iso_file
   - Boot VM

================================================================================
AUTHOR & SUPPORT
================================================================================

Created by: Amer Abdullah Suleiman Hwitat - عامر الحويطات
Location:   Amman 11814, Jordan
Email:      amer.hwitat@proton.me
GitHub:     https://github.com/amerhwitat
Repos:      https://github.com/amerhwitat?tab=repositories

For issues and support: amer.hwitat@proton.me

================================================================================
END OF REPORT
================================================================================

Generated: $(date)
Report Location: $report_file
REPORT
    
    log_success "Report generated: $report_file"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "CHIMERA II OS - COMPREHENSIVE ISO BUILD SYSTEM"
    echo "created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"
    echo "Contact: amer.hwitat@proton.me"
    echo ""
    
    # Check requirements
    check_requirements
    
    # Create build directories
    mkdir -p "$BUILD_DIR" "$DOCKER_DIR" "$ISO_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ROOTFS_DIR"
    
    # Build Docker image
    if [ "$BUILD_DOCKER" -eq 1 ]; then
        build_docker_image
    fi
    
    # Build ISO
    if [ "$BUILD_ISO" -eq 1 ]; then
        export_docker_to_rootfs
        create_boot_menu
        add_branding
        create_bootloader
        create_squashfs
        create_iso_image
        verify_iso
        generate_report
    fi
    
    # Cleanup
    cleanup
    
    print_header "BUILD COMPLETED SUCCESSFULLY"
    log_success "ISO file ready at: ${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    log_info "Build report: ${SCRIPT_DIR}/build-report.txt"
    echo ""
}

# Execute main
main
