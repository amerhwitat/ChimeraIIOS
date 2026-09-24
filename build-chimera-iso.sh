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
#   --apache-ecosystem  Include the ASF official-release package manager/catalog
#   --skip-apache       Do not stage the ASF ecosystem integration
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
DOCKER_PULL="${CHIMERA_DOCKER_PULL:-0}"
DOCKER_NO_CACHE="${CHIMERA_DOCKER_NO_CACHE:-0}"
DOCKER_RETRIES="${CHIMERA_DOCKER_RETRIES:-2}"
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
APACHE_ECOSYSTEM=1
APACHE_ECOSYSTEM_MODE="${CHIMERA_APACHE_ECOSYSTEM:-metadata}"

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
        --apache-ecosystem)
            APACHE_ECOSYSTEM=1
            shift
            ;;
        --skip-apache)
            APACHE_ECOSYSTEM=0
            shift
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
    log_info "Checking and automatically installing all ISO/Docker build dependencies..."

    if [ "${CHIMERA_AUTO_INSTALL_DEPS:-1}" = "1" ]; then
        CHIMERA_INSTALL_OPTIONAL_DEPS="${CHIMERA_INSTALL_OPTIONAL_DEPS:-1}" \
            "$SCRIPT_DIR/tools/check-build-dependencies.sh"
    else
        CHIMERA_AUTO_INSTALL_DEPS=0 \
            "$SCRIPT_DIR/tools/check-build-dependencies.sh"
    fi

    # Docker is the only host-specific dependency outside the generic ISO
    # toolchain. On Debian/Ubuntu it can be installed automatically; Docker
    # Desktop/WSL remains supported when the Docker CLI is already present.
    if ! command -v docker >/dev/null 2>&1 && [ "${CHIMERA_INSTALL_DOCKER:-1}" = "1" ] \
       && command -v apt-get >/dev/null 2>&1 && [ -f /etc/debian_version ]; then
        local apt_prefix=()
        [ "$(id -u)" -eq 0 ] || {
            command -v sudo >/dev/null 2>&1 || { log_error "sudo is required to install docker.io"; exit 2; }
            apt_prefix=(sudo)
        }
        log_info "Docker CLI missing; installing docker.io automatically..."
        "${apt_prefix[@]}" apt-get update
        "${apt_prefix[@]}" apt-get install -y --no-install-recommends docker.io || {
            log_error "docker.io installation failed."; exit 2;
        }
        "${apt_prefix[@]}" apt-get install -y --no-install-recommends docker-buildx-plugin docker-buildx 2>/dev/null || true
    fi

    # Dependencies specific to the comprehensive Docker/rootfs workflow.
    local required_tools=("docker" "mktemp" "mount" "unsquashfs" "mksquashfs")
    local missing_tools=()
    for tool in "${required_tools[@]}"; do
        command -v "$tool" >/dev/null 2>&1 || missing_tools+=("$tool")
    done

    if [ "${#missing_tools[@]}" -gt 0 ]; then
        log_error "Docker/comprehensive-build tools are still missing: ${missing_tools[*]}"
        log_error "Install Docker Engine/Docker Desktop and ensure the daemon is running."
        exit 2
    fi

    # Docker is intentionally not installed by the generic ISO dependency
    # helper because Docker Engine/Desktop is host/platform specific.
    if ! systemctl is-active --quiet docker 2>/dev/null; then
        log_info "Docker daemon is not active; attempting to start it..."
        if command -v systemctl >/dev/null 2>&1; then
            systemctl start docker 2>/dev/null || true
        fi
    fi

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is unavailable. Start Docker Engine/Docker Desktop before continuing."
        exit 2
    fi

    log_success "All mandatory ISO and comprehensive-build dependencies are available"
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

    if [ "${CHIMERA_PRUNE:-0}" = "1" ] && docker buildx prune -af >/tmp/chimera-buildx-prune.log 2>&1; then
        log_info "Unused BuildKit cache pruned."
    else
        log_warning "BuildKit cache prune failed; continuing."
        cat /tmp/chimera-buildx-prune.log >&2 || true
    fi
    rm -f /tmp/chimera-buildx-prune.log

    # Dockerfile.comprehensive now uses FROM builder AS runtime. This avoids
    # the large cross-stage /opt/chimera and /usr/local COPY operations that
    # caused Docker Desktop/containerd SIGBUS crashes.
    local docker_build_flags=(--progress=plain)
    [ "$DOCKER_PULL" = "1" ] && docker_build_flags+=(--pull)
    [ "$DOCKER_NO_CACHE" = "1" ] && docker_build_flags+=(--no-cache)

    local build_rc=1
    local attempt
    for attempt in $(seq 1 "$DOCKER_RETRIES"); do
        log_info "Docker build attempt $attempt/$DOCKER_RETRIES"
        set +e
        docker build "${docker_build_flags[@]}" \
            -f "$SCRIPT_DIR/Dockerfile.comprehensive" \
            -t "$DOCKER_IMAGE:$DOCKER_TAG" \
            -t "$DOCKER_IMAGE:latest" \
            "$SCRIPT_DIR"
        build_rc=$?
        set -e
        [ "$build_rc" -eq 0 ] && break
        if [ "$attempt" -lt "$DOCKER_RETRIES" ]; then
            log_warning "Build failed; running a small Docker storage write test before retry."
            if ! docker run --rm ubuntu:24.04 sh -c 'dd if=/dev/zero of=/tmp/chimera-retry.bin bs=1M count=8 status=none && test -s /tmp/chimera-retry.bin' >/tmp/chimera-storage-retry.log 2>&1; then
                log_error "Docker storage test failed; aborting retries."
                cat /tmp/chimera-storage-retry.log >&2 || true
                break
            fi
            rm -f /tmp/chimera-storage-retry.log
            sleep 3
        fi
    done

    if [ "$build_rc" -eq 0 ]; then
        log_success "Docker image built successfully"

        local image_size
        image_size="$(docker inspect --format='{{.Size}}' "$DOCKER_IMAGE:$DOCKER_TAG" | numfmt --to=iec)"
        log_info "Image size: $image_size"

        if [ "$PUSH_REGISTRY" -eq 1 ] && [ -n "$REGISTRY_NAME" ]; then
            log_info "Pushing image to $REGISTRY_NAME..."
            docker tag "$DOCKER_IMAGE:$DOCKER_TAG" "$REGISTRY_NAME/$DOCKER_IMAGE:$DOCKER_TAG"
            docker push "$REGISTRY_NAME/$DOCKER_IMAGE:$DOCKER_TAG"
            log_success "Image pushed to $REGISTRY_NAME"
        fi
    else
        log_error "Docker image build failed (exit $build_rc)."
        log_error "errno 5 / Input/output error, read-only filesystem, or SIGBUS"
        log_error "indicates Docker Desktop/WSL storage failure."
        log_error "Do not use apt --fix-missing or apt-get -f install to repair Docker storage errors."
        log_error "Recovery: quit Docker Desktop, run 'wsl --shutdown' from PowerShell, then restart Docker Desktop."
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
    
    # Always flatten the final image with docker export.  Manually unpacking
    # containerd layer tarballs is unnecessary and is more fragile with the
    # Docker Desktop containerd image store.
    log_info "Flattening final image with docker export..."
    rm -rf "$ROOTFS_DIR"/*
    local container_name="chimera-export-${BASHPID}"
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    docker create --name "$container_name" "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null

    set +e
    docker export "$container_name" > "$BUILD_DIR/chimera-rootfs.tar"
    local export_rc=$?
    local tar_rc=1
    if [ "$export_rc" -eq 0 ]; then
        tar -xpf "$BUILD_DIR/chimera-rootfs.tar" -C "$ROOTFS_DIR"
        tar_rc=$?
    fi
    rm -f "$BUILD_DIR/chimera-rootfs.tar"
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
# INTEGRATE APACHE SOFTWARE FOUNDATION ECOSYSTEM
# =============================================================================

prepare_apache_ecosystem() {
    print_header "STEP 3: INTEGRATING APACHE SOFTWARE FOUNDATION ECOSYSTEM"

    if [ "$APACHE_ECOSYSTEM" -ne 1 ]; then
        log_info "Apache ecosystem integration disabled."
        return 0
    fi

    local apache_src="$SCRIPT_DIR/services/apache"
    local apache_root="$ROOTFS_DIR/opt/chimera/apache"
    local apache_cache="$ROOTFS_DIR/var/cache/chimera/apache"
    local apache_cfg="$ROOTFS_DIR/etc/chimera/apache-ecosystem.conf"

    if [ ! -d "$apache_src" ]; then
        log_warning "services/apache is not present; skipping Apache ecosystem integration."
        return 0
    fi

    mkdir -p "$apache_root" "$apache_cache" "$(dirname "$apache_cfg")"

    # Ship the Apache package-manager/control plane into the ISO. The ISO
    # contains metadata and installers rather than hundreds of third-party
    # release archives. Official source/binary artifacts are resolved at
    # installation time and remain subject to ASF release verification.
    for f in apache-projects.json README.md apache-sync.py; do
        if [ -f "$apache_src/$f" ]; then
            install -m 0644 "$apache_src/$f" "$apache_root/$f"
        fi
    done

    for f in install-apache-ecosystem.sh verify-apache-package.sh; do
        if [ -f "$apache_src/$f" ]; then
            install -m 0755 "$apache_src/$f" "$ROOTFS_DIR/usr/bin/$f"
        fi
    done

    if [ -f "$SCRIPT_DIR/system/security/apache-sandbox.json" ]; then
        mkdir -p "$ROOTFS_DIR/usr/share/chimera/config"
        install -m 0644 "$SCRIPT_DIR/system/security/apache-sandbox.json"             "$ROOTFS_DIR/usr/share/chimera/config/apache-sandbox.json"
    fi

    cat > "$apache_cfg" <<EOF
# Chimera II OS Apache Software Foundation ecosystem
CHIMERA_APACHE_PREFIX=/opt/chimera/apache
CHIMERA_APACHE_CACHE=/var/cache/chimera/apache
CHIMERA_APACHE_CATALOG=/opt/chimera/apache/apache-projects.json
CHIMERA_APACHE_PROJECT_INDEX=https://projects.apache.org/json/projects/
CHIMERA_APACHE_RELEASE_INDEX=https://downloads.apache.org/
CHIMERA_APACHE_ARTIFACT_POLICY=official-releases-only
CHIMERA_APACHE_VERIFY_SHA256=1
CHIMERA_APACHE_VERIFY_PGP=1
CHIMERA_APACHE_ALLOW_SNAPSHOT=0
CHIMERA_APACHE_MODE=$APACHE_ECOSYSTEM_MODE
EOF

    cat > "$apache_root/ISO-INTEGRATION.json" <<EOF
{
  "component": "Apache Software Foundation ecosystem",
  "mode": "$APACHE_ECOSYSTEM_MODE",
  "catalog": "https://projects.apache.org/json/projects/",
  "release_source": "https://downloads.apache.org/",
  "artifact_policy": "official-releases-only",
  "kernel_boundary": "Apache components run as userland services and libraries; never linked into Koronos"
}
EOF

    # Refresh the complete generated ASF project catalog when Python is
    # available. The bundled metadata remains usable for offline builds.
    if [ "$APACHE_ECOSYSTEM_MODE" = "metadata" ] && command -v python3 >/dev/null 2>&1; then
        log_info "Refreshing complete ASF project catalog metadata..."
        if CHIMERA_APACHE_PREFIX="$apache_root"            CHIMERA_APACHE_CACHE="$apache_cache"            CHIMERA_APACHE_PROJECT_INDEX="https://projects.apache.org/json/projects/"            CHIMERA_APACHE_RELEASE_INDEX="https://downloads.apache.org/"            python3 "$apache_src/apache-sync.py" catalog            >/tmp/chimera-apache-refresh.log 2>&1; then
            log_success "Complete ASF project catalog staged in ISO rootfs."
        else
            log_warning "ASF catalog refresh failed; bundled catalog retained."
            cat /tmp/chimera-apache-refresh.log >&2 || true
        fi
        rm -f /tmp/chimera-apache-refresh.log
    else
        log_warning "python3 unavailable; using bundled Apache project catalog."
    fi

    log_success "Apache ecosystem integration prepared: $apache_root"
    log_info "The ISO ships the ASF catalog/package-manager boundary; release archives are not copied wholesale."
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
    print_header "STEP 5: CREATING BIOS + UEFI ISO"
    local iso_file="${SCRIPT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    command -v grub-mkrescue >/dev/null || { log_error "grub-mkrescue is required."; exit 1; }
    command -v xorriso >/dev/null || { log_error "xorriso is required."; exit 1; }
    test -s "$ISO_DIR/boot/kernel.bin" || { log_error "ISO kernel linkage missing: /boot/kernel.bin"; exit 1; }
    test -s "$ISO_DIR/boot/koronos/koronos.elf" || { log_error "ISO Koronos payload missing."; exit 1; }
    test -s "$ISO_DIR/boot/spitfire/spitfire-stage2.bin" || { log_error "ISO Spit Fire stage2 missing."; exit 1; }
    grep -q "multiboot2 /boot/kernel.bin" "$ISO_DIR/boot/grub/grub.cfg" || { log_error "GRUB is not linked to the kernel stub."; exit 1; }
    grep -q "background_image /boot/grub/aurora-wayland-glass.png" "$ISO_DIR/boot/grub/grub.cfg" || { log_error "Aurora GRUB background is not configured."; exit 1; }
    grub-mkrescue -o "$iso_file" "$ISO_DIR"
    test -s "$iso_file"
    sha256sum "$iso_file" > "${iso_file}.sha256"
    log_success "BIOS + UEFI ISO created: $iso_file"
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
    print_header "CREATING BOOT MENU, KERNEL HANDOFF AND BOOT ARTWORK"
    mkdir -p "$ISO_DIR/boot/grub" "$ISO_DIR/boot/koronos" "$ISO_DIR/boot/jasper" "$ISO_DIR/boot/spitfire" "$ISO_DIR/EFI/BOOT" "$ISO_DIR/install"

    log_info "Building Koronos Multiboot2 kernel payload..."
    "$SCRIPT_DIR/kernel/build-koronos.sh"
    local kernel="$SCRIPT_DIR/build/koronos/x86_64/koronos.elf"
    test -s "$kernel" || { log_error "Koronos kernel ELF was not produced."; exit 1; }
    grub-file --is-x86-multiboot2 "$kernel"
    cp "$kernel" "$ISO_DIR/boot/kernel.bin"
    cp "$kernel" "$ISO_DIR/boot/koronos/koronos.elf"

    log_info "Building linked Spit Fire BIOS stages..."
    "$SCRIPT_DIR/boot/spitfire/build-spitfire.sh" "$BUILD_DIR/bootloaders" "$kernel"
    for f in spitfire-sf0-mbr.bin spitfire-stage2.bin spitfire-sf1-longmode.o spitfire-sf2-loader.o; do
        test -s "$BUILD_DIR/bootloaders/$f" || { log_error "Missing Spit Fire artifact: $f"; exit 1; }
        cp "$BUILD_DIR/bootloaders/$f" "$ISO_DIR/boot/spitfire/"
    done

    cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$GRUB_DIR/grub.cfg"
    cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$ISO_DIR/boot/grub.cfg"
    cat > "$GRUB_DIR/grub-early.cfg" <<EOF
insmod all_video
insmod gfxterm
insmod png
insmod normal
insmod search
insmod search_fs_file
insmod multiboot2
configfile /boot/grub/grub.cfg
EOF
    cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$ISO_DIR/boot/jasper/grub.cfg"
    cat > "$ISO_DIR/boot/jasper/recovery.cfg" <<EOF
set timeout=5
set default=0
insmod normal
insmod gfxterm
insmod png
if [ -f /boot/jasper/background.png ]; then background_image /boot/jasper/background.png; fi
menuentry "Jasper Recovery — Koronos Rescue" { multiboot2 /boot/kernel.bin chm.mode=recovery chm.recovery=1; boot }
menuentry "Jasper Recovery — Safe Graphics" { multiboot2 /boot/kernel.bin chm.mode=safe-graphics; boot }
menuentry "Jasper Recovery — GRUB Command Line" { commandline }
menuentry "Jasper Recovery — Reboot" { reboot }
menuentry "Jasper Recovery — Power Off" { halt }
EOF

    cp "$kernel" "$ISO_DIR/boot/kernel.bin"
    cp "$kernel" "$ISO_DIR/boot/koronos/koronos.elf"
    cp "$BUILD_DIR/bootloaders/spitfire-sf0-mbr.bin" "$ISO_DIR/boot/spitfire/"
    cp "$BUILD_DIR/bootloaders/spitfire-stage2.bin" "$ISO_DIR/boot/spitfire/"

    rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/boot/splash/aurora_boot_splash.svg" -o "$ISO_DIR/boot/grub/aurora-wayland-glass.png"
    rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/boot/splash/jasper_background.svg" -o "$ISO_DIR/boot/jasper/background.png"
    rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/boot/splash/spitfire_background.svg" -o "$ISO_DIR/boot/spitfire/background.png"
    rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/desktop/aurora/assets/aurora-installer.svg" -o "$ISO_DIR/install/installer-background.png"
    rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/desktop/aurora/assets/aurora-library.svg" -o "$ISO_DIR/install/library-background.png"
    log_success "Kernel, Spit Fire, Jasper and Aurora artwork staged."
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
        prepare_apache_ecosystem
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
