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
#   --background FILE   Use FILE as the boot/installer/desktop background
#   --storage-auto      Automatically select a larger mounted drive when space is insufficient
#   --storage PATH      Use PATH as the large-build storage/output root
#   --no-storage-prompt Never prompt; fail with actionable storage diagnostics
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
BUILD_DIR="${CHIMERA_BUILD_DIR:-${SCRIPT_DIR}/build}"
DOCKER_DIR="${BUILD_DIR}/docker"
ISO_DIR="${BUILD_DIR}/iso"
SQUASHFS_DIR="${BUILD_DIR}/squashfs"
BOOT_DIR="${ISO_DIR}/boot"
GRUB_DIR="${BOOT_DIR}/grub"
ROOTFS_DIR="${CHIMERA_ROOTFS_DIR:-${ISO_DIR}/rootfs}"
# Keep GRUB/mtools/xorriso scratch files on a native Linux filesystem (critical
# for WSL /mnt/c builds). The final ISO can be redirected to a larger filesystem
# with CHIMERA_ISO_OUTPUT_DIR when the repository drive is space constrained.
ISO_OUTPUT_DIR="${CHIMERA_ISO_OUTPUT_DIR:-$SCRIPT_DIR}"
ISO_TMP_DIR="${CHIMERA_ISO_TMPDIR:-/tmp/chimera-iso-build}"
mkdir -p "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"
export TMPDIR="$ISO_TMP_DIR"
export MTOOLS_SKIP_CHECK=1

# Flags
BUILD_DOCKER=1
BUILD_ISO=1
PUSH_REGISTRY=0
REGISTRY_NAME=""
APACHE_ECOSYSTEM=1
APACHE_ECOSYSTEM_MODE="${CHIMERA_APACHE_ECOSYSTEM:-metadata}"
BUILD_STATE_FILE="${CHIMERA_BUILD_STATE_FILE:-${BUILD_DIR}/.chimera-build-state}"
FAILED_STAGE_FILE="${CHIMERA_FAILED_STAGE_FILE:-${BUILD_DIR}/.chimera-failed-stage}"
RESUME_BUILD="${CHIMERA_RESUME:-0}"
CURRENT_STAGE=""
BUILD_SUCCEEDED=0
CLEAN_BUILD_STATE=0
STORAGE_AUTO="${CHIMERA_STORAGE_AUTO:-0}"
STORAGE_PROMPT="${CHIMERA_STORAGE_PROMPT:-1}"
LARGE_ISO_BUILD="${CHIMERA_LARGE_ISO_BUILD:-1}"
STORAGE_MIN_FREE_GIB="${CHIMERA_STORAGE_MIN_FREE_GIB:-20}"
ISO_RESERVE_GIB="${CHIMERA_ISO_RESERVE_GIB:-4}"
STORAGE_REQUIRED_BYTES=0
DOCKER_STORAGE_ROOT=""
DOCKER_STORAGE_FREE_BYTES=0

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
        --background)
            [[ -n "${2:-}" ]] || { echo "--background requires an image path"; exit 1; }
            CHIMERA_AURORA_ASSET="$2"
            export CHIMERA_AURORA_ASSET
            shift 2
            ;;
        --resume)
            RESUME_BUILD=1
            shift
            ;;
        --clean-state)
            CLEAN_BUILD_STATE=1
            shift
            ;;
        --storage-auto)
            STORAGE_AUTO=1
            shift
            ;;
        --storage)
            [[ -n "${2:-}" ]] || { echo "--storage requires a path"; exit 1; }
            CHIMERA_BUILD_STORAGE_ROOT="$2"
            export CHIMERA_BUILD_STORAGE_ROOT
            shift 2
            ;;
        --no-storage-prompt)
            STORAGE_PROMPT=0
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Apply an explicitly requested storage root before any build directories are created.
if [[ -n "${CHIMERA_BUILD_STORAGE_ROOT:-}" ]]; then
    BUILD_DIR="${CHIMERA_BUILD_STORAGE_ROOT%/}/chimera-build"
    DOCKER_DIR="$BUILD_DIR/docker"
    ISO_DIR="$BUILD_DIR/iso"
    SQUASHFS_DIR="$BUILD_DIR/squashfs"
    BOOT_DIR="$ISO_DIR/boot"
    GRUB_DIR="$BOOT_DIR/grub"
    ROOTFS_DIR="$BUILD_DIR/rootfs"
    ISO_OUTPUT_DIR="${CHIMERA_BUILD_STORAGE_ROOT%/}/chimera-output"
    BUILD_STATE_FILE="$BUILD_DIR/.chimera-build-state"
    export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR"
fi

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

# =============================================================================
# LARGE-BUILD STORAGE / DOCKER / WSL DISCOVERY
# =============================================================================

is_wsl() {
    grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null || [[ -n "${WSL_INTEROP:-}" ]] || [[ -d /mnt/wsl ]]
}

human_bytes() {
    numfmt --to=iec "$1" 2>/dev/null || echo "$1 bytes"
}

path_free_bytes() {
    df -PB1 "$1" 2>/dev/null | awk 'NR==2 {print $4}'
}

path_free_gib() {
    local b="$(path_free_bytes "$1")"
    [[ "$b" =~ ^[0-9]+$ ]] && echo $((b / 1024 / 1024 / 1024)) || echo 0
}

path_size_bytes() {
    local p="$1"
    if [[ -f "$p" ]]; then
        stat -c%s "$p" 2>/dev/null || stat -f%z "$p" 2>/dev/null || echo 0
    else
        du -sb "$p" 2>/dev/null | awk '{print $1}'
    fi
}

detect_docker_desktop_vhdx() {
    is_wsl || return 0
    local user_dir vhdx
    for user_dir in /mnt/c/Users/*; do
        [[ -d "$user_dir" ]] || continue
        vhdx="$user_dir/AppData/Local/Docker/wsl/disk/docker_data.vhdx"
        [[ -f "$vhdx" ]] || continue
        printf '%s|%s|%s\n' "$vhdx" "$(path_free_bytes "$user_dir")" "$(path_size_bytes "$vhdx")"
    done
}

detect_wsl_distro_vhdx() {
    is_wsl || return 0
    local user_dir vhdx
    for user_dir in /mnt/c/Users/*; do
        [[ -d "$user_dir" ]] || continue
        for vhdx in "$user_dir"/AppData/Local/Packages/*/LocalState/ext4.vhdx; do
            [[ -f "$vhdx" ]] || continue
            printf '%s|%s|%s\n' "$vhdx" "$(path_free_bytes "$user_dir")" "$(path_size_bytes "$vhdx")"
        done
    done
}

detect_docker_storage() {
    DOCKER_STORAGE_ROOT=""
    DOCKER_STORAGE_FREE_BYTES=0
    command -v docker >/dev/null 2>&1 || return 0
    DOCKER_STORAGE_ROOT="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)"
    if [[ -n "$DOCKER_STORAGE_ROOT" ]]; then
        DOCKER_STORAGE_FREE_BYTES="$(path_free_bytes "$DOCKER_STORAGE_ROOT")"
        log_info "Docker engine root: $DOCKER_STORAGE_ROOT"
        [[ "$DOCKER_STORAGE_FREE_BYTES" =~ ^[0-9]+$ ]] &&
            log_info "Docker engine filesystem free: $(human_bytes "$DOCKER_STORAGE_FREE_BYTES")"
    fi
    if is_wsl; then
        local rows
        rows="$(detect_docker_desktop_vhdx || true)"
        if [[ -n "$rows" ]]; then
            log_info "Docker Desktop WSL VHDX:"
            while IFS='|' read -r path host_free vhdx_size; do
                printf '  %s  host-free=%s  vhdx-size=%s\n' "$path" "$(human_bytes "$host_free")" "$(human_bytes "$vhdx_size")"
            done <<< "$rows"
        fi
    fi
}

apply_storage_root() {
    local root="$1"
    [[ -d "$root" ]] || { log_error "Storage root does not exist: $root"; return 1; }
    BUILD_DIR="$root/chimera-build"
    DOCKER_DIR="$BUILD_DIR/docker"
    ISO_DIR="$BUILD_DIR/iso"
    SQUASHFS_DIR="$BUILD_DIR/squashfs"
    BOOT_DIR="$ISO_DIR/boot"
    GRUB_DIR="$BOOT_DIR/grub"
    ROOTFS_DIR="$BUILD_DIR/rootfs"
    ISO_OUTPUT_DIR="$root/chimera-output"
    BUILD_STATE_FILE="$BUILD_DIR/.chimera-build-state"
    export CHIMERA_BUILD_DIR="$BUILD_DIR"
    export CHIMERA_ROOTFS_DIR="$ROOTFS_DIR"
    export CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR"
    mkdir -p "$BUILD_DIR" "$DOCKER_DIR" "$ISO_DIR" "$SQUASHFS_DIR" "$ROOTFS_DIR" "$ISO_OUTPUT_DIR"
}
discover_wsl_drives() {
    is_wsl || return 0
    for d in /mnt/*; do
        [[ -d "$d" ]] || continue
        local name="${d#/mnt/}"
        [[ "$name" =~ ^[a-zA-Z0-9._-]+$ ]] || continue
        local free="$(path_free_gib "$d")"
        (( free > 0 )) && printf '%s|%s\n' "$free" "$d"
    done | sort -t'|' -nr
}

discover_native_mounts() {
    local mounts
    mounts="$(findmnt -rn -o TARGET,FSTYPE 2>/dev/null || true)"
    while IFS=' ' read -r target fstype; do
        [[ -n "$target" && "$target" != /proc* && "$target" != /sys* && "$target" != /dev* && "$target" != /run* ]] || continue
        case "$fstype" in
            ext4|ext3|xfs|btrfs|zfs|ntfs|ntfs3|exfat|fuseblk) ;;
            *) continue ;;
        esac
        local free="$(path_free_gib "$target")"
        (( free > 0 )) && printf '%s|%s\n' "$free" "$target"
    done <<< "$mounts" | sort -t'|' -nr -u
}

show_storage_inventory() {
    print_header "CHIMERA LARGE-BUILD STORAGE INVENTORY"
    log_info "WSL detected: $(is_wsl && echo yes || echo no)"
    log_info "Repository: $SCRIPT_DIR ($(path_free_gib "$SCRIPT_DIR") GiB free)"
    log_info "Rootfs: $ROOTFS_DIR ($(path_free_gib "$ROOTFS_DIR") GiB free)"
    log_info "ISO output: $ISO_OUTPUT_DIR ($(path_free_gib "$ISO_OUTPUT_DIR") GiB free)"
    detect_docker_storage
    if command -v docker >/dev/null 2>&1; then
        docker system df 2>/dev/null || true
    fi
    if is_wsl; then
        log_info "Mounted WSL/Windows drives with free space:"
        discover_wsl_drives | while IFS='|' read -r free path; do
            printf '  %6s GiB  %s\n' "$free" "$path"
        done
        local wsl_vhdx
        wsl_vhdx="$(detect_wsl_distro_vhdx || true)"
        if [[ -n "$wsl_vhdx" ]]; then
            log_info "WSL distro virtual disks:"
            while IFS='|' read -r path host_free vhdx_size; do
                printf '  %s  host-free=%s  vhdx-size=%s\n' "$path" "$(human_bytes "$host_free")" "$(human_bytes "$vhdx_size")"
            done <<< "$wsl_vhdx"
        fi
    else
        log_info "Candidate native build mounts:"
        discover_native_mounts | while IFS='|' read -r free path; do
            printf '  %6s GiB  %s\n' "$free" "$path"
        done
    fi
}

choose_larger_storage() {
    local reason="${1:-insufficient build storage}"
    local required_bytes="${2:-$STORAGE_REQUIRED_BYTES}"
    [[ "$required_bytes" =~ ^[0-9]+$ ]] || required_bytes=0
    show_storage_inventory
    local candidates=""
    if is_wsl; then
        candidates="$(discover_wsl_drives || true)"
    else
        candidates="$(discover_native_mounts || true)"
    fi

    local best=""
    while IFS='|' read -r free path; do
        [[ "$free" =~ ^[0-9]+$ ]] || continue
        (( free >= STORAGE_MIN_FREE_GIB )) || continue
        if (( required_bytes > 0 && free * 1024 * 1024 * 1024 < required_bytes )); then continue; fi
        [[ "$path" != "/" && "$path" != "$SCRIPT_DIR" ]] || continue
        if [[ -z "$best" ]]; then best="$path"; fi
    done <<< "$candidates"

    if [[ "$STORAGE_AUTO" = "1" && -n "$best" ]]; then
        log_warning "$reason"
        log_info "Automatically selecting larger build drive: $best"
        apply_storage_root "$best"
        log_success "Large-build storage switched to $best"
        return 0
    fi

    if [[ "$STORAGE_PROMPT" = "1" && -t 0 ]]; then
        echo ""
        log_warning "Chimera needs more storage for the large ISO build."
        echo "Enter another mounted drive/path, or press Enter to abort."
        read -r -p "Storage path: " answer
        if [[ -n "$answer" && -d "$answer" ]]; then
            local free free_bytes
            free="$(path_free_gib "$answer")"
            free_bytes="$(path_free_bytes "$answer")"
            if [[ "$free_bytes" =~ ^[0-9]+$ ]] && (( free >= STORAGE_MIN_FREE_GIB )) && (( required_bytes == 0 || free_bytes >= required_bytes )); then
                apply_storage_root "$answer"
                log_success "Using user-selected storage: $answer"
                return 0
            fi
            log_error "Selected path has only $free GiB free; need at least $STORAGE_MIN_FREE_GIB GiB."
        fi
    fi

    log_error "No sufficiently large storage location was selected."
    log_error "Use --storage /mnt/d or CHIMERA_ROOTFS_DIR/CHIMERA_ISO_OUTPUT_DIR."
    return 1
}

detect_docker_storage_pressure() {
    command -v docker >/dev/null 2>&1 || return 0
    local root usage
    root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)"
    usage="$(docker system df --format '{{.Size}}' 2>/dev/null | head -n 20 || true)"
    [[ -n "$root" ]] && log_info "Docker storage root: $root"
    if docker info 2>&1 | grep -Eqi 'no space left on device|read-only|input/output error|SIGBUS'; then
        log_error "Docker reports a storage-layer failure."
        log_error "Docker Desktop stores its WSL engine data in its configured disk image location; move/expand that disk in Docker Desktop rather than copying its VHDX manually."
        if [[ "$STORAGE_PROMPT" = "1" && -t 0 ]]; then
            echo "A larger build drive can be selected now, but Docker Desktop own disk image may also need to be moved/expanded."
            if ! choose_larger_storage "Docker engine storage is unhealthy or full."; then
                return 1
            fi
        fi
        return 1
    fi
    [[ -n "$usage" ]] && log_info "Docker storage usage summary available."
    return 0
}

preflight_large_build_storage() {
    print_header "LARGE ISO / DOCKER / WSL STORAGE PREFLIGHT"
    show_storage_inventory

    mkdir -p "$ROOTFS_DIR" "$ISO_OUTPUT_DIR"
    local root_free iso_free
    root_free="$(path_free_gib "$ROOTFS_DIR")"
    iso_free="$(path_free_gib "$ISO_OUTPUT_DIR")"

    if (( root_free < STORAGE_MIN_FREE_GIB )); then
        choose_larger_storage "Rootfs staging filesystem has only $root_free GiB free." || return 1
        root_free="$(path_free_gib "$ROOTFS_DIR")"
    fi
    if (( iso_free < STORAGE_MIN_FREE_GIB )); then
        choose_larger_storage "ISO output filesystem has only $iso_free GiB free." || return 1
        iso_free="$(path_free_gib "$ISO_OUTPUT_DIR")"
    fi

    if is_wsl; then
        log_info "WSL2 storage detected. Native Linux staging/output is preferred over /mnt/c for heavy filesystem operations."
    fi
    detect_docker_storage_pressure || return 1
    mkdir -p "$ROOTFS_DIR" "$ISO_OUTPUT_DIR"
}

# =============================================================================
# RESUMABLE BUILD STATE
# =============================================================================


build_state_get() {
    if [[ -f "$BUILD_STATE_FILE" ]]; then
        sed -n "s/^completed=//p" "$BUILD_STATE_FILE" | tail -n 1
        return 0
    fi
    # Backward-compatible recovery: builds performed before checkpoints were
    # introduced can still resume from the artifacts left by a failed stage.
    if [[ -s "$ISO_DIR/live/filesystem.squashfs" && -s "$ISO_DIR/boot/kernel.bin" && -s "$ISO_DIR/boot/live/chimera-live-initramfs.img" && -s "$ISO_DIR/boot/live/live-manifest.json" ]]; then
        log_info "No checkpoint file found; detected completed SquashFS stage from existing artifacts." >&2
        echo "squashfs"
        return 0
    fi
    if [[ -d "$ROOTFS_DIR" && -e "$ROOTFS_DIR/etc/os-release" ]]; then
        log_info "No checkpoint file found; detected completed rootfs export from existing staging tree." >&2
        echo "rootfs"
        return 0
    fi
    return 0
}

build_state_mark() {
    local stage="$1"
    mkdir -p "$(dirname "$BUILD_STATE_FILE")"
    cat > "$BUILD_STATE_FILE" <<EOF
schema=1
completed=$stage
updated=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
    log_info "Build checkpoint saved: $stage"
}
build_state_reset() {
    rm -f "$BUILD_STATE_FILE" "$FAILED_STAGE_FILE"
}

build_state_failure_record() {
    local rc="$1"
    local failed_stage="${CURRENT_STAGE:-unknown}"
    mkdir -p "$(dirname "$FAILED_STAGE_FILE")"
    cat > "$FAILED_STAGE_FILE" <<EOF
schema=1
failed_stage=$failed_stage
exit_code=$rc
updated=$(date -u +%Y-%m-%dT%H:%M:%SZ)
completed=$(build_state_get 2>/dev/null || true)
EOF
}

build_failure_trap() {
    local rc="$?"
    if (( rc != 0 )) && (( BUILD_SUCCEEDED == 0 )); then
        build_state_failure_record "$rc" || true
        log_error "Build stopped during stage: ${CURRENT_STAGE:-preflight}"
        log_error "Checkpoint retained at: $BUILD_STATE_FILE"
        log_error "Failure record: $FAILED_STAGE_FILE"
        log_error "Re-run with --resume to continue from the last completed checkpoint."
    fi
    return "$rc"
}

run_checkpointed_stage() {
    local stage="$1"
    local fn="$2"
    CURRENT_STAGE="$stage"
    log_info "Starting resumable stage: $stage"
    "$fn"
    build_state_mark "$stage"
    CURRENT_STAGE=""
}

build_state_done() {
    local completed="${1:-}" target="$2"
    case "$target" in
        docker) [[ "$completed" == "docker" || "$completed" == "rootfs" || "$completed" == "boot" || "$completed" == "branding" || "$completed" == "apache" || "$completed" == "features" || "$completed" == "squashfs" || "$completed" == "iso" || "$completed" == "verify" || "$completed" == "report" ]] ;;
        rootfs) [[ "$completed" == "rootfs" || "$completed" == "boot" || "$completed" == "branding" || "$completed" == "apache" || "$completed" == "features" || "$completed" == "squashfs" || "$completed" == "iso" || "$completed" == "verify" || "$completed" == "report" ]] ;;
        boot) [[ "$completed" == "boot" || "$completed" == "branding" || "$completed" == "apache" || "$completed" == "features" || "$completed" == "squashfs" || "$completed" == "iso" || "$completed" == "verify" || "$completed" == "report" ]] ;;
        branding) [[ "$completed" == "branding" || "$completed" == "apache" || "$completed" == "features" || "$completed" == "squashfs" || "$completed" == "iso" || "$completed" == "verify" || "$completed" == "report" ]] ;;
        apache) [[ "$completed" == "apache" || "$completed" == "features" || "$completed" == "squashfs" || "$completed" == "iso" || "$completed" == "verify" || "$completed" == "report" ]] ;;
        features) [[ "$completed" == "features" || "$completed" == "squashfs" || "$completed" == "iso" || "$completed" == "verify" || "$completed" == "report" ]] ;;
        squashfs) [[ "$completed" == "squashfs" || "$completed" == "iso" || "$completed" == "verify" || "$completed" == "report" ]] ;;
        iso) [[ "$completed" == "iso" || "$completed" == "verify" || "$completed" == "report" ]] ;;
        verify) [[ "$completed" == "verify" || "$completed" == "report" ]] ;;
        report) [[ "$completed" == "report" ]] ;;
        *) return 1 ;;
    esac
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
    # Optional application toolchains are non-fatal, but the comprehensive
    # ISO should install every toolchain available in the configured host
    # repositories before catalog/CMake validation. The dependency helper
    # performs targeted fallbacks for Java, Rust, Node/npm, and .NET.
    if [ "${CHIMERA_INSTALL_OPTIONAL_DEPS:-1}" = "1" ]; then
        local optional_toolchains=(javac java rustc cargo node npm dotnet)
        local unavailable_toolchains=()
        local tool
        for tool in "${optional_toolchains[@]}"; do
            if ! command -v "$tool" >/dev/null 2>&1; then
                unavailable_toolchains+=("$tool")
            fi
        done
        if [ "${#unavailable_toolchains[@]}" -gt 0 ]; then
            log_warning "Optional toolchains still unavailable after dependency installation: ${unavailable_toolchains[*]}"
            log_info "Affected catalog applications remain source-integrated and use runtime/provider fallbacks."
        else
            log_success "Optional application toolchains ready: Java/Rust/Node/npm/.NET"
        fi
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
    local required_tools=("docker" "mktemp" "mount" "unsquashfs" "mksquashfs" "xorriso" "grub-mkrescue" "grub-file" "cpio" "file" "busybox" "numfmt" "nasm" "g++" "ld")
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
    local build_log="/tmp/chimera-docker-build.log"
    : > "$build_log"
    for attempt in $(seq 1 "$DOCKER_RETRIES"); do
        log_info "Docker build attempt $attempt/$DOCKER_RETRIES"
        set +e
        docker build "${docker_build_flags[@]}" \
            -f "$SCRIPT_DIR/Dockerfile.comprehensive" \
            -t "$DOCKER_IMAGE:$DOCKER_TAG" \
            -t "$DOCKER_IMAGE:latest" \
            "$SCRIPT_DIR" 2>&1 | tee "$build_log"
        build_rc="${PIPESTATUS[0]}"
        set -e
        [ "$build_rc" -eq 0 ] && break

        # Only classify a failure as Docker/WSL storage corruption when the
        # actual build log contains storage-specific signatures. npm/HTTP/DNS
        # failures are application-network failures and must not be mislabeled
        # as errno 5/SIGBUS.
        if grep -Eqi 'input/output error|read-only file system|read-only filesystem|SIGBUS|no space left on device|failed to mount|overlay.*(error|fail)' "$build_log"; then
            log_error "Docker build log contains a storage/overlayfs failure signature."
            log_error "Check Docker Desktop/WSL storage before retrying."
        elif grep -Eqi 'npm ERR!.*network|ECONNRESET|ETIMEDOUT|EAI_AGAIN|ENOTFOUND|fetch failed' "$build_log"; then
            log_warning "Docker build failed in npm/network access; storage preflight is not being blamed."
        fi

        if [ "$attempt" -lt "$DOCKER_RETRIES" ]; then
            log_warning "Build failed; running a Docker storage write test before retry."
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
        if grep -Eqi 'input/output error|read-only file system|read-only filesystem|SIGBUS|no space left on device|failed to mount|overlay.*(error|fail)' "$build_log"; then
            log_error "Detected Docker Desktop/WSL storage or overlayfs failure."
            log_error "Do not use apt --fix-missing or apt-get -f install to repair Docker storage."
            log_error "Recovery: quit Docker Desktop, run 'wsl --shutdown' from PowerShell, then restart Docker Desktop."
        elif grep -Eqi 'npm ERR!.*network|ECONNRESET|ETIMEDOUT|EAI_AGAIN|ENOTFOUND|fetch failed' "$build_log"; then
            log_error "Detected npm/network failure. Check DNS/proxy/registry connectivity from Docker."
        else
            log_error "Build failure was not identified as a Docker storage failure; inspect: $build_log"
        fi
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

    # Stream docker export directly into tar. The old implementation first
    # created a complete chimera-rootfs.tar and then extracted it, temporarily
    # requiring space for BOTH the archive and the uncompressed rootfs.
    # That caused "tar: var/tmp: Cannot mkdir: No space left on device" on
    # large Chimera images.
    log_info "Preparing streamed Docker rootfs export..."

    local image_size_bytes
    image_size_bytes="$(docker image inspect --format='{{.Size}}' "$DOCKER_IMAGE:$DOCKER_TAG" 2>/dev/null || echo 0)"
    if [[ ! "$image_size_bytes" =~ ^[0-9]+$ ]] || [ "$image_size_bytes" -le 0 ]; then
        log_error "Unable to determine Docker image size for rootfs storage preflight."
        exit 1
    fi

    local rootfs_free_bytes
    rootfs_free_bytes="$(df -PB1 "$ROOTFS_DIR" | awk 'NR==2 {print $4}')"
    local rootfs_required_bytes=$((image_size_bytes + image_size_bytes / 4 + 2*1024*1024*1024))
    log_info "Docker image filesystem size: $(numfmt --to=iec "$image_size_bytes" 2>/dev/null || echo "$image_size_bytes bytes")"
    log_info "Rootfs staging free space: $(numfmt --to=iec "$rootfs_free_bytes" 2>/dev/null || echo "$rootfs_free_bytes bytes")"
    log_info "Rootfs staging safety requirement: $(numfmt --to=iec "$rootfs_required_bytes" 2>/dev/null || echo "$rootfs_required_bytes bytes")"

    if [ "$rootfs_free_bytes" -lt "$rootfs_required_bytes" ]; then
        log_warning "Insufficient space for Docker rootfs extraction."
        log_warning "Required: $(numfmt --to=iec "$rootfs_required_bytes" 2>/dev/null || echo "$rootfs_required_bytes bytes"); available: $(numfmt --to=iec "$rootfs_free_bytes" 2>/dev/null || echo "$rootfs_free_bytes bytes")."
        STORAGE_REQUIRED_BYTES="$rootfs_required_bytes"
        if ! choose_larger_storage "Docker rootfs staging filesystem is too small." "$rootfs_required_bytes"; then
            log_error "Set CHIMERA_ROOTFS_DIR=/path/on/a/larger-drive and retry."
            exit 1
        fi
        rootfs_free_bytes="$(df --output=avail -B1 "$ROOTFS_DIR" | tail -n 1 | tr -d "[:space:]")"
        if [ "$rootfs_free_bytes" -lt "$rootfs_required_bytes" ]; then
            log_error "Selected rootfs filesystem is still too small."
            exit 1
        fi
    fi

    rm -rf "$ROOTFS_DIR"/*
    local container_name="chimera-export-${BASHPID}"
    docker rm -f "$container_name" >/dev/null 2>&1 || true
    docker create --name "$container_name" "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null

    set +e
    docker export "$container_name" | tar -xpf - -C "$ROOTFS_DIR"
    local pipe_status=( "${PIPESTATUS[@]}" )
    local export_rc="${pipe_status[0]:-1}"
    local tar_rc="${pipe_status[1]:-1}"
    set -e

    docker rm -f "$container_name" >/dev/null 2>&1 || true

    if [ "$export_rc" -ne 0 ] || [ "$tar_rc" -ne 0 ] || [ ! -d "$ROOTFS_DIR/bin" ]; then
        log_error "Docker image export or rootfs extraction failed."
        log_error "docker export status: $export_rc; tar extraction status: $tar_rc"
        log_error "The rootfs staging filesystem filled or Docker export failed."
        local remaining_bytes
        remaining_bytes="$(df -PB1 "$ROOTFS_DIR" | awk 'NR==2 {print $4}')"
        log_error "Rootfs staging free space after failure: $(numfmt --to=iec "$remaining_bytes" 2>/dev/null || echo "$remaining_bytes bytes")"
        rm -rf "$ROOTFS_DIR"/*
        log_error "If Docker also reports read-only filesystem/Input/output error/SIGBUS, repair Docker Desktop/WSL storage before retrying."
        exit 1
    fi

    log_success "Rootfs exported successfully (streamed; no intermediate rootfs tar created)"
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
# STAGE COMPREHENSIVE CHIMERA II OS FEATURES
# =============================================================================

stage_comprehensive_features() {
    print_header "STAGING COMPREHENSIVE CHIMERA II OS FEATURES"
    mkdir -p "$ISO_DIR/boot/chimera" "$ISO_DIR/system" "$ISO_DIR/system/branding" \
             "$ISO_DIR/system/commands" "$ISO_DIR/system/shell" "$ISO_DIR/system/display" \
             "$ISO_DIR/opt/chimera" "$ISO_DIR/desktop" "$ISO_DIR/network" "$ISO_DIR/mobile" \
             "$ISO_DIR/drivers" "$ISO_DIR/toolchains" "$ISO_DIR/install"

    copy_tree_if_present() {
        local src="$1" dst="$2"
        [[ -d "$src" ]] || return 0
        mkdir -p "$dst"
        cp -a "$src/." "$dst/"
    }

    copy_tree_if_present "$SCRIPT_DIR/services" "$ISO_DIR/system/services"
    copy_tree_if_present "$SCRIPT_DIR/userland" "$ISO_DIR/system/userland"
    copy_tree_if_present "$SCRIPT_DIR/desktop" "$ISO_DIR/desktop"
    if [[ -f "$SCRIPT_DIR/system/services/chimera-hardware-driver-autoscan.service" ]]; then
        mkdir -p "$ROOTFS_DIR/etc/systemd/system" "$ROOTFS_DIR/etc/systemd/system/multi-user.target.wants"
        install -m 0644 "$SCRIPT_DIR/system/services/chimera-hardware-driver-autoscan.service" "$ROOTFS_DIR/etc/systemd/system/"
        ln -sf ../chimera-hardware-driver-autoscan.service "$ROOTFS_DIR/etc/systemd/system/multi-user.target.wants/chimera-hardware-driver-autoscan.service"
    fi
    if [[ -f "$SCRIPT_DIR/system/services/chimera-gpu-driver-autoscan.service" ]]; then
        mkdir -p "$ROOTFS_DIR/etc/systemd/system"
        install -m 0644 "$SCRIPT_DIR/system/services/chimera-gpu-driver-autoscan.service" "$ROOTFS_DIR/etc/systemd/system/"
        mkdir -p "$ROOTFS_DIR/etc/systemd/system/multi-user.target.wants"
        ln -sf ../chimera-gpu-driver-autoscan.service "$ROOTFS_DIR/etc/systemd/system/multi-user.target.wants/chimera-gpu-driver-autoscan.service"
    fi
    if [[ -d "$SCRIPT_DIR/desktop/aurora" ]]; then
        mkdir -p "$ROOTFS_DIR/usr/share/applications"
        for f in "$SCRIPT_DIR"/desktop/aurora/*.desktop; do
            [[ -f "$f" ]] && install -m 0644 "$f" "$ROOTFS_DIR/usr/share/applications/"
        done
        for f in display_settings.json gpu_driver_settings.json context_actions.json driver_panel.json; do
            [[ -f "$SCRIPT_DIR/desktop/aurora/$f" ]] && install -m 0644 "$SCRIPT_DIR/desktop/aurora/$f" "$ROOTFS_DIR/usr/share/chimera/"
        done
    fi
    copy_tree_if_present "$SCRIPT_DIR/network" "$ISO_DIR/network"
    copy_tree_if_present "$SCRIPT_DIR/installer" "$ISO_DIR/install/installer-source"
    copy_tree_if_present "$BUILD_DIR/mobile" "$ISO_DIR/mobile"
    copy_tree_if_present "$BUILD_DIR/drivers" "$ISO_DIR/drivers"
    if [[ -f "$SCRIPT_DIR/drivers/audio-driver-manifest.json" && -f "$SCRIPT_DIR/drivers/hardware-driver-policy.json" && -f "$SCRIPT_DIR/drivers/hardware-driver-catalog.json" ]]; then
        mkdir -p "$ROOTFS_DIR/usr/share/chimera/drivers" "$ROOTFS_DIR/usr/bin" "$ISO_DIR/drivers"
        install -m 0644 "$SCRIPT_DIR/drivers/audio-driver-manifest.json" "$ROOTFS_DIR/usr/share/chimera/drivers/"
        install -m 0644 "$SCRIPT_DIR/drivers/hardware-driver-policy.json" "$ROOTFS_DIR/usr/share/chimera/drivers/"
        install -m 0644 "$SCRIPT_DIR/drivers/hardware-driver-catalog.json" "$ROOTFS_DIR/usr/share/chimera/drivers/"
        install -m 0644 "$SCRIPT_DIR/drivers/audio-driver-manifest.json" "$ISO_DIR/drivers/"
        install -m 0644 "$SCRIPT_DIR/drivers/hardware-driver-policy.json" "$ISO_DIR/drivers/"
        install -m 0644 "$SCRIPT_DIR/drivers/hardware-driver-catalog.json" "$ISO_DIR/drivers/"
        install -m 0755 "$SCRIPT_DIR/tools/drivers/chimera-hardware-drivers" "$ROOTFS_DIR/usr/bin/chimera-hardware-drivers"
        install -m 0755 "$SCRIPT_DIR/tools/drivers/chimera-driver-panel.py" "$ROOTFS_DIR/usr/bin/chimera-driver-panel.py"
        install -m 0755 "$SCRIPT_DIR/tools/drivers/chimera-hardware-drivers" "$ISO_DIR/drivers/chimera-hardware-drivers"
        install -m 0755 "$SCRIPT_DIR/tools/drivers/chimera-driver-panel.py" "$ISO_DIR/drivers/chimera-driver-panel.py"
    fi
    copy_tree_if_present "$BUILD_DIR/toolchains" "$ISO_DIR/toolchains"
    copy_tree_if_present "$BUILD_DIR/network-tools" "$ISO_DIR/network-tools"
    copy_tree_if_present "$SCRIPT_DIR/system/security" "$ISO_DIR/boot/chimera/security"

    # Refresh the SS64 command-name catalog before staging it. The crawler stores
    # command names, platform/category, and source URLs only; it does not copy
    # SS64 prose. A network failure never destroys an existing checked-in catalog.
    local cmd_catalog="$SCRIPT_DIR/system/commands/chimera-command-list.json"
    local ss64_catalog="$SCRIPT_DIR/system/commands/ss64-command-catalog.json"
    local ss64_tool="$SCRIPT_DIR/tools/commands/crawl_ss64.py"
    if command -v python3 >/dev/null 2>&1 && [[ -f "$ss64_tool" ]]; then
        log_info "Refreshing SS64 command catalog..."
        if python3 "$ss64_tool" \
            --output "$ss64_catalog" \
            --max-pages "${CHIMERA_SS64_MAX_PAGES:-3000}" \
            --timeout "${CHIMERA_SS64_TIMEOUT:-30}" \
            --retries "${CHIMERA_SS64_RETRIES:-2}" \
            --delay "${CHIMERA_SS64_DELAY:-0.05}" \
            >"$ISO_TMP_DIR/ss64-crawl.log" 2>&1; then
            log_success "SS64 command catalog refreshed: $ss64_catalog"
        else
            log_warning "SS64 catalog refresh failed; retaining the existing catalog."
            cat "$ISO_TMP_DIR/ss64-crawl.log" >&2 || true
        fi
        rm -f "$ISO_TMP_DIR/ss64-crawl.log"
    fi

    # Install the Linux/Bash compatibility catalog and native Chimera command list.
    # SS64 is used as a compatibility reference; its prose is not redistributed.
    local arabic_catalog="$SCRIPT_DIR/system/commands/chimera-arabic.json"
    local cmd_tool="$SCRIPT_DIR/tools/runtime/chimera-command.py"
    local shell_integration="$SCRIPT_DIR/system/shell/chimera-shell.sh"
    local background_tool="$SCRIPT_DIR/tools/branding/chimera-background"
    local display_tool="$SCRIPT_DIR/tools/display/chimera-display"
    local display_gui="$SCRIPT_DIR/tools/display/chimera-display-settings.py"
    local gpu_driver_tool="$SCRIPT_DIR/tools/display/chimera-gpu-driver-manager"
    local desktop_action="$SCRIPT_DIR/tools/display/chimera-desktop-action"
    if [[ -f "$cmd_catalog" && -f "$cmd_tool" ]]; then
        mkdir -p "$ROOTFS_DIR/usr/share/chimera/commands" "$ROOTFS_DIR/usr/bin" "$ROOTFS_DIR/etc/profile.d" "$ISO_DIR/system/commands" "$ISO_DIR/system/shell"
        install -m 0644 "$cmd_catalog" "$ROOTFS_DIR/usr/share/chimera/commands/chimera-command-list.json"
        install -m 0755 "$cmd_tool" "$ROOTFS_DIR/usr/bin/chimera"
        install -m 0644 "$cmd_catalog" "$ISO_DIR/system/commands/chimera-command-list.json"
        install -m 0755 "$cmd_tool" "$ISO_DIR/system/commands/chimera-command"
        if [[ -f "$arabic_catalog" ]]; then
            install -m 0644 "$arabic_catalog" "$ROOTFS_DIR/usr/share/chimera/commands/chimera-arabic.json"
            install -m 0644 "$arabic_catalog" "$ISO_DIR/system/commands/chimera-arabic.json"
        fi
        local ss64_catalog="$SCRIPT_DIR/system/commands/ss64-command-catalog.json"
        if [[ -f "$ss64_catalog" ]]; then
            install -m 0644 "$ss64_catalog" "$ROOTFS_DIR/usr/share/chimera/commands/ss64-command-catalog.json"
        elif [[ -s "$ROOTFS_DIR/opt/chimera/share/chimera/commands/ss64-command-catalog.json" ]]; then
            install -m 0644 "$ROOTFS_DIR/opt/chimera/share/chimera/commands/ss64-command-catalog.json" "$ROOTFS_DIR/usr/share/chimera/commands/ss64-command-catalog.json"
            ss64_catalog="$ROOTFS_DIR/usr/share/chimera/commands/ss64-command-catalog.json"
        fi
        if [[ -f "$ss64_catalog" ]]; then
            install -m 0644 "$ss64_catalog" "$ISO_DIR/system/commands/ss64-command-catalog.json"
        fi
        if [[ -f "$shell_integration" ]]; then
            install -m 0644 "$shell_integration" "$ROOTFS_DIR/etc/profile.d/chimera-shell.sh"
            install -m 0644 "$shell_integration" "$ISO_DIR/system/shell/chimera-shell.sh"
        fi
        if [[ -f "$background_tool" ]]; then
            install -m 0755 "$background_tool" "$ROOTFS_DIR/usr/bin/chimera-background"
            install -m 0755 "$background_tool" "$ISO_DIR/system/branding/chimera-background"
        fi
        if [[ -f "$display_tool" && -f "$display_gui" && -f "$gpu_driver_tool" ]]; then
            install -m 0755 "$display_tool" "$ROOTFS_DIR/usr/bin/chimera-display"
            install -m 0755 "$display_gui" "$ROOTFS_DIR/usr/bin/chimera-display-settings.py"
            install -m 0755 "$gpu_driver_tool" "$ROOTFS_DIR/usr/bin/chimera-gpu-driver-manager"
            [[ -f "$desktop_action" ]] && install -m 0755 "$desktop_action" "$ROOTFS_DIR/usr/bin/chimera-desktop-action"
            mkdir -p "$ISO_DIR/system/display"
            install -m 0755 "$display_tool" "$ISO_DIR/system/display/chimera-display"
            install -m 0755 "$display_gui" "$ISO_DIR/system/display/chimera-display-settings.py"
            install -m 0755 "$gpu_driver_tool" "$ISO_DIR/system/display/chimera-gpu-driver-manager"
            [[ -f "$desktop_action" ]] && install -m 0755 "$desktop_action" "$ISO_DIR/system/display/chimera-desktop-action"
        fi
        cat > "$ROOTFS_DIR/usr/share/chimera/commands/README.md" <<CMDREADME
# Chimera II OS command catalog

`chimera commands` lists the Linux/Bash compatibility catalog.
`chimera native` lists native Chimera II OS control-plane commands.
`chimera search TERM` searches both catalogs.
`chimera help COMMAND` shows command classification.
`chimera exec COMMAND ...` explicitly executes a command available in PATH.

The Linux catalog is based on the public SS64 Bash/Linux command index and
is maintained as command names/categories rather than copied SS64 prose.
CMDREADME
        log_success "Linux/Bash compatibility and native Chimera command catalog staged."
    else
        log_warning "Chimera command catalog source files are missing; skipping command integration."
    fi

    # Canonical boot-manager configuration and recovery contracts.
    mkdir -p "$ISO_DIR/boot/jasper" "$ISO_DIR/boot/spitfire" "$ISO_DIR/boot/installation" "$ISO_DIR/boot/recovery" "$ISO_DIR/boot/diagnostics"
    for f in "$SCRIPT_DIR"/boot/jasper/*.cfg; do [[ -f "$f" ]] && cp -f "$f" "$ISO_DIR/boot/jasper/"; done
    [[ -f "$SCRIPT_DIR/boot/spitfire/spitfire-menu.cfg" ]] && cp -f "$SCRIPT_DIR/boot/spitfire/spitfire-menu.cfg" "$ISO_DIR/boot/spitfire/"
    [[ -f "$SCRIPT_DIR/boot/installation/menu.cfg" ]] && cp -f "$SCRIPT_DIR/boot/installation/menu.cfg" "$ISO_DIR/boot/installation/"
    [[ -f "$SCRIPT_DIR/boot/recovery/recovery-manifest.json" ]] && cp -f "$SCRIPT_DIR/boot/recovery/recovery-manifest.json" "$ISO_DIR/boot/recovery/"
    [[ -f "$SCRIPT_DIR/boot/diagnostics/diagnostics-manifest.json" ]] && cp -f "$SCRIPT_DIR/boot/diagnostics/diagnostics-manifest.json" "$ISO_DIR/boot/diagnostics/"

    for f in \
        boot/boot_protocol.json boot/boot-menu-contract.json \
        boot/startup/boot_phase_manifest.json \
        installer/installation_phases.json installer/installer_profiles.json \
        installer/chimera-installer-plan.json; do
        [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$ISO_DIR/boot/chimera/"
    done

    if [[ -d "$BUILD_DIR/boot-artifacts/runtime" ]]; then
        cp -a "$BUILD_DIR/boot-artifacts/runtime/." "$ISO_DIR/opt/chimera/"
    fi

    for f in \
        desktop/aurora/assets/aurora-wayland-glass.svg \
        desktop/aurora/assets/aurora-installer.svg \
        desktop/aurora/assets/aurora-library.svg \
        desktop/aurora/assets/aurora-desktop.svg \
        boot/splash/aurora_boot_splash.svg \
        boot/splash/jasper_background.svg \
        boot/splash/spitfire_background.svg; do
        [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$ISO_DIR/boot/chimera/"
    done

    for f in \
        "$ISO_DIR/boot/grub/aurora-wayland-glass.png" \
        "$ISO_DIR/boot/jasper/background.png" \
        "$ISO_DIR/boot/spitfire/background.png" \
        "$ISO_DIR/install/installer-background.png" \
        "$ISO_DIR/install/library-background.png"; do
        test -s "$f" || { log_error "Required Aurora artwork missing: $f"; exit 1; }
    done

    cat > "$ISO_DIR/boot/chimera/feature-manifest.json" <<EOF
{
  "schema": "CHM-ISO-FEATURES-2026-1",
  "kernel": "/boot/koronos/koronos.elf",
  "kernel_protocol": "Multiboot2",
  "native_boot_chain": ["Spit Fire", "Jasper", "GRUB2", "Koronos"],
  "firmware": ["BIOS", "UEFI"],
  "boot_artifacts": ["/boot/chimera/elf", "/boot/chimera/bin"],
  "live": {
    "initramfs": "/boot/live/chimera-live-initramfs.img",
    "manifest": "/boot/live/live-manifest.json"
  },
  "desktop": "Aurora Wayland",
  "features": [
    "screen-saver", "auto-lock", "battery-optimizer",
    "Active-Directory", "local-users", "root-superuser",
    "passwd-shadow", "filesystem-permissions", "Linux-security",
    "Cockpit-style-web-administration", "Spotnik-networking",
    "Nucleus-Hive-Kore-Aegis", "Apache-ecosystem",
    "mobile-editions", "toolchains", "compatibility-layers", "display-resolution", "multi-monitor", "gpu-driver-auto-detection", "signed-driver-repositories"
  ]
}
EOF
    log_success "Comprehensive feature payload and Aurora artwork staged."
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

        # IMPORTANT: ROOTFS is only the staging tree used to create the
        # compressed live filesystem. Never leave it inside the ISO tree.
        # Leaving it here duplicates the entire uncompressed OS inside the
        # ISO, can add hundreds of thousands of files, and can exhaust the
        # host filesystem while xorriso is mastering the image.
        log_info "Removing uncompressed rootfs staging tree from ISO payload..."
        rm -rf "$ROOTFS_DIR"
        if [ -e "$ROOTFS_DIR" ]; then
            log_error "Failed to remove uncompressed rootfs staging tree: $ROOTFS_DIR"
            exit 1
        fi

        local iso_payload_bytes
        iso_payload_bytes="$(du -sb "$ISO_DIR" | awk '{print $1}')"
        log_info "Final ISO staging payload after rootfs removal: $(numfmt --to=iec "$iso_payload_bytes" 2>/dev/null || echo "$iso_payload_bytes bytes")"
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
    local iso_file="${ISO_OUTPUT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    command -v grub-mkrescue >/dev/null || { log_error "grub-mkrescue is required."; exit 1; }
    command -v xorriso >/dev/null || { log_error "xorriso is required."; exit 1; }

    # xorriso writes the ISO to the same filesystem as SCRIPT_DIR. A build
    # can have "10 GB free" and still fail if the staging tree is larger than
    # that. Check this before spending time mastering the image.
    local payload_bytes free_bytes required_bytes
    payload_bytes="$(du -sb "$ISO_DIR" | awk '{print $1}')"
    free_bytes="$(df -PB1 "$ISO_OUTPUT_DIR" | awk 'NR==2 {print $4}')"
    required_bytes=$((payload_bytes + 256*1024*1024))
    log_info "ISO payload: $(numfmt --to=iec "$payload_bytes" 2>/dev/null || echo "$payload_bytes bytes")"
    log_info "Filesystem free: $(numfmt --to=iec "$free_bytes" 2>/dev/null || echo "$free_bytes bytes")"
    if [ "$free_bytes" -lt "$required_bytes" ]; then
        log_warning "Insufficient filesystem space for ISO mastering."
        log_warning "Need at least $(numfmt --to=iec "$required_bytes" 2>/dev/null || echo "$required_bytes bytes"), have $(numfmt --to=iec "$free_bytes" 2>/dev/null || echo "$free_bytes bytes")."
        STORAGE_REQUIRED_BYTES="$required_bytes"
        if ! choose_larger_storage "ISO mastering filesystem is full or too small." "$required_bytes"; then
            log_error "Use --storage /mnt/d or CHIMERA_ISO_OUTPUT_DIR=/path/to/a/larger/filesystem."
            exit 1
        fi
        free_bytes="$(df --output=avail -B1 "$ISO_OUTPUT_DIR" | tail -n 1 | tr -d "[:space:]")"
        if [ "$free_bytes" -lt "$required_bytes" ]; then
            log_error "Selected ISO output filesystem is still too small."
            exit 1
        fi
    fi

    test -s "$ISO_DIR/boot/kernel.bin" || { log_error "ISO kernel linkage missing: /boot/kernel.bin"; exit 1; }
    test -s "$ISO_DIR/boot/koronos/koronos.elf" || { log_error "ISO Koronos payload missing."; exit 1; }
    test -s "$ISO_DIR/boot/spitfire/spitfire-stage2.bin" || { log_error "ISO Spit Fire stage2 missing."; exit 1; }
    grep -Eq "multiboot2 /boot/(koronos/koronos\\.elf|kernel\\.bin)" "$ISO_DIR/boot/grub/grub.cfg" || { log_error "GRUB is not linked to the Koronos Multiboot2 kernel."; exit 1; }
    grep -q "background_image /boot/grub/aurora-wayland-glass.png" "$ISO_DIR/boot/grub/grub.cfg" || { log_error "Aurora GRUB background is not configured."; exit 1; }
    test -s "$ISO_DIR/boot/live/chimera-live-initramfs.img" || { log_error "Live initramfs missing."; exit 1; }
    test -s "$ISO_DIR/boot/live/live-manifest.json" || { log_error "Live manifest missing."; exit 1; }
    grep -q "/boot/live/chimera-live-initramfs.img" "$ISO_DIR/boot/grub/grub.cfg" || { log_error "GRUB live initramfs linkage missing."; exit 1; }
    grep -q "/boot/live/live-manifest.json" "$ISO_DIR/boot/grub/grub.cfg" || { log_error "GRUB live manifest linkage missing."; exit 1; }
    # grub-mkrescue passes ordinary unrecognized arguments to xorriso's
    # mkisofs-emulation mode. Do NOT place these after --: that switches
    # xorriso to native command mode, where -iso-level is not a command.
    local xorriso_opts=(-iso-level 3 -J -R -V "CHIMERA_II_OS")
    log_info "Mastering large-capacity BIOS + UEFI ISO with ISO9660 Level 3..."
    grub-mkrescue -o "$iso_file" "$ISO_DIR" "${xorriso_opts[@]}"
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
    
    local iso_file="${ISO_OUTPUT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    
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

    log_info "Building complete native boot artifact set (Spit Fire + Jasper + GRUB + Koronos)..."
    bash "$SCRIPT_DIR/tools/build-boot-artifacts.sh"
    local boot_art="$BUILD_DIR/boot-artifacts"
    test -s "$boot_art/jasper/jasper.elf" || { log_error "Jasper ELF was not produced."; exit 1; }
    mkdir -p "$ISO_DIR/boot/chimera/elf" "$ISO_DIR/boot/chimera/bin" "$ISO_DIR/boot/chimera/manifests"
    cp -a "$boot_art/all-elf/." "$ISO_DIR/boot/chimera/elf/" 2>/dev/null || true
    cp -a "$boot_art/all-bin/." "$ISO_DIR/boot/chimera/bin/" 2>/dev/null || true
    cp -a "$boot_art/manifests/." "$ISO_DIR/boot/chimera/manifests/" 2>/dev/null || true
    cp "$boot_art/jasper/jasper.elf" "$ISO_DIR/boot/jasper/jasper.elf"
    for f in spitfire-sf0-mbr.bin spitfire-stage2.bin spitfire-sf1-longmode.o spitfire-sf2-loader.o; do
        test -s "$boot_art/spitfire/$f" || { log_error "Missing Spit Fire artifact: $f"; exit 1; }
        cp "$boot_art/spitfire/$f" "$ISO_DIR/boot/spitfire/"
    done

    cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$GRUB_DIR/grub.cfg"
    cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$ISO_DIR/boot/grub.cfg"

    log_info "Building live-boot payload..."
    bash "$SCRIPT_DIR/tools/build-live-boot-binaries.sh"
    local live_boot="$BUILD_DIR/live-boot"
    for f in "$live_boot/boot/live/chimera-live-initramfs.img" "$live_boot/boot/live/live-manifest.json" "$live_boot/boot/koronos/koronos.elf"; do
        test -s "$f" || { log_error "Missing live boot artifact: $f"; exit 1; }
    done
    mkdir -p "$ISO_DIR/boot/live"
    cp "$live_boot/boot/live/chimera-live-initramfs.img" "$ISO_DIR/boot/live/"
    cp "$live_boot/boot/live/live-manifest.json" "$ISO_DIR/boot/live/"
    cp "$live_boot/boot/koronos/koronos.elf" "$ISO_DIR/boot/koronos/koronos.elf"
    [[ -s "$live_boot/boot/vmlinuz" ]] && cp "$live_boot/boot/vmlinuz" "$ISO_DIR/boot/live/vmlinuz" || true
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
    local rasterizer=""
    if command -v rsvg-convert >/dev/null 2>&1; then
        rasterizer="rsvg-convert"
    elif command -v convert >/dev/null 2>&1; then
        rasterizer="convert"
    else
        log_error "Aurora artwork requires rsvg-convert or ImageMagick convert."
        exit 2
    fi
    if [[ "$rasterizer" == "rsvg-convert" ]]; then
        rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/boot/splash/aurora_boot_splash.svg" -o "$ISO_DIR/boot/grub/aurora-wayland-glass.png"
        rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/boot/splash/jasper_background.svg" -o "$ISO_DIR/boot/jasper/background.png"
        rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/boot/splash/spitfire_background.svg" -o "$ISO_DIR/boot/spitfire/background.png"
        rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/desktop/aurora/assets/aurora-installer.svg" -o "$ISO_DIR/install/installer-background.png"
        rsvg-convert -w 1920 -h 1080 "$SCRIPT_DIR/desktop/aurora/assets/aurora-library.svg" -o "$ISO_DIR/install/library-background.png"
    else
        convert -background none "$SCRIPT_DIR/boot/splash/aurora_boot_splash.svg" "$ISO_DIR/boot/grub/aurora-wayland-glass.png"
        convert -background none "$SCRIPT_DIR/boot/splash/jasper_background.svg" "$ISO_DIR/boot/jasper/background.png"
        convert -background none "$SCRIPT_DIR/boot/splash/spitfire_background.svg" "$ISO_DIR/boot/spitfire/background.png"
        convert -background none "$SCRIPT_DIR/desktop/aurora/assets/aurora-installer.svg" "$ISO_DIR/install/installer-background.png"
        convert -background none "$SCRIPT_DIR/desktop/aurora/assets/aurora-library.svg" "$ISO_DIR/install/library-background.png"
    fi

    # If the user supplies the Aurora-Wayland-Glass desktop image, use that
    # exact artwork across every boot/installer surface. Repository SVGs remain
    # deterministic fallbacks for unattended builds.
    if [[ -f "$SCRIPT_DIR/tools/branding/stage-aurora-image.sh" ]]; then
        bash "$SCRIPT_DIR/tools/branding/stage-aurora-image.sh" "$ISO_DIR" || log_warning "Supplied Aurora artwork could not be staged; keeping SVG backgrounds."
    fi
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
    
    # Create build directories before state handling so --resume can continue
    # without rebuilding completed Docker/rootfs/boot stages.
    mkdir -p "$BUILD_DIR" "$DOCKER_DIR" "$ISO_DIR" "$ISO_DIR/live" "$ISO_DIR/boot"
    if [ "$CLEAN_BUILD_STATE" -eq 1 ]; then
        log_info "Removing resumable Chimera build state."
        build_state_reset
    elif [[ -f "$BUILD_STATE_FILE" ]]; then
        # A previous failed invocation leaves its checkpoint intact. Resume by
        # default so a simple re-run continues instead of rebuilding everything.
        RESUME_BUILD=1
        log_info "Existing Chimera checkpoint detected; automatic resume enabled."
    fi
    local completed_stage=""
    if [ "$RESUME_BUILD" -eq 1 ]; then
        completed_stage="$(build_state_get || true)"
        if [ -n "$completed_stage" ]; then
            log_info "Resuming after completed stage: $completed_stage"
        else
            log_info "No prior checkpoint found; starting at the first stage."
        fi
    fi

    preflight_large_build_storage

    check_requirements

    if [ "$BUILD_ISO" -eq 0 ]; then
        check_docker_storage
        if ! build_state_done "$completed_stage" docker; then
            build_docker_image
            build_state_mark docker
            completed_stage="docker"
        else
            log_info "Docker stage already completed; skipping."
        fi
        cleanup
        print_header "DOCKER BUILD COMPLETED SUCCESSFULLY"
        return 0
    fi

    if ! build_state_done "$completed_stage" rootfs; then
        check_docker_storage
        if ! build_state_done "$completed_stage" docker; then
            build_docker_image
            build_state_mark docker
            completed_stage="docker"
        else
            log_info "Docker image stage already completed; skipping."
        fi
        export_docker_to_rootfs
        build_state_mark rootfs
        completed_stage="rootfs"
    fi

    if ! build_state_done "$completed_stage" boot; then run_checkpointed_stage boot create_boot_menu; completed_stage="boot"; fi
    if ! build_state_done "$completed_stage" branding; then run_checkpointed_stage branding add_branding; completed_stage="branding"; fi
    if ! build_state_done "$completed_stage" apache; then run_checkpointed_stage apache prepare_apache_ecosystem; completed_stage="apache"; fi
    if ! build_state_done "$completed_stage" features; then run_checkpointed_stage features stage_comprehensive_features; completed_stage="features"; fi
    if ! build_state_done "$completed_stage" squashfs; then run_checkpointed_stage squashfs create_squashfs; completed_stage="squashfs"; fi
    if ! build_state_done "$completed_stage" iso; then run_checkpointed_stage iso create_iso_image; completed_stage="iso"; fi
    if ! build_state_done "$completed_stage" verify; then run_checkpointed_stage verify verify_iso; completed_stage="verify"; fi
    if ! build_state_done "$completed_stage" report; then run_checkpointed_stage report generate_report; completed_stage="report"; fi

    cleanup
    BUILD_SUCCEEDED=1
    build_state_reset
    print_header "BUILD COMPLETED SUCCESSFULLY"
    log_success "ISO file ready at: ${ISO_OUTPUT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    log_info "Build report: ${SCRIPT_DIR}/build-report.txt"
    echo ""
}

# Preserve checkpoints across failures. A later invocation automatically resumes
# when a valid build-state file exists, while --clean-state explicitly starts over.
trap build_failure_trap EXIT

# Execute main
main