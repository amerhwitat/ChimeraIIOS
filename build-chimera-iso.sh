#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: build-chimera-iso.sh

Usage:
  build-chimera-iso.sh [options] [arguments]

Options:
  -h, --help                  Show this help and exit successfully.
  --verbose, --debug          Emit detailed stage diagnostics (default).
  --quiet                     Reduce console output; logs remain enabled.
  --resume, --resume-auto     Resume after the last recorded completed stage.
  --clean-state               Clear saved resume/failure state before building.
  --storage-auto, --auto-storage
                              Automatically select writable storage with >=20 GiB free.
  --no-storage-prompt         Fail instead of prompting when storage is insufficient.
  --storage PATH              Use PATH/chimera-build and PATH/chimera-output.
  --docker-only               Build/publish only the Docker image.
  --iso-only                  Build an ISO from an existing Docker image.
  --full                      Force a clean full build, including native SDK compilation/tests and ISO staging.
  --tag TAG                   Docker image tag (default: latest).
  --background PATH           Aurora background artwork asset.
  --skip-apache               Skip Apache ecosystem integration.
  --apache-ecosystem          Enable Apache ecosystem integration.
  --push / --no-push          Enable/disable Docker Hub image publishing.
  --registry NAME             Set the package registry name.
  --refresh-online-catalogs,
  --refresh-isa-catalog       Refresh online ISA/OS catalogs.
  --sync-dos-payloads         Fetch eligible DOS payloads for ISO staging.
  --skip-native-iso           Skip the additional native boot/ISO pipeline.
  --install-build-deps        Opt in to installing missing host build tools.

Environment:
  CHIMERA_BUILD_DIR, CHIMERA_ROOTFS_DIR, CHIMERA_ISO_OUTPUT_DIR,
  CHIMERA_BUILD_STORAGE_ROOT, CHIMERA_STORAGE_AUTO, CHIMERA_STORAGE_PROMPT,
  CHIMERA_BUILD_STATE_FILE, CHIMERA_FAILED_STAGE_FILE, CHIMERA_PUSH,
  CHIMERA_VERBOSE, CHIMERA_SQUASHFS_PROCESSORS and CHIMERA_* build controls.

Resume safety:
  Resume state is advisory. Use --clean-state to force a complete rebuild.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail

# Canonical system block-size contract shared by every boot and ISO stage.
# Default to 4096 bytes (4 KiB); honor an explicit canonical value or legacy
# alias only when the caller supplies one.
if [[ -z "${CHIMERA_SYSTEM_BLOCK_SIZE:-}" && -z "${SYSTEM_BLOCK_SIZE:-}" ]]; then
  printf '[INFO] No system block size supplied; defaulting to 4096 bytes (4 KiB).\n'
fi
CHIMERA_SYSTEM_BLOCK_SIZE="${CHIMERA_SYSTEM_BLOCK_SIZE:-${SYSTEM_BLOCK_SIZE:-4096}}"
if [[ ! "$CHIMERA_SYSTEM_BLOCK_SIZE" =~ ^[1-9][0-9]*$ ]]; then
  printf '[ERROR] CHIMERA_SYSTEM_BLOCK_SIZE must be a positive integer (got: %s)\n' "$CHIMERA_SYSTEM_BLOCK_SIZE" >&2
  exit 2
fi
# Export both names so all downstream scripts and legacy contract checks agree.
SYSTEM_BLOCK_SIZE="$CHIMERA_SYSTEM_BLOCK_SIZE"
export CHIMERA_SYSTEM_BLOCK_SIZE SYSTEM_BLOCK_SIZE

# CHIMERA_ROOTFS_EXPORT_V3
chimera_export_docker_rootfs() {
    local image="${1:-${CHIMERA_DOCKER_IMAGE:-${DOCKER_IMAGE:-}}}"
    local dest="${2:-${CHIMERA_ROOTFS_DIR:-${ROOTFS_DIR:-${ROOTFS:-}}}}"
    local work="${CHIMERA_ROOTFS_WORK:-/tmp/chimera-rootfs-work}"
    local cid='' tarball='' avail required=0 stage
    [[ -n "$image" ]] || { log_error "Docker image is not set for rootfs export."; return 1; }
    [[ -n "$dest" ]] || { log_error "Rootfs destination is not set; use CHIMERA_ROOTFS_DIR."; return 1; }
    command -v docker >/dev/null || { log_error "Docker CLI not found."; return 1; }
    command -v tar >/dev/null || { log_error "tar not found."; return 1; }
    docker image inspect "$image" >/dev/null 2>&1 || { log_error "Docker image does not exist: $image"; return 1; }
    mkdir -p "$work" "$dest"; chmod 0700 "$work"
    [[ -w "$dest" ]] || { log_error "Rootfs destination is not writable: $dest"; return 1; }
    required="$(docker image inspect -f '{{.Size}}' "$image" 2>/dev/null || echo 0)"; [[ "$required" =~ ^[0-9]+$ ]] || required=0
    required=$((required + 1073741824))
    avail="$(df -Pk "$work" | awk 'NR==2 {print $4*1024}')"; [[ "$avail" =~ ^[0-9]+$ ]] || avail=0
    (( required == 0 || avail >= required )) || { log_error "Insufficient WSL /tmp space: need about $required bytes, have $avail."; return 1; }
    rm -rf -- "$work/export" "$work/rootfs"
    mkdir -p "$work/export" "$work/rootfs"
    while read -r old; do [[ -z "$old" ]] || docker rm -f "$old" >/dev/null 2>&1 || true; done < <(docker ps -aq --filter 'label=chimera.rootfs.export=true')
    cid="$(docker create --label chimera.rootfs.export=true "$image")" || { log_error "docker create failed: $image"; return 1; }
    tarball="$work/export/rootfs.tar"
    log_info "Exporting $image -> $tarball"
    if ! docker export "$cid" -o "$tarball"; then
        docker logs "$cid" 2>&1 || true; docker rm -f "$cid" >/dev/null 2>&1 || true
        log_error "docker export failed"; return 1
    fi
    docker rm -f "$cid" >/dev/null 2>&1 || true; cid=''
    [[ -s "$tarball" ]] || { log_error "Docker export archive is empty: $tarball"; return 1; }
    log_info "Extracting rootfs on Linux-native WSL storage"
    tar --numeric-owner --xattrs --xattrs-include='*' --acls --same-permissions -xf "$tarball" -C "$work/rootfs" || { log_error "tar extraction failed; archive retained at $tarball"; return 1; }
    [[ -d "$work/rootfs/etc" ]] || { log_error "Invalid exported rootfs: /etc missing"; return 1; }
    stage="${dest}.chimera-new.$$"; rm -rf -- "$stage"; mkdir -p "$stage"
    cp -a -- "$work/rootfs/." "$stage/"
    rm -rf -- "$dest"; mv -- "$stage" "$dest"
    [[ -d "$dest/etc" ]] || { log_error "Final rootfs validation failed"; return 1; }
    rm -rf -- "$work/export" "$work/rootfs"
    log_info "Rootfs export completed: $dest"
}
type log_info >/dev/null 2>&1 || log_info(){ printf '[INFO] %s\n' "$*"; }
type log_error >/dev/null 2>&1 || log_error(){ printf '[ERROR] %s\n' "$*" >&2; }
# CHIMERA_ROOTFS_DIAGNOSTICS_V1
chimera_rootfs_err_report(){ local rc=$?; printf '[ERROR] rootfs command failed (rc=%s): %s\n' "$rc" "$BASH_COMMAND" >&2; return "$rc"; }


# Copy only when source and destination are different filesystem objects.
# This is intentionally used at every boot-artifact boundary so a build/output
# directory alias cannot trigger cp's "same file" failure.
chimera_copy_if_distinct() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  local src_real dst_real
  src_real="$(realpath -m "$src")"
  dst_real="$(realpath -m "$dst")"
  if [[ "$src_real" == "$dst_real" ]]; then
    echo "[CHIMERA] SKIP self-copy: $src_real"
    return 0
  fi
  cp -f -- "$src" "$dst"
}

# Chimera II OS comprehensive ISO builder.
# The SquashFS stage is deliberately non-append and transactionally replaces
# the final image only after a successful build. ISO generation uses
# grub-mkrescue so the resulting image contains GRUB BIOS + UEFI El Torito
# boot paths rather than merely being an ISO9660 data image.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
DOCKER_IMAGE="chimera2os-comprehensive"
DOCKER_TAG="${DOCKER_TAG:-latest}"
ISO_NAME="ChimeraIIOS-comprehensive"
ISO_VERSION="1.0.0"
BUILD_DIR="${CHIMERA_BUILD_DIR:-$SCRIPT_DIR/build}"
ISO_DIR="$BUILD_DIR/iso"
ROOTFS_DIR="${CHIMERA_ROOTFS_DIR:-$ISO_DIR/rootfs}"
ISO_OUTPUT_DIR="${CHIMERA_ISO_OUTPUT_DIR:-$SCRIPT_DIR}"
ISO_TMP_DIR="${CHIMERA_ISO_TMPDIR:-$BUILD_DIR/logs/chimera-iso-build}"
LOG_DIR="$BUILD_DIR/logs"
LOG_FALLBACK_DIR="${CHIMERA_LOG_FALLBACK_DIR:-${TMPDIR:-/tmp}/chimera-build-logs-${UID:-$(id -u)}}"
WATCHDOG_PID=""
STATE_FILE="${CHIMERA_BUILD_STATE_FILE:-$BUILD_DIR/.chimera-build-state}"
FAILED_FILE="${CHIMERA_FAILED_STAGE_FILE:-$BUILD_DIR/.chimera-failed-stage}"
RESUME_BUILD=0
CLEAN_STATE=0
STORAGE_AUTO="${CHIMERA_STORAGE_AUTO:-0}"
STORAGE_PROMPT="${CHIMERA_STORAGE_PROMPT:-1}"
CURRENT_STAGE=""
BUILD_SUCCEEDED=0
CHIMERA_PUSH="${CHIMERA_PUSH:-1}"
BUILD_DOCKER=1
BUILD_ISO=1
CHIMERA_VERBOSE="${CHIMERA_VERBOSE:-1}"
CHIMERA_CAPTURE_CONSOLE="${CHIMERA_CAPTURE_CONSOLE:-1}"

# Architecture-aware media profile. Current boot artifacts are x86_64-only.
detect_cpu_arch() {
  case "$(uname -m)" in
    x86_64|amd64) printf "x86_64\n" ;;
    aarch64|arm64) printf "aarch64\n" ;;
    i?86) printf "i386\n" ;;
    riscv64) printf "riscv64\n" ;;
    *) uname -m ;;
  esac
}
HOST_ARCH="$(detect_cpu_arch)"
TARGET_ARCH="${CHIMERA_TARGET_ARCH:-$HOST_ARCH}"
case "$TARGET_ARCH" in x86_64|aarch64|riscv64|i386) ;; *) log_error "Unsupported target CPU architecture: $TARGET_ARCH"; exit 2 ;; esac
MEDIA_FS_PROFILE="${CHIMERA_MEDIA_FS_PROFILE:-auto}"
case "$MEDIA_FS_PROFILE" in
  auto) MEDIA_FS_PROFILE="iso9660+squashfs" ;;
  iso9660+squashfs) ;;
  *) log_error "Unsupported media filesystem profile: $MEDIA_FS_PROFILE"; exit 2 ;;
esac
if [[ "$TARGET_ARCH" != "x86_64" ]]; then
  log_error "Target $TARGET_ARCH detected, but the current ISO boot pipeline supports x86_64 only."
  log_error "ARM64/mobile and RISC-V require matching Koronos, Jasper/Spit Fire, GRUB EFI, and boot verification before an ISO can be emitted."
  log_error "No mislabeled cross-architecture ISO will be produced."
  exit 2
fi
export CHIMERA_TARGET_ARCH="$TARGET_ARCH" CHIMERA_HOST_ARCH="$HOST_ARCH" CHIMERA_MEDIA_FS_PROFILE="$MEDIA_FS_PROFILE"

mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_DIR/boot/live" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR" 2>/dev/null || true

# WSL/DrvFs can expose a drive as read-only even when it reports ample free space.
# Never let logging/state writes turn the real Docker error into a secondary failure.
ensure_log_dir(){
  if ! mkdir -p "$LOG_DIR" 2>/dev/null || ! test -w "$LOG_DIR"; then
    LOG_DIR="$LOG_FALLBACK_DIR"
    mkdir -p "$LOG_DIR" 2>/dev/null || { echo "[ERROR] No writable build log directory; check WSL storage mounts." >&2; return 1; }
    echo "[CHIMERA] Build logs redirected to $LOG_DIR because the selected storage is not writable." >&2
  fi
}
ensure_log_dir
export TMPDIR="$ISO_TMP_DIR" MTOOLS_SKIP_CHECK=1

log_file(){ ensure_log_dir || return 0; printf "[%s] %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG_DIR/chimera-build.log" 2>/dev/null || true; }
log_info(){ printf "${BLUE}[%s INFO]${NC} %s\n" "$(date -u +%H:%M:%S)" "$*"; log_file "INFO $*"; }
log_success(){ printf "${GREEN}[%s SUCCESS]${NC} %s\n" "$(date -u +%H:%M:%S)" "$*"; log_file "SUCCESS $*"; }
log_warning(){ printf "${YELLOW}[%s WARNING]${NC} %s\n" "$(date -u +%H:%M:%S)" "$*"; log_file "WARNING $*"; }
log_error(){ printf "${RED}[%s ERROR]${NC} %s\n" "$(date -u +%H:%M:%S)" "$*" >&2; log_file "ERROR $*"; }
log_debug(){ [[ "$CHIMERA_VERBOSE" == 1 ]] || return 0; printf "[%s DEBUG] %s\n" "$(date -u +%H:%M:%S)" "$*"; log_file "DEBUG $*"; }
log_both(){ log_info "$*"; }

# Capture all child-tool output for post-failure diagnosis. Avoid `set -x`:
# shell tracing can disclose expanded registry tokens and other credentials.
if [[ "$CHIMERA_CAPTURE_CONSOLE" == 1 ]]; then
  BUILD_CONSOLE_LOG="$LOG_DIR/build-console.log"
  if touch "$BUILD_CONSOLE_LOG" 2>/dev/null; then
    exec > >(tee -a "$BUILD_CONSOLE_LOG") 2>&1
  else
    log_warning "Could not enable full console capture at $BUILD_CONSOLE_LOG"
  fi
fi
emit_build_diagnostics(){
  header 'VERBOSE HOST / TOOLCHAIN / SOURCE DIAGNOSTICS'
  log_info "UTC timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  log_info "Script: $SCRIPT_DIR/build-chimera-iso.sh"
  log_info "Build=$BUILD_DIR Rootfs=$ROOTFS_DIR ISO-stage=$ISO_DIR ISO-output=$ISO_OUTPUT_DIR Temp=$ISO_TMP_DIR"
  log_info "Host=$HOST_ARCH Target=$TARGET_ARCH Media=$MEDIA_FS_PROFILE Block-size=$CHIMERA_SYSTEM_BLOCK_SIZE"
  log_info "Verbose=$CHIMERA_VERBOSE Console-capture=$CHIMERA_CAPTURE_CONSOLE"
  log_info "Kernel: $(uname -srmo 2>/dev/null || uname -a)"
  log_info "Distribution: $(. /etc/os-release 2>/dev/null; printf '%s %s' "${PRETTY_NAME:-unknown}" "${VERSION_ID:-}")"
  log_info "CPU count: $(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc 2>/dev/null || echo unknown)"
  if command -v git >/dev/null 2>&1 && git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log_info "Source commit: $(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
    log_info "Source branch: $(git -C "$SCRIPT_DIR" branch --show-current 2>/dev/null || echo detached)"
    log_info "Worktree change rows: $(git -C "$SCRIPT_DIR" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  fi
  for tool in docker cmake ctest ninja make gcc g++ clang clang++ nasm yasm grub-mkrescue grub-script-check xorriso mksquashfs cpio busybox python3 rustc cargo go javac java dotnet node npm qemu-system-x86_64; do
    if command -v "$tool" >/dev/null 2>&1; then
      local version_line
      version_line="$("$tool" --version 2>&1 | head -n 1 || true)"
      log_debug "tool=$tool version=${version_line:-available} path=$(command -v "$tool")"
    else
      log_debug "tool=$tool unavailable"
    fi
  done
  for path in "$BUILD_DIR" "$ROOTFS_DIR" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"; do
    [[ -e "$path" ]] || mkdir -p "$path" 2>/dev/null || true
    log_info "Storage $path: $(df -h "$path" 2>/dev/null | awk 'NR==2 {print "size=" $2 " used=" $3 " free=" $4 " mount=" $6}')"
  done
  log_info "Console log: ${BUILD_CONSOLE_LOG:-disabled}; structured log: $LOG_DIR/chimera-build.log"
}

process_snapshot(){
  ensure_log_dir || return 0
  {
    echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) PROCESS SNAPSHOT ====="
    echo "-- host processes --"
    ps -eo pid,ppid,stat,%cpu,%mem,etime,comm --sort=-%cpu 2>/dev/null || true
    echo "-- process tree --"
    pstree -p "$" 2>/dev/null | head -n 80 || true
    echo "-- docker containers --"
    docker ps -a --no-trunc --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}' 2>/dev/null || true
    echo "-- docker disk usage --"
    docker system df 2>/dev/null || true
    echo "-- storage --"
    df -h "$BUILD_DIR" "$ISO_OUTPUT_DIR" 2>/dev/null || true
    echo "-- build directories --"
    du -sh "$BUILD_DIR"/* "$ISO_DIR"/* 2>/dev/null | sort -h | tail -n 20 || true
  } >> "$LOG_DIR/process-snapshots.log" 2>&1
}
start_watchdog(){
  stop_watchdog || true
  ensure_log_dir || return 0
  local label="$1" interval="${CHIMERA_BUILD_WATCHDOG_INTERVAL:-5}"
  (while :; do log_both "[WATCHDOG] $label still active"; process_snapshot; sleep "$interval"; done) &
  WATCHDOG_PID=$!
}
stop_watchdog(){
  if [[ -n "$WATCHDOG_PID" ]]; then kill "$WATCHDOG_PID" 2>/dev/null || true; wait "$WATCHDOG_PID" 2>/dev/null || true; WATCHDOG_PID=""; fi
}
header(){ printf '\n==================================================================\n%s\n==================================================================\n' "$*"; }

REFRESH_ONLINE_CATALOGS="${CHIMERA_REFRESH_ONLINE_CATALOGS:-0}"
DOS_FETCH_ON_BUILD="${CHIMERA_DOS_FETCH_ON_BUILD:-0}"
FULL_BUILD=0

require_option_value() {
  local option="$1" value="${2:-}"
  [[ -n "$value" && "$value" != --* ]] || { log_error "$option requires a value"; exit 2; }
}
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) sed -n '/^Chimera II OS script:/,/^CHIMERA_HELP$/p' "$0"; exit 0;;
    --refresh-online-catalogs|--refresh-isa-catalog) REFRESH_ONLINE_CATALOGS=1; shift;;
    --verbose|--debug) CHIMERA_VERBOSE=1; shift;;
    --quiet) CHIMERA_VERBOSE=0; shift;;
    --sync-dos-payloads) DOS_FETCH_ON_BUILD=1; shift;;
    --docker-only) BUILD_ISO=0; shift;;
    --iso-only) BUILD_DOCKER=0; shift;;
    --full) FULL_BUILD=1; RESUME_BUILD=0; CLEAN_STATE=1; export CHIMERA_FULL_BUILD=1 CHIMERA_BUILD_NATIVE_ISO_PIPELINE=1; shift;;
    --resume|--resume-auto) RESUME_BUILD=1; shift;;
    --clean-state) CLEAN_STATE=1; shift;;
    --storage-auto|--auto-storage) STORAGE_AUTO=1; shift;;
    --no-storage-prompt) STORAGE_PROMPT=0; shift;;
    --storage) require_option_value "$1" "${2:-}"; export CHIMERA_BUILD_STORAGE_ROOT="$2"; shift 2;;
    --tag) require_option_value "$1" "${2:-}"; DOCKER_TAG="$2"; shift 2;;
    --background) require_option_value "$1" "${2:-}"; export CHIMERA_AURORA_ASSET="$2"; shift 2;;
    --skip-apache) export APACHE_ECOSYSTEM=0; shift;;
    --apache-ecosystem) export APACHE_ECOSYSTEM=1; shift;;
    --push) export CHIMERA_PUSH=1; shift;;
    --no-push) export CHIMERA_PUSH=0; shift;;
    --skip-native-iso) export CHIMERA_BUILD_NATIVE_ISO_PIPELINE=0; shift;;
    --install-build-deps) export CHIMERA_INSTALL_BUILD_DEPS=1; shift;;
    --registry) require_option_value "$1" "${2:-}"; export REGISTRY_NAME="$2"; shift 2;;
    *) log_error "Unknown option: $1"; exit 2;;
  esac
done

if [[ "$FULL_BUILD" == 1 ]]; then
  # --full is an explicit complete-build request, regardless of option order.
  BUILD_DOCKER=1
  BUILD_ISO=1
  RESUME_BUILD=0
  CLEAN_STATE=1
  export CHIMERA_FULL_BUILD=1 CHIMERA_BUILD_NATIVE_ISO_PIPELINE=1
fi

if [[ -n "${CHIMERA_BUILD_STORAGE_ROOT:-}" ]]; then
  root="${CHIMERA_BUILD_STORAGE_ROOT%/}"
  [[ -n "$root" && -d "$root" && -w "$root" ]] || { log_error "Storage root must exist and be writable: $root"; exit 2; }
  probe="$(mktemp "$root/.chimera-storage-test.XXXXXX" 2>/dev/null)" || { log_error "Storage root failed a write test: $root"; exit 2; }
  rm -f "$probe"
  BUILD_DIR="$root/chimera-build"; ISO_DIR="$BUILD_DIR/iso"; ROOTFS_DIR="$BUILD_DIR/rootfs"; ISO_OUTPUT_DIR="$root/chimera-output"; ISO_TMP_DIR="$BUILD_DIR/logs/chimera-iso-build"; STATE_FILE="$BUILD_DIR/.chimera-build-state"; FAILED_FILE="$BUILD_DIR/.chimera-failed-stage"
  mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_DIR/boot/live" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"
  export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" TMPDIR="$ISO_TMP_DIR"
fi

free_bytes(){ df -PB1 "$1" 2>/dev/null | awk 'NR==2{print $4}'; }
free_gib(){ local n="$(free_bytes "$1")"; [[ "$n" =~ ^[0-9]+$ ]] && echo $((n/1024/1024/1024)) || echo 0; }
docker_image_bytes(){ docker image inspect "$1" --format '{{.Size}}' 2>/dev/null | awk 'NR==1{print $1+0}'; }
cleanup_generated_build_artifacts(){
  # Remove only build-owned intermediate artifacts. Never touch repository
  # source/assets, the final ISO/checksum, or explicitly supplied media.
  rm -rf -- \
    "$ISO_DIR/rootfs" \
    "$ISO_DIR/live" \
    "$ISO_DIR/boot" \
    "$ISO_DIR/install" \
    "$ISO_DIR/system" \
    "$ISO_DIR/desktop" \
    "$ISO_DIR/network" \
    "$ISO_DIR/drivers" \
    "$ISO_DIR/games" \
    "$BUILD_DIR/boot-artifacts" \
    "$BUILD_DIR/live-boot" \
    "$BUILD_DIR/emulators" \
    "$ISO_TMP_DIR" 2>/dev/null || true
  find "$BUILD_DIR" -maxdepth 3 -type f \
    \( -name '*.tmp' -o -name '*.partial' -o -name '*.part' -o -name '*.lock' \) \
    -delete 2>/dev/null || true
  # Remove empty build-owned directories left after the sweep.
  find "$ISO_DIR" -depth -type d -empty -delete 2>/dev/null || true
  docker container prune -f >/dev/null 2>&1 || true
}
cleanup_final_success_artifacts(){
  [[ "$BUILD_SUCCEEDED" == 1 ]] || return 0
  log_info "Cleaning unused generated ISO build intermediates..."
  cleanup_generated_build_artifacts
  # Resume/failure state is no longer useful after a complete verified build.
  rm -f -- "$STATE_FILE" "$FAILED_FILE" 2>/dev/null || true
  log_success "Unused generated build artifacts removed; final ISO/checksum retained."
}
docker_image_in_use(){
  local image="$1"
  docker ps -aq --filter "ancestor=$image" | grep -q .
}
cleanup_generated_docker_image(){
  local image="$1" image_id="$2" tagged=""
  [[ -n "$image_id" ]] || return 0
  if docker_image_in_use "$image"; then
    log_warning "Keeping Docker image $image because a container still references it."
    return 0
  fi
  # Remove every local tag that points at the image created by this build.
  while read -r tagged; do
    [[ -n "$tagged" ]] || continue
    docker image rm -f "$tagged" >/dev/null 2>&1 || true
  done < <(docker image ls --no-trunc --format '{{.Repository}}:{{.Tag}} {{.ID}}' | awk -v id="$image_id" '$2==id{print $1}')
  if docker image inspect "$image_id" >/dev/null 2>&1; then
    log_warning "Docker image layers remain because another local reference uses $image_id."
  else
    log_success "Unused generated Docker image removed: $image_id"
  fi
}
push_docker_image(){
  [[ "${CHIMERA_PUSH:-0}" == 1 ]] || return 0
  local source="$DOCKER_IMAGE:$DOCKER_TAG"
  local target="${CHIMERA_DOCKERHUB_IMAGE:-docker.io/amerhwitat/chimeraiios}"
  local target_tag="${CHIMERA_DOCKERHUB_TAG:-$DOCKER_TAG}"
  local image_id
  image_id="$(docker image inspect -f '{{.Id}}' "$source" 2>/dev/null || true)"
  [[ -n "$image_id" ]] || { log_error "Cannot push missing Docker image: $source"; return 1; }
  command -v docker >/dev/null || { log_error "Docker CLI not found"; return 1; }

  if [[ -n "${DOCKERHUB_USERNAME:-}" && -n "${DOCKERHUB_TOKEN:-}" ]]; then
    printf '%s' "$DOCKERHUB_TOKEN" | docker login docker.io --username "$DOCKERHUB_USERNAME" --password-stdin
  elif [[ -n "${CHIMERA_DOCKERHUB_USERNAME:-}" && -n "${CHIMERA_DOCKERHUB_TOKEN:-}" ]]; then
    printf '%s' "$CHIMERA_DOCKERHUB_TOKEN" | docker login docker.io --username "$CHIMERA_DOCKERHUB_USERNAME" --password-stdin
  elif ! docker info 2>/dev/null | grep -q 'Username:'; then
    log_error "Docker Hub credentials are required. Set DOCKERHUB_USERNAME/DOCKERHUB_TOKEN or CHIMERA_DOCKERHUB_USERNAME/CHIMERA_DOCKERHUB_TOKEN."
    return 1
  fi

  log_info "Publishing generated Docker image: $source -> $target:$target_tag"
  docker tag "$source" "$target:$target_tag"
  docker push "$target:$target_tag"
  if [[ "$target_tag" != "latest" && "${CHIMERA_DOCKERHUB_PUSH_LATEST:-0}" == 1 ]]; then
    docker tag "$source" "$target:latest"
    docker push "$target:latest"
  fi
  log_success "Docker Hub push completed: $target:$target_tag"
  cleanup_generated_docker_image "$source" "$image_id"
}

is_writable_dir(){
  local dir="$1" probe
  [[ -d "$dir" && -w "$dir" ]] || return 1
  probe="$(mktemp "$dir/.chimera-write-test.XXXXXX" 2>/dev/null)" || return 1
  rm -f "$probe" 2>/dev/null || return 1
  return 0
}
is_wsl(){ grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null || [[ -n "${WSL_INTEROP:-}" ]] || [[ -d /mnt/wsl ]]; }
choose_storage(){
  local need="${1:-20}"; local best="" free path
  if is_wsl; then
    for path in /mnt/*; do
      [[ -d "$path" ]] || continue
      free="$(free_gib "$path")"
      ((free>=need)) || continue
      is_writable_dir "$path" || { log_warning "Skipping non-writable storage candidate: $path"; continue; }
      [[ "$path" != /mnt/c ]] || continue
      best="$path"; break
    done
  else
    while read -r path; do
      free="$(free_gib "$path")"
      ((free>=need)) || continue
      is_writable_dir "$path" || { log_warning "Skipping non-writable storage candidate: $path"; continue; }
      best="$path"; break
    done < <(findmnt -rn -o TARGET 2>/dev/null | grep -Ev '^/(proc|sys|dev|run)(/|$)')
  fi
  if [[ -z "$best" ]] && is_writable_dir "$HOME"; then
    free="$(free_gib "$HOME")"
    ((free>=need)) && best="$HOME"
  fi
  [[ -n "$best" ]] || return 1
  BUILD_DIR="$best/chimera-build"; ISO_DIR="$BUILD_DIR/iso"; ROOTFS_DIR="$BUILD_DIR/rootfs"; ISO_OUTPUT_DIR="$best/chimera-output"; ISO_TMP_DIR="$BUILD_DIR/logs/chimera-iso-build"; STATE_FILE="$BUILD_DIR/.chimera-build-state"; FAILED_FILE="$BUILD_DIR/.chimera-failed-stage"
  mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_DIR/boot/live" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR" || return 1
  LOG_DIR="$BUILD_DIR/logs"
  ensure_log_dir || return 1
  export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" TMPDIR="$ISO_TMP_DIR"
  log_success "Build storage switched to $best"
}
preflight(){
  emit_build_diagnostics
  header 'CAPABILITY STATUS / EVIDENCE PREFLIGHT'
  python3 "$SCRIPT_DIR/tools/validation/validate_capability_status.py" || { log_error 'Capability evidence registry validation failed'; return 1; }
  header 'CPU / MEDIA PROFILE'
  log_info "Detected build-host CPU: $HOST_ARCH"
  log_info "Selected ISO target CPU: $TARGET_ARCH"
  log_info "Media filesystem profile: $MEDIA_FS_PROFILE (ISO9660/El Torito + SquashFS rootfs)"
  log_info "SquashFS worker count: ${CHIMERA_SQUASHFS_PROCESSORS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc 2>/dev/null || echo 2)}"
  header 'LARGE ISO / STORAGE PREFLIGHT'
  mkdir -p "$ROOTFS_DIR" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR" 2>/dev/null || true
  local rg="$(free_gib "$ROOTFS_DIR")" og="$(free_gib "$ISO_OUTPUT_DIR")"
  log_info "Rootfs filesystem free: ${rg} GiB"; log_info "ISO output filesystem free: ${og} GiB"
<<<<<<< HEAD
  if [[ "${CHIMERA_SKIP_SPACE_CHECKS:-0}" == 1 ]]; then
    log_info 'Storage preflight skipped (CHIMERA_SKIP_SPACE_CHECKS=1).'
  else
  local need="${CHIMERA_MIN_FREE_GIB:-20}"
  if ((rg<need || og<need)); then
=======
  # --storage-auto is an explicit request to select a suitable writable volume.
  if [[ "$STORAGE_AUTO" == 1 && -z "${CHIMERA_BUILD_STORAGE_ROOT:-}" ]]; then
    choose_storage 20 || { log_error 'No suitable writable storage with at least 20 GiB free was found'; log_error 'Read-only WSL /mnt mounts are never selected.'; exit 1; }
    rg="$(free_gib "$ROOTFS_DIR")"; og="$(free_gib "$ISO_OUTPUT_DIR")"
    log_info "Automatic storage selected; rootfs free=${rg} GiB output free=${og} GiB"
  elif ((rg<20 || og<20)); then
>>>>>>> bfa2171b7 (Restore full builder CLI and improve resume/storage handling)
    if [[ "$STORAGE_AUTO" == 1 ]]; then choose_storage 20 || { log_error 'No suitable writable storage with enough free space found'; log_error 'A read-only /mnt drive is never selected automatically.'; exit 1; }
    elif [[ "$STORAGE_PROMPT" == 1 && -t 0 ]]; then
      read -r -p 'Storage path for large Chimera build: ' p
      [[ -d "$p" ]] || { log_error 'No storage selected'; exit 1; }
      export CHIMERA_BUILD_STORAGE_ROOT="$p"; root="${p%/}"; BUILD_DIR="$root/chimera-build"; ISO_DIR="$BUILD_DIR/iso"; ROOTFS_DIR="$BUILD_DIR/rootfs"; ISO_OUTPUT_DIR="$root/chimera-output"; ISO_TMP_DIR="$BUILD_DIR/logs/chimera-iso-build"; STATE_FILE="$BUILD_DIR/.chimera-build-state"; FAILED_FILE="$BUILD_DIR/.chimera-failed-stage"; mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_DIR/boot/live" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"; export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" TMPDIR="$ISO_TMP_DIR"
    else log_error 'Insufficient storage; use --storage /mnt/d or --storage-auto'; exit 1; fi
  fi
  fi
  # Architecture/ISA discovery is metadata-only and defaults to offline mode.
  # Network research is opt-in; failures do not silently promote support claims.
  if [[ "${CHIMERA_ARCH_DISCOVERY:-1}" == 1 && -f "$SCRIPT_DIR/tools/architecture_discovery/chimera_discovery.py" ]]; then
    local -a discovery_args=(--output-dir "$BUILD_DIR/architecture-discovery")
    [[ "${CHIMERA_ARCH_DISCOVERY_ONLINE:-0}" == 1 ]] && discovery_args+=(--online)
    if ! python3 "$SCRIPT_DIR/tools/architecture_discovery/chimera_discovery.py" "${discovery_args[@]}"; then
      if [[ "${CHIMERA_ARCH_DISCOVERY_STRICT:-0}" == 1 ]]; then
        log_error 'Architecture discovery failed in strict mode'; return 1
      fi
      log_warning 'Architecture discovery failed; continuing build without promoting candidates.'
    fi
  fi
  command -v mksquashfs >/dev/null || { log_error 'mksquashfs is required'; exit 2; }
}
state_get(){ [[ -f "$STATE_FILE" ]] && sed -n 's/^completed=//p' "$STATE_FILE" | tail -1 || true; }
state_fingerprint(){
  local head diff untracked
  head="$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null || printf 'no-git')"
  diff="$(git -C "$SCRIPT_DIR" diff --binary HEAD -- . 2>/dev/null | sha256sum | awk '{print $1}')"
  # Include untracked source/assets too: otherwise a newly added file could
  # change the build inputs without invalidating a saved resume checkpoint.
  untracked="$(git -C "$SCRIPT_DIR" ls-files --others --exclude-standard -z 2>/dev/null | xargs -0 -r sha256sum 2>/dev/null | sha256sum | awk '{print $1}')"
  printf '%s:%s:%s' "$head" "${diff:-no-diff}" "${untracked:-no-untracked}"
}
state_mark(){
  local fingerprint
  fingerprint="$(state_fingerprint)"
  printf 'schema=3\ncompleted=%s\nfingerprint=%s\nupdated=%s\n' "$1" "$fingerprint" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$STATE_FILE" 2>/dev/null || log_warning "Build state could not be written to $STATE_FILE; continuing without persistent resume state."
}
state_reset(){ rm -f "$STATE_FILE" "$FAILED_FILE" 2>/dev/null || true; }
resume_artifacts_present(){
  case "$1" in
    docker) docker image inspect "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null 2>&1 ;;
    rootfs) [[ -d "$ROOTFS_DIR/etc" ]] ;;
    commands) [[ -x "$ROOTFS_DIR/usr/bin/chimera-cmd" ]] ;;
    docker-publish) return 1 ;; # Re-publish idempotently rather than trusting an old push marker.
    boot) [[ -s "$ISO_DIR/boot/grub/grub.cfg" || -s "$ISO_DIR/boot/grub.cfg" ]] ;;
    installer) [[ -s "$ISO_DIR/install/installer/installation.img" ]] ;;
    branding) [[ -d "$ISO_DIR/boot/visual" && -n "$(find "$ISO_DIR/boot/visual" -maxdepth 1 -type f -print -quit 2>/dev/null)" ]] ;;
    apache|features|package-managers|games) return 1 ;; # Re-run until each stage has a dedicated completion manifest.
    squashfs) [[ -s "$ISO_DIR/live/filesystem.squashfs" ]] ;;
    iso) [[ -s "$ISO_OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}-${TARGET_ARCH}.iso" ]] ;;
    verify) [[ -s "$ISO_OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}-${TARGET_ARCH}.iso.sha256" && -s "$LOG_DIR/iso-el-torito.log" ]] ;;
    native-iso|report) return 1 ;;
    *) return 1 ;;
  esac
}
state_done(){
<<<<<<< HEAD
  local c="$1" t="$2"; [[ -n "$c" ]] || return 1
  local order='docker rootfs commands docker-publish boot installer branding apache features package-managers games extended linuxboot scripts squashfs iso verify native-iso report'; local ci ti
  ci=$(printf '%s\n' "$order" | awk -v x="$c" '{for(i=1;i<=NF;i++)if($i==x)print i}'); ti=$(printf '%s\n' "$order" | awk -v x="$t" '{for(i=1;i<=NF;i++)if($i==x)print i}')
  [[ -n "$ci" && -n "$ti" && "$ci" -ge "$ti" ]]
=======
  local completed="$1" target="$2" stored_fingerprint current_fingerprint
  [[ -n "$completed" && -f "$STATE_FILE" ]] || return 1
  stored_fingerprint="$(sed -n 's/^fingerprint=//p' "$STATE_FILE" | tail -1)"
  current_fingerprint="$(state_fingerprint)"
  # Older state files or changed source trees are deliberately not trusted.
  [[ -n "$stored_fingerprint" && "$stored_fingerprint" == "$current_fingerprint" ]] || return 1
  local order='docker rootfs commands docker-publish boot installer branding apache features package-managers games squashfs iso verify native-iso report'; local ci ti
  ci=$(printf '%s\n' "$order" | awk -v x="$completed" '{for(i=1;i<=NF;i++)if($i==x)print i}')
  ti=$(printf '%s\n' "$order" | awk -v x="$target" '{for(i=1;i<=NF;i++)if($i==x)print i}')
  [[ -n "$ci" && -n "$ti" && "$ci" -ge "$ti" ]] || return 1
  resume_artifacts_present "$target"
>>>>>>> 181e59f46 (Validate saved build state before resuming completed stages)
}
run_stage(){
  local stage="$1" fn="$2" started="$SECONDS" started_utc rc elapsed
  started_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  CURRENT_STAGE="$stage"
  header "BEGIN STAGE: $stage"
  log_info "Stage started=$started_utc function=$fn pid=${BASHPID:-unknown}"
  if "$fn"; then
    elapsed=$((SECONDS-started))
    state_mark "$stage"
    log_success "Stage completed=$stage duration=${elapsed}s"
    log_file "STAGE_COMPLETE stage=$stage duration_seconds=$elapsed finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    CURRENT_STAGE=""
  else
    rc=$?
    elapsed=$((SECONDS-started))
    log_error "Stage failed=$stage exit=$rc duration=${elapsed}s function=$fn"
    log_file "STAGE_FAILED stage=$stage exit=$rc duration_seconds=$elapsed"
    return "$rc"
  fi
}

check_deps(){
  header 'BUILD DEPENDENCIES'
  if [[ "${CHIMERA_ROOTFS_MODE:-docker}" == "local" ]]; then
    local missing=0
    for t in debootstrap cpio grub-mkrescue xorriso mksquashfs chroot; do
      command -v "$t" >/dev/null 2>&1 || { log_error "Required local-rootfs tool missing: $t"; missing=1; }
    done
    command -v busybox >/dev/null 2>&1 || log_warning 'busybox unavailable on host; create_installer needs busybox-static.'
    (( missing == 0 )) || exit 2
    log_info 'Local debootstrap rootfs mode: Docker daemon not required.'
    return 0
  fi
  if ! command -v docker >/dev/null || ! command -v cpio >/dev/null || ! command -v grub-mkrescue >/dev/null || ! command -v xorriso >/dev/null || ! command -v mksquashfs >/dev/null; then
    if [[ "${CHIMERA_INSTALL_BUILD_DEPS:-0}" == 1 ]]; then
      bash "$SCRIPT_DIR/tools/chimera-build-deps.sh" || { log_error 'Build dependency fallback installer failed'; exit 2; }
    else
      log_error 'Required build tools are missing. Install Docker, cpio, grub-mkrescue, xorriso and mksquashfs; optional fallback: CHIMERA_INSTALL_BUILD_DEPS=1.'
      exit 2
    fi
  fi
  command -v docker >/dev/null || { log_error 'Docker is required'; exit 2; }
  command -v cpio >/dev/null || { log_error 'cpio is required'; exit 2; }
  command -v grub-mkrescue >/dev/null || { log_error 'grub-mkrescue is required'; exit 2; }
  command -v xorriso >/dev/null || { log_error 'xorriso is required'; exit 2; }
  command -v mksquashfs >/dev/null || { log_error 'mksquashfs is required'; exit 2; }
  command -v busybox >/dev/null || log_warning 'busybox unavailable on host; create_installer currently requires host BusyBox. Install busybox-static (Debian/Ubuntu) before the installer stage.'
  # Docker CLI presence does not imply that a daemon is running. Diagnose the
  # endpoint and optionally start a local Linux daemon when explicitly enabled.
  if ! docker info >/dev/null 2>&1; then
    # Capture the actual failure rather than collapsing socket permissions,
    # a stale context, and a stopped daemon into the same generic message.
    local docker_diag docker_socket
    docker_diag="$(docker info 2>&1 || true)"
    log_error 'Docker CLI cannot access the configured Docker Engine.'
    log_error "Docker context: $(docker context show 2>/dev/null || echo unknown)"
    log_error "DOCKER_HOST: ${DOCKER_HOST:-<unset>}"
    docker_socket="${DOCKER_HOST#unix://}"
    [[ -n "$docker_socket" && "$docker_socket" != "$DOCKER_HOST" ]] || docker_socket="/var/run/docker.sock"
    [[ -S "$docker_socket" ]] && log_info "Docker socket exists: $docker_socket" || log_warning "Docker socket not found at $docker_socket"
    [[ -S /run/docker.sock ]] && log_info "Alternative socket exists: /run/docker.sock"
    [[ -n "$docker_diag" ]] && log_error "Docker diagnostic: $(printf '%s' "$docker_diag" | tail -n 2 | tr '\n' ' ')"
    if sudo -n docker info >/dev/null 2>&1; then
      log_error 'The daemon is reachable only with sudo; fix socket group permissions rather than running the whole build as root.'
      log_error 'Try: sudo usermod -aG docker "$USER" ; then log out of WSL/Linux completely and log back in.'
    elif [[ -S "$docker_socket" ]] && ! [[ -r "$docker_socket" && -w "$docker_socket" ]]; then
      log_error "Current user lacks read/write permission on $docker_socket."
      log_error 'Check: ls -l /var/run/docker.sock; id; getent group docker'
    fi
    if [[ "${CHIMERA_AUTO_START_DOCKER:-0}" == 1 ]]; then
      if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files docker.service >/dev/null 2>&1; then
        if sudo -n systemctl start docker >/dev/null 2>&1; then
          sleep 2
        fi
      elif command -v service >/dev/null 2>&1 && [[ -x /etc/init.d/docker ]]; then
        sudo -n service docker start >/dev/null 2>&1 || true
        sleep 2
      fi
    fi
    if docker info >/dev/null 2>&1; then
      log_success 'Docker daemon became available.'
    else
      if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null || [[ -n "${WSL_INTEROP:-}" ]]; then
        log_error 'WSL detected: start Docker Desktop on Windows and enable Settings > Resources > WSL Integration for this distro, then rerun the build.'
        log_error 'If using Docker Engine inside WSL instead, start it with: sudo service docker start'
      elif command -v systemctl >/dev/null 2>&1; then
        log_error 'Start the Docker Engine with: sudo systemctl start docker'
      else
        log_error 'Start Docker Engine, verify the active context/DOCKER_HOST, and ensure your user can access the daemon socket.'
      fi
      log_error 'Optional Linux auto-start: set CHIMERA_AUTO_START_DOCKER=1 (requires passwordless sudo).'
      return 2
    fi
  fi
}

build_docker(){
  header 'STEP 1: BUILD DOCKER IMAGE'
  [[ -f "$SCRIPT_DIR/Dockerfile.comprehensive" ]] || { log_error 'Dockerfile.comprehensive not found'; exit 1; }
  start_watchdog "Docker BuildKit image build"; set +e
  local -a docker_build_args=()
  [[ "$FULL_BUILD" == 1 ]] && docker_build_args+=(--no-cache)
  BUILDKIT_PROGRESS=plain docker build --progress=plain "${docker_build_args[@]}" -f "$SCRIPT_DIR/Dockerfile.comprehensive" -t "$DOCKER_IMAGE:$DOCKER_TAG" -t "$DOCKER_IMAGE:latest" "$SCRIPT_DIR" 2>&1 | tee "$LOG_DIR/docker-build.log"
  local rc="${PIPESTATUS[0]}"; set -e; stop_watchdog; ((rc==0)) || { log_error "Docker build failed; full log: $LOG_DIR/docker-build.log"; exit "$rc"; }
}

export_rootfs(){
  if [[ "${CHIMERA_ROOTFS_MODE:-docker}" == "local" ]]; then
    export_rootfs_local
    return $?
  fi
  header 'STEP 2: EXPORT DOCKER ROOTFS'
  cleanup_generated_build_artifacts
  mkdir -p "$ROOTFS_DIR"
  rm -rf "$ROOTFS_DIR"/*
  local cname="chimera-export-$BASHPID"
  local tar_rc=1
  local image_bytes=0 free_now=0 required_bytes=0
  local safety_bytes=$((4 * 1024 * 1024 * 1024))
  image_bytes="$(docker_image_bytes "$DOCKER_IMAGE:$DOCKER_TAG")"
  free_now="$(free_bytes "$ROOTFS_DIR")"
  required_bytes=$((image_bytes + safety_bytes))
  log_info "Docker image virtual size: $((image_bytes / 1024 / 1024 / 1024)) GiB"
  log_info "Rootfs target free space: $((free_now / 1024 / 1024 / 1024)) GiB"
  log_info "Rootfs export safety requirement: $((required_bytes / 1024 / 1024 / 1024)) GiB"
  if (( free_now < required_bytes )); then
    log_error "Insufficient free space for Docker rootfs export."
    log_error "Required: $((required_bytes / 1024 / 1024 / 1024)) GiB; available: $((free_now / 1024 / 1024 / 1024)) GiB"
    log_error "Use --storage-auto or --storage /path/to/a-writable-large-filesystem."
    exit 1
  fi
  docker rm -f "$cname" >/dev/null 2>&1 || true
  docker create --name "$cname" "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null
  start_watchdog "Docker rootfs export / tar extraction"
  set +e


    log_info "STEP 2: exporting Docker rootfs"
  # archive.  Extract it with delayed directory metadata restoration so
  # usr/local and deeply nested package trees are created before tar applies
  # their final permissions/timestamps.  This also avoids failures on WSL
  # and other filesystems that reject directory metadata during creation.
  # Exclude volatile host/package-manager state from the immutable ISO rootfs.
  local tar_args=(-xpf - -C "$ROOTFS_DIR"
                  --no-same-owner --no-same-permissions
                  --delay-directory-restore
                  --exclude=./var/log/*
                  --exclude=./var/cache/*
                  --exclude=./var/tmp/*
                  --exclude=./var/lib/apt/lists/*
                  --exclude=./var/lib/dpkg/updates/*
                  --exclude=./var/lib/systemd/coredump/*
                  --exclude=./var/lib/systemd/random-seed
                  --exclude=./var/lib/NetworkManager/*
                  --exclude=./var/spool/*
                  --exclude=./var/run/*
                  --exclude=./run/*
                  --exclude=./tmp/*
                  --exclude=./root/.cache/*
                  --exclude=./home/*/.cache/*
                  --checkpoint=10000
                  --checkpoint-action="echo=[ROOTFS] extracted %T")
  if command -v pv >/dev/null 2>&1; then
    docker export "$cname" |
      pv -brt 2> >(tee -a "$LOG_DIR/docker-export.progress" >&2) |
      tar "${tar_args[@]}"
    local s=("${PIPESTATUS[@]}")
    tar_rc="${s[2]:-1}"
    [[ "${s[0]:-1}" == 0 && "${s[1]:-1}" == 0 ]] || tar_rc=1
  else
    docker export "$cname" | tar "${tar_args[@]}"
    local s=("${PIPESTATUS[@]}")
    tar_rc="${s[1]:-1}"
    [[ "${s[0]:-1}" == 0 ]] || tar_rc=1
  fi
  set -e
  stop_watchdog
  docker rm -f "$cname" >/dev/null 2>&1 || true

  (( tar_rc==0 )) || {
    log_error "Docker rootfs export failed (tar exit $tar_rc)"
    log_error "Target filesystem after failure: $(df -h "$ROOTFS_DIR" 2>/dev/null | tail -1 || true)"
    log_error "Generated rootfs usage: $(du -sh "$ROOTFS_DIR" 2>/dev/null | tail -1 || true)"
    exit 1
  }
  mkdir -p "$ROOTFS_DIR"/{run,tmp,var/log,var/cache,var/tmp,var/spool}
  chmod 1777 "$ROOTFS_DIR/tmp" "$ROOTFS_DIR/var/tmp" 2>/dev/null || true
  rm -rf -- "$ROOTFS_DIR/var/lib/apt/lists/"* "$ROOTFS_DIR/root/.cache" 2>/dev/null || true
  [[ -d "$ROOTFS_DIR/bin" || -d "$ROOTFS_DIR/usr/bin" ]] || {
    log_error 'Rootfs export is incomplete'
    exit 1
  }
}

create_boot_menu(){
  header 'STEP 3: BUILD BOOT ARTIFACTS'
  # Refresh advisory ISA/kernel/driver/mobile-OS research before producing boot artifacts.
  # Set CHIMERA_ISA_RESEARCH=0 to skip network discovery; offline indexing remains available.
  if [[ "${CHIMERA_ISA_RESEARCH:-1}" != "0" ]]; then
    if [[ ! -f "$SCRIPT_DIR/tools/isa/research_catalog.py" ]]; then
      log_warning "ISA research script is missing; skipping optional research refresh. Update the checkout or restore tools/isa/research_catalog.py."
    elif command -v python3 >/dev/null 2>&1; then
      CHIMERA_ISA_RESEARCH_DEPTH="${CHIMERA_ISA_RESEARCH_DEPTH:-10}" CHIMERA_ISA_RESEARCH_PAGE_BUDGET="${CHIMERA_ISA_RESEARCH_PAGE_BUDGET:-80}" python3 "$SCRIPT_DIR/tools/isa/research_catalog.py" --depth "${CHIMERA_ISA_RESEARCH_DEPTH:-10}" --page-budget "${CHIMERA_ISA_RESEARCH_PAGE_BUDGET:-80}" 2>&1 | tee -a "$LOG_DIR/isa-research.log" || {
        log_warning "Online ISA research failed; continuing boot build with existing registries."
      }
    else
      log_warning "python3 unavailable; skipping ISA research refresh."
    fi
  else
    log_info "ISA research refresh skipped by CHIMERA_ISA_RESEARCH=0."
  fi
  CHIMERA_SYSTEM_BLOCK_SIZE="$CHIMERA_SYSTEM_BLOCK_SIZE" SYSTEM_BLOCK_SIZE="$CHIMERA_SYSTEM_BLOCK_SIZE" bash "$SCRIPT_DIR/kernel/build-koronos.sh"
  local k="$SCRIPT_DIR/build/koronos/x86_64/koronos.elf"; [[ -s "$k" ]] || { log_error 'Koronos ELF missing'; exit 1; }
  mkdir -p "$ISO_DIR/boot/koronos" "$ISO_DIR/boot/jasper" "$ISO_DIR/boot/spitfire" "$ISO_DIR/boot/grub" "$ISO_DIR/boot/live" "$ISO_DIR/EFI/BOOT"
  chimera_copy_if_distinct "$k" "$ISO_DIR/boot/kernel.bin"; chimera_copy_if_distinct "$k" "$ISO_DIR/boot/koronos/koronos.elf"
  bash "$SCRIPT_DIR/tools/build-boot-artifacts.sh"
  local b="$BUILD_DIR/boot-artifacts"; [[ -s "$b/jasper/jasper.elf" ]] || { log_error 'Jasper ELF missing'; exit 1; }
  cp "$b/jasper/jasper.elf" "$ISO_DIR/boot/jasper/"
  for f in spitfire-sf0-mbr.bin spitfire-stage2.bin spitfire-sf1-longmode.o spitfire-sf2-loader.o; do [[ -s "$b/spitfire/$f" ]] || { log_error "Missing Spit Fire artifact: $f"; exit 1; }; cp "$b/spitfire/$f" "$ISO_DIR/boot/spitfire/"; done
  bash "$SCRIPT_DIR/tools/build-live-boot-binaries.sh"
  chimera_copy_if_distinct "$BUILD_DIR/live-boot/boot/live/chimera-live-initramfs.img" "$ISO_DIR/boot/live/chimera-live-initramfs.img"
  chimera_copy_if_distinct "$BUILD_DIR/live-boot/boot/live/live-manifest.json" "$ISO_DIR/boot/live/live-manifest.json"
  mkdir -p "$ISO_DIR/boot/recovery" "$ISO_DIR/recovery"
  chimera_copy_if_distinct "$BUILD_DIR/live-boot/boot/recovery/chimera-recovery-initramfs.img" "$ISO_DIR/boot/recovery/chimera-recovery-initramfs.img"
  chimera_copy_if_distinct "$BUILD_DIR/live-boot/boot/recovery/chimera-recovery-initramfs.img.sha256" "$ISO_DIR/boot/recovery/chimera-recovery-initramfs.img.sha256"
  chimera_copy_if_distinct "$BUILD_DIR/live-boot/boot/recovery/recovery-manifest.json" "$ISO_DIR/boot/recovery/recovery-manifest.json"
  cp "$SCRIPT_DIR/config/recovery/chimera-recovery-targets.json" "$ISO_DIR/recovery/"
  cp "$SCRIPT_DIR/docs/recovery-runtime-levels.md" "$ISO_DIR/recovery/"
  [[ -s "$BUILD_DIR/live-boot/boot/vmlinuz" ]] && chimera_copy_if_distinct "$BUILD_DIR/live-boot/boot/vmlinuz" "$ISO_DIR/boot/live/vmlinuz" || true
  [[ -f "$SCRIPT_DIR/boot/iso/grub.cfg" ]] && cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$ISO_DIR/boot/grub/grub.cfg"
  # Stage every canonical Jasper, installation and Spit Fire menu contract.
  for f in "$SCRIPT_DIR/boot/jasper/"*.cfg; do
    [[ -f "$f" ]] || continue
    cp -f "$f" "$ISO_DIR/boot/jasper/$(basename "$f")"
  done
  for f in "$SCRIPT_DIR/boot/installation/"*.cfg; do
    [[ -f "$f" ]] || continue
    mkdir -p "$ISO_DIR/boot/installation"
    cp -f "$f" "$ISO_DIR/boot/installation/$(basename "$f")"
  done
  for f in "$SCRIPT_DIR/boot/spitfire/"*.cfg; do
    [[ -f "$f" ]] || continue
    cp -f "$f" "$ISO_DIR/boot/spitfire/$(basename "$f")"
  done
  [[ -f "$SCRIPT_DIR/boot/loader-menu.cfg" ]] && cp -f "$SCRIPT_DIR/boot/loader-menu.cfg" "$ISO_DIR/boot/loader-menu.cfg"
  [[ -f "$SCRIPT_DIR/boot/boot-menu-contract.json" ]] && cp -f "$SCRIPT_DIR/boot/boot-menu-contract.json" "$ISO_DIR/boot/boot-menu-contract.json"
  [[ -f "$SCRIPT_DIR/boot/boot-artwork-manifest.json" ]] && cp -f "$SCRIPT_DIR/boot/boot-artwork-manifest.json" "$ISO_DIR/boot/boot-artwork-manifest.json"
  [[ -f "$SCRIPT_DIR/boot/iso/grub.cfg" ]] || { log_error 'GRUB configuration missing'; exit 1; }
  [[ -s "$ISO_DIR/boot/grub/grub.cfg" ]] || { log_error 'Staged GRUB configuration is empty'; exit 1; }
  [[ -s "$ISO_DIR/boot/recovery/chimera-recovery-initramfs.img" ]] || { log_error 'Recovery initramfs missing'; exit 1; }
  [[ -s "$ISO_DIR/boot/live/chimera-live-initramfs.img" ]] || { log_error 'Live initramfs missing'; exit 1; }
}

prepare_branding(){
  header 'STEP 4: BRANDING / AURORA'
  mkdir -p "$ROOTFS_DIR/usr/share/chimera/aurora" \
           "$ROOTFS_DIR/usr/share/chimera/aurora/assets/library" \
           "$ROOTFS_DIR/usr/share/backgrounds/chimera" \
           "$ISO_DIR/boot/visual" \
           "$ISO_DIR/boot/grub"

  # Discover and stage repository artwork recursively. Do not assume that
  # user-supplied artwork lives in one hard-coded directory: repositories often
  # contain artwork under desktop, assets, docs, mobile, themes, and app folders.
  # Keep original filenames/relative paths, exclude VCS/build/vendor caches, and
  # prefer the named original session wallpaper when present. If it is absent,
  # keep the generated offline artwork rather than failing on a stale filename.
  local artwork_stage="$BUILD_DIR/aurora-artwork-library"
  local artwork_manifest="$artwork_stage/artwork-index.txt"
  local preferred_wallpaper=""
  rm -rf -- "$artwork_stage"
  mkdir -p "$artwork_stage"
  : > "$artwork_manifest"
  while IFS= read -r -d '' asset; do
    local rel dest
    rel="${asset#"$SCRIPT_DIR"/}"
    dest="$artwork_stage/$rel"
    mkdir -p "$(dirname "$dest")"
    if cp -p -- "$asset" "$dest"; then
      printf '%s\n' "$rel" >> "$artwork_manifest"
      case "$(basename "$asset" | tr '[:upper:]' '[:lower:]')" in
        duck-ai-image-2026-10-18-06-36.jpeg)
          preferred_wallpaper="$dest"
          ;;
      esac
    fi
  done < <(find "$SCRIPT_DIR" \
    \( -type d \( -name .git -o -name .github -o -name node_modules -o -name vendor -o -name build -o -name dist -o -name target -o -name .venv -o -name __pycache__ \) -prune \) -o \
    \( -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' -o -iname '*.bmp' -o -iname '*.gif' -o -iname '*.tif' -o -iname '*.tiff' -o -iname '*.svg' -o -iname '*.avif' -o -iname '*.heic' -o -iname '*.heif' -o -iname '*.jxl' -o -iname '*.ico' -o -iname '*.icns' \) -print0 \) 2>/dev/null)
  if [[ -s "$artwork_manifest" ]]; then
    log_info "Discovered $(wc -l < "$artwork_manifest" | tr -d ' ') artwork files recursively."
    mkdir -p "$ROOTFS_DIR/usr/share/chimera/aurora/assets/library/repository-artwork" \
             "$ISO_DIR/desktop/aurora/assets/library/repository-artwork" \
             "$ROOTFS_DIR/usr/share/chimera/aurora/branding/artwork-library" \
             "$ISO_DIR/desktop/aurora/branding/artwork-library" \
             "$ROOTFS_DIR/usr/share/chimera/branding/artwork-library" \
             "$ISO_DIR/system/branding/artwork-library"
    # Keep a complete offline copy in the desktop library AND the canonical
    # branding namespace, so boot/installer/desktop consumers never need network
    # access or a particular source-tree layout.
    cp -a "$artwork_stage/." "$ROOTFS_DIR/usr/share/chimera/aurora/assets/library/repository-artwork/"
    cp -a "$artwork_stage/." "$ISO_DIR/desktop/aurora/assets/library/repository-artwork/"
    cp -a "$artwork_stage/." "$ROOTFS_DIR/usr/share/chimera/aurora/branding/artwork-library/"
    cp -a "$artwork_stage/." "$ISO_DIR/desktop/aurora/branding/artwork-library/"
    cp -a "$artwork_stage/." "$ROOTFS_DIR/usr/share/chimera/branding/artwork-library/"
    cp -a "$artwork_stage/." "$ISO_DIR/system/branding/artwork-library/"
    cp -f "$artwork_manifest" "$ROOTFS_DIR/usr/share/chimera/aurora/assets/library/repository-artwork-index.txt"
    cp -f "$artwork_manifest" "$ISO_DIR/desktop/aurora/assets/library/repository-artwork-index.txt"
    cp -f "$artwork_manifest" "$ROOTFS_DIR/usr/share/chimera/aurora/branding/artwork-index.txt"
    cp -f "$artwork_manifest" "$ISO_DIR/desktop/aurora/branding/artwork-index.txt"
    cp -f "$artwork_manifest" "$ROOTFS_DIR/usr/share/chimera/branding/artwork-index.txt"
    cp -f "$artwork_manifest" "$ISO_DIR/system/branding/artwork-index.txt"
    # Record hashes for reproducible offline auditing and detect damaged assets.
    if command -v sha256sum >/dev/null 2>&1; then
      (cd "$artwork_stage" && find . -type f -print0 | sort -z | xargs -0 -r sha256sum) \
        > "$ISO_DIR/system/branding/artwork-sha256.txt"
      cp -f "$ISO_DIR/system/branding/artwork-sha256.txt" \
        "$ROOTFS_DIR/usr/share/chimera/branding/artwork-sha256.txt"
      cp -f "$ISO_DIR/system/branding/artwork-sha256.txt" \
        "$ROOTFS_DIR/usr/share/chimera/aurora/branding/artwork-sha256.txt"
      cp -f "$ISO_DIR/system/branding/artwork-sha256.txt" \
        "$ISO_DIR/desktop/aurora/branding/artwork-sha256.txt"
    fi
  else
    log_warning "No raster/SVG artwork files found by recursive scan; generated Aurora artwork remains the fallback."
  fi

  # Resolve the default wallpaper without depending on a single legacy filename.
  # Explicit CHIMERA_AURORA_ASSET has priority, then the original session image,
  # then descriptive wallpaper/background names; generated assets remain fallback.
  local discovered_wallpaper=""
  if [[ -n "${CHIMERA_AURORA_ASSET:-}" && -s "${CHIMERA_AURORA_ASSET}" ]]; then
    discovered_wallpaper="$CHIMERA_AURORA_ASSET"
  elif [[ -n "$preferred_wallpaper" && -s "$preferred_wallpaper" ]]; then
    discovered_wallpaper="$preferred_wallpaper"
  else
    while IFS= read -r -d '' asset; do
      case "$(basename "$asset" | tr '[:upper:]' '[:lower:]')" in
        *wallpaper*|*background*|*aurora*desktop*)
          discovered_wallpaper="$asset"
          break
          ;;
      esac
    done < <(find "$SCRIPT_DIR" \
      \( -type d \( -name .git -o -name .github -o -name node_modules -o -name vendor -o -name build -o -name dist -o -name target -o -name .venv -o -name __pycache__ \) -prune \) -o \
      \( -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' -o -iname '*.bmp' -o -iname '*.gif' -o -iname '*.tif' -o -iname '*.tiff' -o -iname '*.svg' -o -iname '*.avif' -o -iname '*.heic' -o -iname '*.heif' -o -iname '*.jxl' -o -iname '*.ico' -o -iname '*.icns' \) -print0 \) 2>/dev/null)
  fi
  if [[ -n "$discovered_wallpaper" && -s "$discovered_wallpaper" ]]; then
    export CHIMERA_AURORA_ASSET="$discovered_wallpaper"
    log_info "Selected recursively discovered Aurora wallpaper: ${discovered_wallpaper#"$SCRIPT_DIR"/}"
  fi

  # Build the deterministic Aurora visual set, then actively apply the selected
  # repository artwork to boot + desktop + showcase + menu surfaces. Discovery
  # alone is not enough: each consumer needs a normalized raster image staged
  # under the exact filename it loads at boot/runtime.
  local visual="$BUILD_DIR/aurora-media"
  rm -rf -- "$visual"
  if [[ -x "$SCRIPT_DIR/tools/aurora/build-visual-assets.sh" ]]; then
    bash "$SCRIPT_DIR/tools/aurora/build-visual-assets.sh" "$visual"
  fi

  if [[ -n "${CHIMERA_AURORA_ASSET:-}" && -s "$CHIMERA_AURORA_ASSET" ]]; then
    local selected_art="$CHIMERA_AURORA_ASSET"
    local applied_art="$BUILD_DIR/aurora-selected-artwork.png"
    local png_magic
    png_magic="$(head -c 8 "$selected_art" 2>/dev/null | od -An -tx1 | tr -d ' \\n')"
    if [[ "$png_magic" == "89504e470d0a1a0a" ]]; then
      cp -f -- "$selected_art" "$applied_art"
    elif command -v convert >/dev/null 2>&1; then
      if ! convert "$selected_art" -resize 1920x1080^ -gravity center -extent 1920x1080 "PNG32:$applied_art" 2>"$LOG_DIR/aurora-selected-artwork-convert.log"; then
        rm -f "$applied_art"
      fi
    elif command -v magick >/dev/null 2>&1; then
      if ! magick "$selected_art" -resize 1920x1080^ -gravity center -extent 1920x1080 "PNG32:$applied_art" 2>"$LOG_DIR/aurora-selected-artwork-convert.log"; then
        rm -f "$applied_art"
      fi
    fi

    if [[ -s "$applied_art" ]] && [[ "$(head -c 8 "$applied_art" | od -An -tx1 | tr -d ' \\n')" == "89504e470d0a1a0a" ]]; then
      for surface in \
        "$visual/backgrounds/boot.png" \
        "$visual/backgrounds/desktop.png" \
        "$visual/backgrounds/showcase.png" \
        "$visual/menus/default.png"; do
        mkdir -p "$(dirname "$surface")"
        cp -f "$applied_art" "$surface"
      done
      log_info "Applied discovered artwork to Aurora boot, desktop, showcase, and menu surfaces."
    else
      log_warning "Selected artwork could not be normalized to PNG; retaining generated Aurora surfaces."
    fi
  fi

  # Stage every boot/menu screen explicitly. GRUB/Jasper/Spit Fire only consume
  # raster images; the original SVGs remain available to the graphical runtime.
  for f in \
    boot.png desktop.png showcase.png menus/default.png \
    splash/aurora-splash.png installer/aurora-installer.png \
    recovery/aurora-recovery.png diagnostics/aurora-diagnostics.png \
    live/aurora-live.png mobile/aurora-mobile.png; do
    [[ -s "$visual/$f" ]] || continue
    cp -f "$visual/$f" "$ISO_DIR/boot/visual/$(basename "$f")"
  done

  # Canonical GRUB/Jasper background: materialize the repository's embedded
  # artwork when available, otherwise use the generated Aurora boot artwork.
  # The embedded payload is optional. Never allow a malformed Base64 blob or a
  # missing image converter to abort the branding stage.
  local embedded_art="$SCRIPT_DIR/boot/visual/aurora-wayland-glass.jpg.b64"
  local embedded_out="$ISO_DIR/boot/visual/aurora-wayland-glass.jpg"
  if [[ -s "$embedded_art" ]]; then
    local embedded_tmp="$embedded_out.tmp"
    rm -f "$embedded_tmp"
    if base64 -d -i "$embedded_art" >"$embedded_tmp" 2>"$LOG_DIR/aurora-artwork-base64.log"; then
      if [[ -s "$embedded_tmp" ]] &&
         { head -c 2 "$embedded_tmp" | od -An -tx1 | tr -d ' \n' | grep -qi '^ffd8' ||
           head -c 8 "$embedded_tmp" | od -An -tx1 | tr -d ' \n' | grep -qi '^89504e470d0a1a0a'; }; then
        mv -f "$embedded_tmp" "$embedded_out"
        log_info "Embedded Aurora GRUB artwork decoded successfully."
      else
        rm -f "$embedded_tmp"
        log_warning "Embedded Aurora GRUB artwork decoded but has an unsupported file signature; using generated Aurora artwork."
      fi
    else
      rm -f "$embedded_tmp"
      log_warning "Embedded Aurora GRUB artwork Base64 payload is invalid; using generated Aurora artwork."
    fi
  fi

  if [[ ! -s "$embedded_out" ]] && [[ -s "$visual/backgrounds/boot.png" ]]; then
    if command -v convert >/dev/null 2>&1; then
      if convert "$visual/backgrounds/boot.png" -quality 90 "$embedded_out" 2>"$LOG_DIR/aurora-artwork-convert.log"; then
        log_info "Generated Aurora GRUB artwork converted to JPEG."
      else
        rm -f "$embedded_out"
        log_warning "ImageMagick conversion failed; GRUB artwork will use the PNG fallback."
      fi
    else
      log_warning "ImageMagick unavailable; skipping optional JPEG artwork."
    fi
  fi

  # Init.mp4 is a hardcoded offline Aurora splash asset. GRUB does not
  # decode MP4; Jasper/Wayland hands it to Aurora after the graphical session
  # is ready. The same binary is deliberately staged for installer + desktop
  # so all entry paths share one deterministic video.
  local init_video=""
  for candidate in \
    "$SCRIPT_DIR/desktop/aurora/assets/Init.mp4" \
    "$SCRIPT_DIR/desktop/aurora/assets/library/Init.mp4" \
    "$SCRIPT_DIR/build/aurora-media/Init.mp4" \
    "$SCRIPT_DIR/Init.mp4"; do
    if [[ -s "$candidate" ]]; then init_video="$candidate"; break; fi
  done

  [[ -n "$init_video" ]] || {
    log_error "Required Aurora Init.mp4 is missing."
    log_error "Expected desktop/aurora/assets/Init.mp4 or desktop/aurora/assets/library/Init.mp4."
    return 1
  }

  if command -v ffprobe >/dev/null 2>&1; then
    ffprobe -v error -select_streams v:0 -show_entries stream=codec_type \
      -of csv=p=0 "$init_video" >/dev/null || {
        log_error "Aurora Init.mp4 failed ffprobe validation: $init_video"
        return 1
      }
  fi

  mkdir -p \
    "$ISO_DIR/boot/visual" \
    "$ROOTFS_DIR/usr/share/chimera/aurora/assets" \
    "$ROOTFS_DIR/usr/share/chimera/aurora/assets/library" \
    "$ROOTFS_DIR/usr/share/chimera/installer/assets" \
    "$ROOTFS_DIR/usr/share/chimera/installer"

  cp -f "$init_video" "$ISO_DIR/boot/visual/Init.mp4"
  cp -f "$init_video" "$ISO_DIR/boot/visual/chimera-intro.mp4"
  cp -f "$init_video" "$ROOTFS_DIR/usr/share/chimera/aurora/assets/init.mp4"
  cp -f "$init_video" "$ROOTFS_DIR/usr/share/chimera/aurora/assets/Init.mp4"
  cp -f "$init_video" "$ROOTFS_DIR/usr/share/chimera/installer/assets/Init.mp4"
  cp -f "$init_video" "$ROOTFS_DIR/usr/share/chimera/installer/assets/installer-splash.mp4"

  # Hard-stage the same offline artwork/media at every native handoff boundary.
  # Spit Fire/Jasper/GRUB must be able to find the assets without depending on
  # the later Aurora rootfs mount. GRUB itself only uses the raster/SVG assets;
  # Init.mp4 is carried forward for Jasper/Aurora handoff.
  mkdir -p "$ISO_DIR/boot/spitfire" "$ISO_DIR/boot/jasper" "$ISO_DIR/boot/grub" "$ISO_DIR/boot/koronos"
  for stage in spitfire jasper grub koronos; do
    cp -f "$init_video" "$ISO_DIR/boot/$stage/Init.mp4"
    cp -f "$SCRIPT_DIR/boot/boot-artwork-manifest.json" "$ISO_DIR/boot/$stage/boot-artwork-manifest.json"
  done

  [[ -s "$SCRIPT_DIR/boot/splash/spitfire_background.svg" ]] || { log_error "Spit Fire background is missing"; return 1; }
  [[ -s "$SCRIPT_DIR/boot/splash/jasper_background.svg" ]] || { log_error "Jasper background is missing"; return 1; }
  [[ -s "$SCRIPT_DIR/boot/splash/aurora_boot_splash.svg" ]] || { log_error "Koronos splash artwork is missing"; return 1; }

  cp -f "$SCRIPT_DIR/boot/splash/spitfire_background.svg" "$ISO_DIR/boot/spitfire/spitfire_background.svg"
  cp -f "$SCRIPT_DIR/boot/splash/jasper_background.svg" "$ISO_DIR/boot/jasper/jasper_background.svg"
  cp -f "$SCRIPT_DIR/boot/splash/aurora_boot_splash.svg" "$ISO_DIR/boot/koronos/aurora_boot_splash.svg"
  cp -f "$SCRIPT_DIR/boot/splash/aurora_boot_splash.svg" "$ISO_DIR/boot/grub/aurora_boot_splash.svg"

  # The canonical raster background is also copied into every bootloader
  # namespace so a stage can render it without reaching across directories.
  if [[ -s "$embedded_out" ]]; then
    cp -f "$embedded_out" "$ISO_DIR/boot/spitfire/aurora-wayland-glass.jpg"
    cp -f "$embedded_out" "$ISO_DIR/boot/jasper/aurora-wayland-glass.jpg"
    cp -f "$embedded_out" "$ISO_DIR/boot/grub/aurora-wayland-glass.jpg"
    cp -f "$embedded_out" "$ISO_DIR/boot/koronos/aurora-wayland-glass.jpg"
  fi
  if [[ -s "$visual/backgrounds/boot.png" ]]; then
    cp -f "$visual/backgrounds/boot.png" "$ISO_DIR/boot/spitfire/aurora-boot.png"
    cp -f "$visual/backgrounds/boot.png" "$ISO_DIR/boot/jasper/aurora-boot.png"
    cp -f "$visual/backgrounds/boot.png" "$ISO_DIR/boot/grub/aurora-boot.png"
    cp -f "$visual/backgrounds/boot.png" "$ISO_DIR/boot/koronos/aurora-boot.png"
  fi

  # One machine-readable contract consumed by Aurora desktop, installer and
  # boot-progress UI. Progress remains independent of the media player.
  cat > "$ROOTFS_DIR/usr/share/chimera/aurora/assets/init-video.json" <<'EOF_INIT_VIDEO'
{
  "schema": "CHIMERA-AURORA-INIT-VIDEO-1",
  "file": "/usr/share/chimera/aurora/assets/Init.mp4",
  "installer_file": "/usr/share/chimera/installer/assets/Init.mp4",
  "boot_file": "/boot/visual/Init.mp4",
  "desktop": true,
  "installer": true,
  "aurora_boot": true,
  "offline": true,
  "progress_state": "/run/chimera/koronos-progress.state",
  "progress_ui": "/usr/share/chimera/aurora/aurora-progress.sh"
}
EOF_INIT_VIDEO

  # Keep the complete artwork library inside the installed system and on the
  # ISO so every Aurora screen can use the hardcoded artwork offline.
  # Ship the curated cross-platform optional-app catalog to both the installed
  # root filesystem and the ISO artifact. Catalog entries are discovery-only;
  # this does not install third-party applications or claim native compatibility.
  local optional_app_catalog="$SCRIPT_DIR/desktop/optional_apps_catalog.json"
  [[ -s "$optional_app_catalog" ]] || {
    log_error "Required optional application catalog is missing: $optional_app_catalog"
    return 1
  }
  mkdir -p "$ROOTFS_DIR/usr/share/chimera/desktop" "$ISO_DIR/system/applications"
  cp -f "$optional_app_catalog" "$ROOTFS_DIR/usr/share/chimera/desktop/optional_apps_catalog.json"
  cp -f "$optional_app_catalog" "$ISO_DIR/system/applications/optional_apps_catalog.json"
  chmod 0644 "$ROOTFS_DIR/usr/share/chimera/desktop/optional_apps_catalog.json" "$ISO_DIR/system/applications/optional_apps_catalog.json"
  if [[ -d "$SCRIPT_DIR/desktop/aurora/assets/library" ]]; then
    cp -a "$SCRIPT_DIR/desktop/aurora/assets/library/." \
      "$ROOTFS_DIR/usr/share/chimera/aurora/assets/library/"
  fi
  if [[ -f "$SCRIPT_DIR/desktop/aurora/assets/library-artwork-manifest.json" ]]; then
    cp -f "$SCRIPT_DIR/desktop/aurora/assets/library-artwork-manifest.json" \
      "$ROOTFS_DIR/usr/share/chimera/aurora/assets/"
  fi

  # Install the same visual aliases used by desktop, installer, recovery and
  # mobile components so there is one deterministic offline artwork contract.
  if [[ -s "$visual/backgrounds/desktop.png" ]]; then
    cp -f "$visual/backgrounds/desktop.png" \
      "$ROOTFS_DIR/usr/share/chimera/aurora/aurora-wayland-glass.png"
    cp -f "$visual/backgrounds/desktop.png" \
      "$ROOTFS_DIR/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png"
  fi
  if [[ -s "$visual/backgrounds/boot.png" ]]; then
    cp -f "$visual/backgrounds/boot.png" \
      "$ROOTFS_DIR/usr/share/backgrounds/chimera/Aurora-Boot.png"
  fi
  if [[ -s "$visual/installer/aurora-installer.png" ]]; then
    cp -f "$visual/installer/aurora-installer.png" \
      "$ROOTFS_DIR/usr/share/backgrounds/chimera/Aurora-Installer.png"
  fi
  if [[ -s "$visual/recovery/aurora-recovery.png" ]]; then
    cp -f "$visual/recovery/aurora-recovery.png" \
      "$ROOTFS_DIR/usr/share/backgrounds/chimera/Aurora-Recovery.png"
  fi
  if [[ -s "$visual/live/aurora-live.png" ]]; then
    cp -f "$visual/live/aurora-live.png" \
      "$ROOTFS_DIR/usr/share/backgrounds/chimera/Aurora-Live.png"
  fi

  # Make the real GRUB theme contract part of the ISO.
  if [[ -s "$SCRIPT_DIR/boot/iso/aurora-theme.txt" ]]; then
    cp -f "$SCRIPT_DIR/boot/iso/aurora-theme.txt" "$ISO_DIR/boot/grub/aurora-theme.txt"
  fi

  # Preserve an explicitly supplied background as the highest-priority
  # desktop artwork while still staging the complete generated asset set.
  local bg="${CHIMERA_AURORA_ASSET:-}"
  if [[ -n "$bg" && -f "$bg" ]]; then
    cp -f "$bg" "$ROOTFS_DIR/usr/share/chimera/aurora/aurora-wayland-glass.png"
  fi

  [[ -s "$ISO_DIR/boot/visual/aurora-boot.png" ]] || \
    cp -f "$visual/backgrounds/boot.png" "$ISO_DIR/boot/visual/aurora-boot.png" 2>/dev/null || true
  [[ -s "$ISO_DIR/boot/visual/aurora-menu.png" ]] || \
    cp -f "$visual/menus/default.png" "$ISO_DIR/boot/visual/aurora-menu.png" 2>/dev/null || true

  [[ -s "$ISO_DIR/boot/visual/Init.mp4" ]] || {
    log_error "Aurora Init.mp4 was not staged into the ISO."
    return 1
  }
  for stage in spitfire jasper grub koronos; do
    [[ -s "$ISO_DIR/boot/$stage/Init.mp4" ]] || {
      log_error "Aurora Init.mp4 missing from $stage boot stage."
      return 1
    }
    [[ -s "$ISO_DIR/boot/$stage/boot-artwork-manifest.json" ]] || {
      log_error "Boot artwork manifest missing from $stage boot stage."
      return 1
    }
  done
  [[ -s "$ROOTFS_DIR/usr/share/chimera/installer/assets/Init.mp4" ]] || {
    log_error "Aurora Init.mp4 was not staged into the installer."
    return 1
  }
  [[ -s "$ROOTFS_DIR/usr/share/chimera/aurora/assets/Init.mp4" ]] || {
    log_error "Aurora Init.mp4 was not staged into the desktop."
    return 1
  }
}

prepare_apache_ecosystem(){
  [[ "${APACHE_ECOSYSTEM:-1}" == 0 ]] && return 0
  local src="$SCRIPT_DIR/services/apache" dst="$ROOTFS_DIR/opt/chimera/apache"
  [[ -d "$src" ]] || return 0
  mkdir -p "$dst"
  # Verification policy is explicit and strict; release artifacts are not
  # downloaded or executed during image composition.
  export CHIMERA_APACHE_VERIFY_PGP=1
  for f in apache-projects.json README.md apache-sync.py install-apache-ecosystem.sh verify-apache-package.sh; do
    [[ -f "$src/$f" ]] && cp -f "$src/$f" "$dst/"
  done
  chmod +x "$dst/apache-sync.py" "$dst/install-apache-ecosystem.sh" "$dst/verify-apache-package.sh" 2>/dev/null || true
}
prepare_apache(){ prepare_apache_ecosystem; }
stage_features(){
  # Install the bounded discovery worker and its data/configuration into the
  # rootfs so Aurora can run it from a user-level systemd timer at runtime.
  if [[ -f "$SCRIPT_DIR/tools/architecture_discovery/chimera_discovery.py" ]]; then
    mkdir -p "$ROOTFS_DIR/usr/lib/chimera/tools/architecture_discovery" \
             "$ROOTFS_DIR/usr/lib/chimera/config/architecture-discovery" \
             "$ROOTFS_DIR/usr/lib/chimera/config/compatibility" \
             "$ROOTFS_DIR/usr/lib/systemd/user"
    cp -f "$SCRIPT_DIR/tools/architecture_discovery/chimera_discovery.py" "$ROOTFS_DIR/usr/lib/chimera/tools/architecture_discovery/chimera_discovery.py"
    cp -f "$SCRIPT_DIR/tools/architecture_discovery/__init__.py" "$ROOTFS_DIR/usr/lib/chimera/tools/architecture_discovery/__init__.py"
    cp -f "$SCRIPT_DIR/config/architecture-discovery/sources.json" "$ROOTFS_DIR/usr/lib/chimera/config/architecture-discovery/sources.json"
    cp -f "$SCRIPT_DIR/config/compatibility/distro-desktop-profiles.json" "$ROOTFS_DIR/usr/lib/chimera/config/compatibility/distro-desktop-profiles.json"
    if [[ -s "$SCRIPT_DIR/isa/isa_database.json" ]]; then
      mkdir -p "$ROOTFS_DIR/usr/lib/chimera/isa"
      cp -f "$SCRIPT_DIR/isa/isa_database.json" "$ROOTFS_DIR/usr/lib/chimera/isa/isa_database.json"
    fi
    cp -f "$SCRIPT_DIR/packaging/systemd/user/chimera-architecture-discovery.service" "$ROOTFS_DIR/usr/lib/systemd/user/"
    cp -f "$SCRIPT_DIR/packaging/systemd/user/chimera-architecture-discovery.timer" "$ROOTFS_DIR/usr/lib/systemd/user/"
    log_info "Staged Aurora architecture/ISA discovery worker, profile catalog and optional weekly user timer."
  fi
  [[ -x "$SCRIPT_DIR/tools/stage-chimera-runtime.sh" ]] && bash "$SCRIPT_DIR/tools/stage-chimera-runtime.sh" "$ROOTFS_DIR" "$SCRIPT_DIR"
  if [[ "${CHIMERA_BUILD_EMULATORS:-0}" == 1 && -x "$SCRIPT_DIR/tools/build-emulator-stack.sh" ]]; then bash "$SCRIPT_DIR/tools/build-emulator-stack.sh" >> "$LOG_DIR/emulator-build.log" 2>&1 || printf "[WARN] Emulator build staging failed; continuing ISO build.\n" | tee -a "$LOG_DIR/chimera-build.log"; fi
  if [[ -d "$BUILD_DIR/emulators/payloads" ]]; then mkdir -p "$ROOTFS_DIR/usr/lib/chimera/emulators/payloads"; cp -a "$BUILD_DIR/emulators/payloads/." "$ROOTFS_DIR/usr/lib/chimera/emulators/payloads/"; fi
  mkdir -p "$ISO_DIR/system" "$ISO_DIR/desktop" "$ISO_DIR/network" "$ISO_DIR/drivers" "$ISO_DIR/install"
  for d in services userland desktop network installer system/security; do [[ -d "$SCRIPT_DIR/$d" ]] && cp -a "$SCRIPT_DIR/$d" "$ISO_DIR/system/" 2>/dev/null || true; done
  # Ship the authoritative command registry, unified dispatcher and runtime model
  # into both the ISO contract tree and the installed rootfs.
  mkdir -p "$ISO_DIR/system/commands" "$ROOTFS_DIR/usr/share/chimera/commands" "$ROOTFS_DIR/usr/bin"
  for f in system/commands/chimera-command-list.json system/commands/chimera-arabic.json system/commands/compatibility-binary-policy.json system/commands/ss64-command-catalog.json system/commands/command-runtime-capabilities.json tools/commands/os-command-runtime.json; do
    [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$ISO_DIR/system/commands/$(basename "$f")" && cp -f "$SCRIPT_DIR/$f" "$ROOTFS_DIR/usr/share/chimera/commands/$(basename "$f")"
  done
  # Install the alias dispatcher as a *separate* helper. It must never overwrite
  # /usr/bin/chimera-cmd (the compiled multicall ELF) and must never shadow
  # canonical coreutils.
  if [[ -f "$SCRIPT_DIR/tools/commands/chimera-cmd" ]]; then
    mkdir -p "$ROOTFS_DIR/usr/lib/chimera"
    install -m 0755 "$SCRIPT_DIR/tools/commands/chimera-cmd" "$ROOTFS_DIR/usr/lib/chimera/chimera-cmd-alias"
    if [[ ! -e "$ROOTFS_DIR/usr/bin/chimera-cmd" ]]; then
      ln -sfn ../lib/chimera/chimera-cmd-alias "$ROOTFS_DIR/usr/bin/chimera-cmd"
    fi
  fi
  if [[ -f "$SCRIPT_DIR/tools/commands/chimera-run" ]]; then
    install -m 0755 "$SCRIPT_DIR/tools/commands/chimera-run" "$ROOTFS_DIR/usr/bin/chimera-run"
    python3 -m py_compile "$ROOTFS_DIR/usr/bin/chimera-run"
  fi
  [[ -f "$SCRIPT_DIR/system/kore/chimera-unified-runtime-model.json" ]] && cp -f "$SCRIPT_DIR/system/kore/chimera-unified-runtime-model.json" "$ROOTFS_DIR/usr/share/chimera/chimera-unified-runtime-model.json"
  [[ -f "$SCRIPT_DIR/system/shell/chimera-shell.sh" ]] && cp -f "$SCRIPT_DIR/system/shell/chimera-shell.sh" "$ROOTFS_DIR/usr/share/chimera/chimera-shell.sh" && chmod +x "$ROOTFS_DIR/usr/share/chimera/chimera-shell.sh"
  mkdir -p "$ROOTFS_DIR/etc/chimera" "$ROOTFS_DIR/usr/share/chimera"
  [[ -f "$SCRIPT_DIR/system/storage/chimera-storage.conf" ]] && cp -f "$SCRIPT_DIR/system/storage/chimera-storage.conf" "$ROOTFS_DIR/etc/chimera/"
  [[ -f "$SCRIPT_DIR/system/hardware/chimera-hardware-profile.json" ]] && cp -f "$SCRIPT_DIR/system/hardware/chimera-hardware-profile.json" "$ROOTFS_DIR/usr/share/chimera/"
  local aurora_dir aurora_config_dir
  aurora_dir="$ROOTFS_DIR/usr/share/chimera/aurora"
  aurora_config_dir="$aurora_dir/config"
  mkdir -p "$aurora_dir"
  if [[ -e "$aurora_config_dir" && ! -d "$aurora_config_dir" ]] || [[ -L "$aurora_config_dir" ]]; then rm -rf -- "$aurora_config_dir"; fi
  mkdir -p "$aurora_config_dir" "$ROOTFS_DIR/usr/share/chimera/docs"
  # Stage the authoritative capability status and acceptance policy into both the ISO contract tree and installed rootfs.
  mkdir -p "$ISO_DIR/chimera/docs/validation" "$ROOTFS_DIR/usr/share/chimera/docs/validation"
  for f in docs/IMPLEMENTATION_EVIDENCE_AND_REAL_SMP.md docs/validation/capability-evidence.json; do
    [[ -f "$SCRIPT_DIR/$f" ]] || { log_error "Required capability documentation missing: $f"; return 1; }
    cp -f "$SCRIPT_DIR/$f" "$ISO_DIR/chimera/$f"
    cp -f "$SCRIPT_DIR/$f" "$ROOTFS_DIR/usr/share/chimera/$f"
  done
  for f in config/aurora/desktop-parity.json config/aurora/emulators.json config/aurora/free-roms.json config/aurora/emulator-windows.json config/aurora/emulator-associations.json config/chimera/kernel-desktop-parity.json config/chimera/platform-feature-policy.json; do [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$aurora_config_dir/"; done
  [[ -f "$SCRIPT_DIR/docs/kernel-desktop-implementation.md" ]] && cp -f "$SCRIPT_DIR/docs/kernel-desktop-implementation.md" "$ROOTFS_DIR/usr/share/chimera/docs/"
  [[ -f "$SCRIPT_DIR/system/boot/chimera-log.conf" ]] && cp -f "$SCRIPT_DIR/system/boot/chimera-log.conf" "$ROOTFS_DIR/etc/chimera/" || true
  [[ -f "$SCRIPT_DIR/system/aurora/chimera-log-window.desktop" ]] && cp -f "$SCRIPT_DIR/system/aurora/chimera-log-window.desktop" "$ROOTFS_DIR/usr/share/applications/" 2>/dev/null || true
  [[ -f "$SCRIPT_DIR/system/aurora/chimera-log-window.service" ]] && cp -f "$SCRIPT_DIR/system/aurora/chimera-log-window.service" "$ROOTFS_DIR/etc/systemd/system/" 2>/dev/null || true

  # Native Aurora installer UI + hardware-aware installation planner.
  mkdir -p "$ROOTFS_DIR/usr/share/chimera/installer"
  for f in installer/chimera_installer.py installer/installer-manifest.json installer/installation_phases.json installer/installer_profiles.json installer/tool_profiles.json; do
    [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$ROOTFS_DIR/usr/share/chimera/installer/"
  done
  if [[ -f "$SCRIPT_DIR/installer/gui/aurora-installer.sh" ]]; then
    cp -f "$SCRIPT_DIR/installer/gui/aurora-installer.sh" "$ROOTFS_DIR/usr/share/chimera/installer/aurora-installer.sh"
    chmod +x "$ROOTFS_DIR/usr/share/chimera/installer/aurora-installer.sh"
  fi
  [[ -f "$SCRIPT_DIR/system/aurora/chimera-installer.desktop" ]] && cp -f "$SCRIPT_DIR/system/aurora/chimera-installer.desktop" "$ROOTFS_DIR/usr/share/applications/"
}


stage_package_managers(){
  header 'STEP 6: STAGE AURORA PACKAGE MANAGER CENTER'
  local cli="$SCRIPT_DIR/tools/chimera-package-manager.sh"
  local panel="$SCRIPT_DIR/desktop/aurora/package_manager_panel.py"
  local desktop="$SCRIPT_DIR/desktop/aurora/aurora-package-managers.desktop"
  local catalog="$SCRIPT_DIR/appcenter/catalog/package-managers.json"
  local database_catalog="$SCRIPT_DIR/data/registry/databases.json"
  for f in "$cli" "$panel" "$desktop" "$catalog" "$database_catalog"; do
    [[ -s "$f" ]] || { log_error "Package manager payload missing: $f"; return 1; }
  done
  mkdir -p "$ROOTFS_DIR/usr/bin" "$ROOTFS_DIR/usr/share/chimera/aurora" \
    "$ROOTFS_DIR/usr/share/applications" "$ROOTFS_DIR/usr/share/chimera/appcenter" "$ROOTFS_DIR/usr/share/chimera/database" \
    "$ISO_DIR/system/package-managers" "$ISO_DIR/system/desktop/aurora" \
    "$ISO_DIR/system/appcenter/catalog" "$ISO_DIR/system/database"
  install -m 0755 "$cli" "$ROOTFS_DIR/usr/bin/chimera-pkg"
  install -m 0644 "$panel" "$ROOTFS_DIR/usr/share/chimera/aurora/package_manager_panel.py"
  install -m 0644 "$desktop" "$ROOTFS_DIR/usr/share/applications/aurora-package-managers.desktop"
  install -m 0644 "$catalog" "$ROOTFS_DIR/usr/share/chimera/appcenter/package-managers.json"
  install -m 0644 "$database_catalog" "$ROOTFS_DIR/usr/share/chimera/database/databases.json"
  cp -f "$database_catalog" "$ISO_DIR/system/database/databases.json"
  cp -f "$cli" "$ISO_DIR/system/package-managers/chimera-package-manager.sh"
  cp -f "$panel" "$ISO_DIR/system/desktop/aurora/package_manager_panel.py"
  cp -f "$desktop" "$ISO_DIR/system/desktop/aurora/aurora-package-managers.desktop"
  cp -f "$catalog" "$ISO_DIR/system/appcenter/catalog/package-managers.json"
  chmod +x "$ROOTFS_DIR/usr/bin/chimera-pkg"
  bash -n "$ROOTFS_DIR/usr/bin/chimera-pkg"
  python3 -m py_compile "$ROOTFS_DIR/usr/share/chimera/aurora/package_manager_panel.py"
  python3 -m json.tool "$ROOTFS_DIR/usr/share/chimera/appcenter/package-managers.json" >/dev/null
  python3 -m json.tool "$ROOTFS_DIR/usr/share/chimera/database/databases.json" >/dev/null
  python3 -m json.tool "$SCRIPT_DIR/desktop/aurora/waybar/config.jsonc" >/dev/null
  python3 -c 'import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])' "$SCRIPT_DIR/desktop/aurora/labwc/menu.xml"
  log_info "Aurora Package Manager Center staged (APT, DNF, Pacman, Zypper, APK, Snap, Flatpak, Homebrew, Nix, npm, Yarn, pnpm and Corepack)."
  log_info "Free/open-source SQL and NoSQL database catalog staged into Aurora and the ISO payload."
  log_info "Providers remain optional and are detected at runtime; the ISO build will not run remote package-manager installer scripts."
}

build_native_iso_pipeline(){
  if [[ "${CHIMERA_BUILD_NATIVE_ISO_PIPELINE:-1}" == 0 ]]; then
    log_info "Native boot/iso/build-iso.sh pipeline skipped by CHIMERA_BUILD_NATIVE_ISO_PIPELINE=0"
    return 0
  fi
  header 'STEP 11: RUN CANONICAL NATIVE ISO PIPELINE'
  local native_script="$SCRIPT_DIR/boot/iso/build-iso.sh"
  local native_iso="$SCRIPT_DIR/boot/iso/dist/output.iso"
  [[ -x "$native_script" || -f "$native_script" ]] || { log_error "Native ISO pipeline is missing: $native_script"; return 1; }
  # Forward the target system block size through the canonical native ISO boundary.
  # 4096 bytes (4 KiB) is the default; callers may override it explicitly.
  local system_block_size="${CHIMERA_SYSTEM_BLOCK_SIZE:-4096}"
  [[ "$system_block_size" =~ ^[1-9][0-9]*$ ]] || { log_error "Invalid CHIMERA_SYSTEM_BLOCK_SIZE: $system_block_size"; return 2; }
  # Pass the complete artifact path contract explicitly across this process
  # boundary. The child builder re-exports these values to prepare-layout.sh
  # and the Live producer; no stage should silently fall back to $SCRIPT_DIR/build.
  local live_boot_dir="$BUILD_DIR/live-boot"
  log_info "Native ISO artifact paths: BUILD_DIR=$BUILD_DIR LIVE_BOOT=$live_boot_dir"
  CHIMERA_SYSTEM_BLOCK_SIZE="$system_block_size" \
    SYSTEM_BLOCK_SIZE="$system_block_size" \
    CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_BUILD_DIR="$BUILD_DIR" \
    CHIMERA_LIVE_BOOT_DIR="$live_boot_dir" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" \
    bash "$native_script" 2>&1 | tee "$LOG_DIR/native-iso-pipeline.log"
  [[ -s "$native_iso" && -s "$native_iso.sha256" ]] || { log_error "Native ISO pipeline did not produce ISO and SHA-256 checksum"; return 1; }
  (cd "$(dirname "$native_iso")" && sha256sum -c "$(basename "$native_iso").sha256") || { log_error "Native ISO checksum verification failed"; return 1; }
  log_success "Canonical native ISO and checksum verified: $native_iso"
}


stage_games(){ local d="$ISO_DIR/games"; mkdir -p "$d"; [[ -f "$SCRIPT_DIR/appcenter/catalog/game-registry.json" ]] && cp -f "$SCRIPT_DIR/appcenter/catalog/game-registry.json" "$d/"; [[ -f "$SCRIPT_DIR/appcenter/catalog/game-capability-policy.json" ]] && cp -f "$SCRIPT_DIR/appcenter/catalog/game-capability-policy.json" "$d/"; [[ -d "$SCRIPT_DIR/games" ]] && cp -a "$SCRIPT_DIR/games/." "$d/" 2>/dev/null || true; }

create_installer(){
  header 'STEP 7: BUILD NATIVE INSTALLER MEDIA'
  local p
  mkdir -p "$ISO_DIR/install/installer"
  p="$(mktemp -d "$ISO_TMP_DIR/installer.XXXXXX")"

  mkdir -p "$p"/{bin,dev,proc,sys,run,tmp,mnt,target,etc,chimera/installer,lib,lib/firmware,lib/chimera/drivers} "$p/run/chimera" "$p/var/log/mesgs/archive"
  ln -sfn /var/log/mesgs "$p/run/chimera/mesgs"
  ln -sfn mesgs "$p/var/log/messages"

  local bb="$(command -v busybox || true)"
  [[ -n "$bb" ]] || { log_error "busybox is required to build the native installer initramfs"; rm -rf "$p"; exit 1; }
  cp -f "$bb" "$p/bin/busybox"
  for x in sh mount umount switch_root mkdir cat echo ls cp mv rm sleep sync ps top tail date clear sed awk head find grep gzip cpio ip udhcpc nslookup; do
    ln -sf busybox "$p/bin/$x"
  done

  if [[ -f "$SCRIPT_DIR/tools/chimera-installer-runtime.sh" ]]; then
    cp -f "$SCRIPT_DIR/tools/chimera-installer-runtime.sh" "$p/bin/chimera-installer-runtime.sh"
    chmod +x "$p/bin/chimera-installer-runtime.sh"
  fi
  for f in tools/chimera-driver-manager.sh tools/chimera-logrotate.sh; do
    if [[ -f "$SCRIPT_DIR/$f" ]]; then
      cp -f "$SCRIPT_DIR/$f" "$p/bin/"
      chmod +x "$p/bin/$(basename "$f")"
    fi
  done

  for f in \
    "$SCRIPT_DIR/install/installer-contract.json" \
    "$SCRIPT_DIR/install/installation-manifest.json" \
    "$SCRIPT_DIR/installer/installation_phases.json" \
    "$SCRIPT_DIR/installer/installer_profiles.json" \
    "$SCRIPT_DIR/installer/profiles/chimera-installer-features.json" \
    "$SCRIPT_DIR/installer/profiles/filesystem-support.json"; do
    [[ -f "$f" ]] || continue
    cp -f "$f" "$p/chimera/installer/"
  done

  if [[ -f "$SCRIPT_DIR/config/drivers/driver-repositories.json" ]]; then
    mkdir -p "$p/etc/chimera/drivers"
    cp -f "$SCRIPT_DIR/config/drivers/driver-repositories.json" "$p/etc/chimera/drivers/"
  fi
  if [[ -f "$SCRIPT_DIR/config/drivers/driver-policy.json" ]]; then
    mkdir -p "$p/etc/chimera/drivers"
    cp -f "$SCRIPT_DIR/config/drivers/driver-policy.json" "$p/etc/chimera/drivers/"
  fi

  cat > "$p/init" <<'EOF'
#!/bin/sh
set -eu
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
mkdir -p /proc /sys /dev /run /tmp /mnt /target
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
echo "CHIMERA II OS — NATIVE INSTALLER"
echo "[INST] Koronos installer environment online"
echo "[INST] Aurora installation contracts loaded"
if [ -x /bin/chimera-installer-runtime.sh ]; then
  /bin/chimera-installer-runtime.sh /
fi
echo "[INST] Installation environment ready"
exec /bin/sh
EOF
  chmod +x "$p/init"

  (
    cd "$p"
    find . -print0 | cpio --null --format=newc --create --quiet
  ) | gzip -9 > "$ISO_DIR/install/installer/installation.img"

  cp -f "$SCRIPT_DIR/install/installation-manifest.json" "$ISO_DIR/install/installer/" 2>/dev/null || true
  cp -f "$SCRIPT_DIR/install/installer-contract.json" "$ISO_DIR/install/installer/" 2>/dev/null || true
  cp -f "$SCRIPT_DIR/installer/installation_phases.json" "$ISO_DIR/install/installer/" 2>/dev/null || true
  cp -f "$SCRIPT_DIR/installer/installer_profiles.json" "$ISO_DIR/install/installer/" 2>/dev/null || true
  cp -f "$ISO_DIR/install/installer/installation.img" "$ISO_DIR/install/installer/installer-initrd.img"

  rm -rf "$p"
  [[ -s "$ISO_DIR/install/installer/installation.img" ]] || { log_error "Installer initramfs is empty"; exit 1; }
  log_success "Native installer initramfs created: $ISO_DIR/install/installer/installation.img"
}


# ---------------------------------------------------------------------------
# Local (Docker-free) rootfs provider
# ---------------------------------------------------------------------------
chimera_local_default_packages(){
  cat <<'CHIMERA_PKGS'
linux-image-amd64
initramfs-tools
live-boot
live-config
systemd-sysv
systemd-timesyncd
dbus
sudo
locales
console-setup
keyboard-configuration
ca-certificates
curl
wget
nano
vim-tiny
less
procps
psmisc
iproute2
iputils-ping
net-tools
network-manager
wireless-tools
wpasupplicant
openssh-client
rsync
tar
gzip
xz-utils
zstd
zip
unzip
file
findutils
grep
sed
gawk
bash-completion
zsh
fish
tcsh
mksh
ksh
dash
python3
python3-pip
python3-tk
python3-venv
python3-flask
python3-requests
python3-pil
python3-pam
nodejs
npm
perl
ruby
php-cli
lua5.4
tcl
nginx-light
busybox-static
squashfs-tools
parted
dosfstools
mtools
e2fsprogs
grub-pc-bin
grub-efi-amd64-bin
grub2-common
xorg
xwayland
xinit
xterm
sway
swaybg
swayidle
swaylock
labwc
waybar
foot
i3-wm
openbox
cage
greetd
pcmanfm
lxterminal
fonts-dejavu
fonts-liberation
fonts-noto-color-emoji
hicolor-icon-theme
adwaita-icon-theme
pipewire
pipewire-pulse
wireplumber
alsa-utils
pulseaudio-utils
pavucontrol
network-manager-gnome
firefox-esr
evince
eog
file-roller
galculator
mousepad
mednafen
zenity
yad
policykit-1
udisks2
gvfs
CHIMERA_PKGS
}

export_rootfs_local(){
  header 'STEP 2: BUILD LOCAL ROOTFS (DEBOOTSTRAP)'
  cleanup_generated_build_artifacts
  local suite="${CHIMERA_DEBOOTSTRAP_SUITE:-bookworm}"
  local mirror="${CHIMERA_DEBOOTSTRAP_MIRROR:-http://deb.debian.org/debian}"
  local arch="${CHIMERA_DEBOOTSTRAP_ARCH:-amd64}"
  local pkgs=""
  if [[ -n "${CHIMERA_LOCAL_PACKAGES:-}" ]]; then
    pkgs="${CHIMERA_LOCAL_PACKAGES// /,}"
  fi
  mkdir -p "$ROOTFS_DIR"
  rm -rf "${ROOTFS_DIR:?}"/* 2>/dev/null || true
  log_info "debootstrap $suite/$arch -> $ROOTFS_DIR"
  start_watchdog "debootstrap local rootfs"
  set +e
  debootstrap --arch="$arch" --variant=minbase --components=main,contrib,non-free \
    ${pkgs:+--include="$pkgs"} "$suite" "$ROOTFS_DIR" "$mirror" 2>&1 | tee "$LOG_DIR/debootstrap.log"
  local rc="${PIPESTATUS[0]}"
  set -e
  stop_watchdog
  if (( rc != 0 )); then
    log_error "debootstrap failed with exit code $rc; see $LOG_DIR/debootstrap.log"
    exit "$rc"
  fi

  # Basic host identity and resolver
  printf 'chimera\n' > "$ROOTFS_DIR/etc/hostname"
  cat > "$ROOTFS_DIR/etc/hosts" <<'EOF'
127.0.0.1 localhost
127.0.1.1 chimera
::1 localhost ip6-localhost ip6-loopback
EOF
  cp -f /etc/resolv.conf "$ROOTFS_DIR/etc/resolv.conf" 2>/dev/null || true
  mkdir -p "$ROOTFS_DIR/dev" "$ROOTFS_DIR/proc" "$ROOTFS_DIR/sys" "$ROOTFS_DIR/run" \
           "$ROOTFS_DIR/tmp" "$ROOTFS_DIR/var/log" "$ROOTFS_DIR/var/cache/apt/archives/partial"
  chmod 1777 "$ROOTFS_DIR/tmp" 2>/dev/null || true
  mount --bind /dev "$ROOTFS_DIR/dev" 2>/dev/null || true
  mount -t proc proc "$ROOTFS_DIR/proc" 2>/dev/null || true
  mount -t sysfs sysfs "$ROOTFS_DIR/sys" 2>/dev/null || true
  mount --bind /run "$ROOTFS_DIR/run" 2>/dev/null || true

  chroot "$ROOTFS_DIR" /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get update -qq || true' 2>&1 | tee -a "$LOG_DIR/debootstrap.log" || true

  # Resolve the curated package set against the archive, skipping packages that
  # are not published for this suite (e.g. labwc is trixie+, not bookworm).
  if [[ -z "${CHIMERA_LOCAL_PACKAGES:-}" ]]; then
    local avail=() p
    while IFS= read -r p; do
      [[ -n "$p" ]] || continue
      if chroot "$ROOTFS_DIR" apt-cache show "$p" >/dev/null 2>&1; then
        avail+=("$p")
      else
        log_warning "Package not available in $suite: $p (skipped)"
      fi
    done < <(chimera_local_default_packages)
    log_info "Installing ${#avail[@]} curated packages (no-install-recommends)"
    set +e
    chroot "$ROOTFS_DIR" /bin/bash -c "export DEBIAN_FRONTEND=noninteractive; apt-get install -y --no-install-recommends --allow-downgrades ${avail[*]}" 2>&1 | tee -a "$LOG_DIR/debootstrap.log"
    local irc="${PIPESTATUS[0]}"
    if (( irc != 0 )); then
      log_warning "Bulk package install returned $irc; retrying package-by-package"
      for p in "${avail[@]}"; do
        chroot "$ROOTFS_DIR" /bin/bash -c "export DEBIAN_FRONTEND=noninteractive; apt-get install -y --no-install-recommends $p" >/dev/null 2>&1 || log_warning "Could not install: $p"
      done
    fi
    set -e
  fi

  # Enable the services the live/installed system expects.
  for unit in NetworkManager ssh systemd-timesyncd; do
    chroot "$ROOTFS_DIR" systemctl enable "$unit" >/dev/null 2>&1 || true
  done

  # Make sure the live-boot initramfs hooks are present.
  if [[ -x "$ROOTFS_DIR/usr/bin/update-initramfs" ]]; then
    chroot "$ROOTFS_DIR" update-initramfs -u -k all >/dev/null 2>&1 || log_warning 'update-initramfs reported an issue'
  fi

  umount -R "$ROOTFS_DIR/run" 2>/dev/null || true
  umount -R "$ROOTFS_DIR/sys" 2>/dev/null || true
  umount -R "$ROOTFS_DIR/proc" 2>/dev/null || true
  umount -R "$ROOTFS_DIR/dev" 2>/dev/null || true
  rm -rf "$ROOTFS_DIR/var/lib/apt/lists/"* "$ROOTFS_DIR/var/cache/apt/archives/"*.deb 2>/dev/null || true

  [[ -x "$ROOTFS_DIR/bin/bash" ]] || { log_error "Local rootfs is incomplete (no /bin/bash)"; exit 1; }
  log_success "Local rootfs ready: $(du -sh "$ROOTFS_DIR" | awk '{print $1}')"
}

# ---------------------------------------------------------------------------
# STEP 8a: extended application payload (all GitHub apps, GUI wrappers, etc.)
# ---------------------------------------------------------------------------
stage_extended(){
  header 'STEP 8a: EXTENDED APPLICATION PAYLOAD'
  local gen="$SCRIPT_DIR/tools/extended/chimera_extended.py"
  local inst="$SCRIPT_DIR/tools/extended/install-extended.sh"
  local out="$BUILD_DIR/extended-payload"
  [[ -f "$gen" ]] || { log_error "Extended payload generator missing: $gen"; return 1; }
  [[ -f "$inst" ]] || { log_error "Extended payload installer missing: $inst"; return 1; }
  local repos="${CHIMERA_REPOS_DIR:-}"
  if [[ -z "$repos" || ! -d "$repos" ]]; then
    repos="$(cd "$SCRIPT_DIR/.." && pwd)"
    log_warning "CHIMERA_REPOS_DIR not set; scanning $repos"
  fi
  mkdir -p "$out"
  python3 "$gen" --repos "$repos" --out "$out" \
    --build-pyinstaller "${CHIMERA_PYINSTALLER_BUILDS:-0}" 2>&1 | tee "$LOG_DIR/extended-generate.log"
  bash "$inst" "$ROOTFS_DIR" "$out" "$repos" 2>&1 | tee "$LOG_DIR/extended-install.log"
  if [[ "${CHIMERA_DROP_REPOS_AFTER_STAGE:-1}" == 1 && "$repos" == /workspace/gh ]]; then
    log_info "Dropping cloned repositories from build storage after staging into the ISO"
    rm -rf "$repos"
  fi
  log_success "Extended payload installed ($(du -sh "$ROOTFS_DIR/opt/chimera/apps" 2>/dev/null | awk '{print $1}'))"
}

# ---------------------------------------------------------------------------
# STEP 8b: real Linux kernel + initrd for Live CD / Installer / Recovery
# ---------------------------------------------------------------------------
stage_linuxboot(){
  header 'STEP 8b: STAGE LINUX LIVE KERNEL / INITRD'
  local k="" i=""
  for f in "$ROOTFS_DIR"/boot/vmlinuz-*; do [[ -s "$f" ]] && k="$f"; done
  for f in "$ROOTFS_DIR"/boot/initrd.img-*; do [[ -s "$f" ]] && i="$f"; done
  if [[ -z "$k" ]]; then
    log_warning 'No kernel found in rootfs; installing linux-image-amd64'
    if [[ "${CHIMERA_ROOTFS_MODE:-docker}" == "local" ]]; then
      chroot "$ROOTFS_DIR" /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get update -qq && apt-get install -y --no-install-recommends linux-image-amd64 initramfs-tools' 2>&1 | tee -a "$LOG_DIR/linuxboot.log" || true
      for f in "$ROOTFS_DIR"/boot/vmlinuz-*; do [[ -s "$f" ]] && k="$f"; done
      for f in "$ROOTFS_DIR"/boot/initrd.img-*; do [[ -s "$f" ]] && i="$f"; done
    fi
  fi
  [[ -n "$k" ]] || { log_error 'No Linux kernel available to stage for live boot'; return 1; }
  if [[ -z "$i" ]]; then
    log_warning 'No initrd found; generating one with update-initramfs'
    chroot "$ROOTFS_DIR" update-initramfs -c -k all 2>&1 | tee -a "$LOG_DIR/linuxboot.log" || true
    for f in "$ROOTFS_DIR"/boot/initrd.img-*; do [[ -s "$f" ]] && i="$f"; done
  fi
  [[ -n "$i" ]] || { log_error 'No initrd available to stage for live boot'; return 1; }
  mkdir -p "$ISO_DIR/boot"
  cp -f "$k" "$ISO_DIR/boot/vmlinuz"
  cp -f "$i" "$ISO_DIR/boot/initrd.img"
  log_info "Kernel: $(basename "$k") -> /boot/vmlinuz"
  log_info "Initrd: $(basename "$i") -> /boot/initrd.img"

  # Gates menu: desktops, sessions and app launchers.
  mkdir -p "$ISO_DIR/boot/grub"
  cat > "$ISO_DIR/boot/grub/gates.cfg" <<'EOF'
# Chimera II OS - Gates menu (desktops / sessions / apps)
set timeout=30
menuentry "Aurora Desktop (default)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.session=aurora
  initrd /boot/initrd.img
}
menuentry "Sway (Wayland tiling)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.session=sway
  initrd /boot/initrd.img
}
menuentry "labwc (Wayland stacking)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.session=labwc
  initrd /boot/initrd.img
}
menuentry "i3 (X11 tiling)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.session=i3
  initrd /boot/initrd.img
}
menuentry "Openbox (X11 lightweight)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.session=openbox
  initrd /boot/initrd.img
}
menuentry "Cage (single-app kiosk)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.session=cage
  initrd /boot/initrd.img
}
menuentry "Text console (multi-user)" {
  linux /boot/vmlinuz boot=live components quiet splash systemd.unit=multi-user.target
  initrd /boot/initrd.img
}
menuentry "Back to main menu" {
  configfile /boot/grub/grub.cfg
}
EOF

  # Emulators / retro center menu.
  cat > "$ISO_DIR/boot/grub/emulators.cfg" <<'EOF'
# Chimera II OS - Emulators / Retro Center
set timeout=30
menuentry "Retro Center (desktop hub)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.emulator=hub
  initrd /boot/initrd.img
}
menuentry "MAME / arcade" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.emulator=mame
  initrd /boot/initrd.img
}
menuentry "Mednafen (multi-system)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.emulator=mednafen
  initrd /boot/initrd.img
}
menuentry "DOSBox (DOS)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.emulator=dosbox
  initrd /boot/initrd.img
}
menuentry "Sakhr (Arabic retro)" {
  linux /boot/vmlinuz boot=live components quiet splash chimera.emulator=sakhr
  initrd /boot/initrd.img
}
menuentry "Back to main menu" {
  configfile /boot/grub/grub.cfg
}
EOF
  log_success 'Gates and emulator boot menus staged'
}

# ---------------------------------------------------------------------------
# STEP 8c: every *.sh in the repository, syntax-checked + manifest
# ---------------------------------------------------------------------------
stage_scripts(){
  header 'STEP 8c: STAGE ALL SHELL SCRIPTS'
  local dst="$ROOTFS_DIR/opt/chimera/scripts"
  mkdir -p "$dst"
  local n=0 bad=0
  local manifest="$dst/SCRIPTS-MANIFEST.json"
  printf '{\n  "generated": "%s",\n  "scripts": [\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$manifest"
  local first=1
  while IFS= read -r -d '' f; do
    local rel="${f#"$SCRIPT_DIR"/}"
    mkdir -p "$dst/$(dirname "$rel")"
    cp -f "$f" "$dst/$rel"
    chmod +x "$dst/$rel" 2>/dev/null || true
    local ok=true
    if head -n1 "$f" | grep -qE '^#!.*(bash|sh)'; then
      bash -n "$f" 2>/dev/null || ok=false
    fi
    [[ "$ok" == "false" ]] && bad=$((bad+1))
    (( first == 1 )) || printf ',\n' >> "$manifest"
    printf '    {"path": "%s", "syntax_ok": %s}' "$rel" "$ok" >> "$manifest"
    first=0
    n=$((n+1))
  done < <(find "$SCRIPT_DIR" -type f -name '*.sh' -not -path '*/build/*' -print0 | sort -z)
  printf '\n  ],\n  "count": %d,\n  "syntax_failures": %d\n}\n' "$n" "$bad" >> "$manifest"
  cp -f "$manifest" "$ISO_DIR/SCRIPTS-MANIFEST.json" 2>/dev/null || true
  log_success "Staged $n shell scripts ($bad syntax failures) into /opt/chimera/scripts"
}

build_squashfs(){
  header 'STEP 8: BUILD ROOTFS SQUASHFS'
  [[ -d "$ROOTFS_DIR" ]] || { log_error "SquashFS source rootfs is missing: $ROOTFS_DIR"; exit 1; }
  mkdir -p "$ISO_DIR/live" "$ISO_TMP_DIR" "$LOG_DIR"
  if [[ "${CHIMERA_PRUNE_ROOTFS:-1}" != "0" ]]; then
    log_info 'Pruning rootfs caches and build-only files before SquashFS'
    rm -rf "$ROOTFS_DIR/var/cache/apt/archives/"*.deb \
           "$ROOTFS_DIR/var/lib/apt/lists/"* \
           "$ROOTFS_DIR/root/.cache/"* \
           "$ROOTFS_DIR/home/"*/.cache/* \
           "$ROOTFS_DIR/tmp/"* \
           "$ROOTFS_DIR/var/tmp/"* \
           "$ROOTFS_DIR/usr/share/doc/"* \
           "$ROOTFS_DIR/usr/share/man/"* \
           "$ROOTFS_DIR/usr/share/help/"* \
           "$ROOTFS_DIR/usr/share/nodejs/"* \
           "$ROOTFS_DIR/usr/share/perl/"* \
           "$ROOTFS_DIR/usr/share/ruby/"* \
           "$ROOTFS_DIR/usr/lib/gcc/"* \
           "$ROOTFS_DIR/usr/include/"* 2>/dev/null || true
    if [[ -d "$ROOTFS_DIR/usr/share/locale" ]]; then
      find "$ROOTFS_DIR/usr/share/locale" -mindepth 1 -maxdepth 1 -type d \
        ! -name 'en' ! -name 'en_US' ! -name 'en_GB' -exec rm -rf {} + 2>/dev/null || true
    fi
  fi
  local tmp="$ISO_TMP_DIR/filesystem.squashfs.tmp" out="$ISO_DIR/live/filesystem.squashfs"
  local root_bytes free_bytes_now processors rc
  root_bytes="$(du -sB1 "$ROOTFS_DIR" 2>/dev/null | awk '{print $1+0}')"
  free_bytes_now="$(free_bytes "$ISO_TMP_DIR")"
  processors="${CHIMERA_SQUASHFS_PROCESSORS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc 2>/dev/null || echo 2)}"
  [[ "$processors" =~ ^[1-9][0-9]*$ ]] || processors=2
  log_info "SquashFS source: $ROOTFS_DIR ($(numfmt --to=iec --suffix=B "$root_bytes" 2>/dev/null || printf '%s bytes' "$root_bytes"))"
  log_info "SquashFS temp: $tmp; free space on temp filesystem: $(numfmt --to=iec --suffix=B "$free_bytes_now" 2>/dev/null || printf '%s bytes' "$free_bytes_now")"
  log_info "SquashFS compression: zstd; processors: $processors"
  if [[ ! "$free_bytes_now" =~ ^[0-9]+$ ]] || (( free_bytes_now < 1073741824 )); then
    log_error "Less than 1 GiB free on the SquashFS temporary filesystem; free space or choose another build storage with --storage."
    exit 1
  fi
  rm -f "$tmp"
  start_watchdog "mksquashfs root filesystem"
  set +e
  mksquashfs "$ROOTFS_DIR" "$tmp" -comp zstd -noappend -processors "$processors" -progress 2>&1 | tee "$LOG_DIR/mksquashfs.log"
  rc="${PIPESTATUS[0]}"
  set -e
  stop_watchdog
  if ((rc!=0)); then
    log_error "mksquashfs failed with exit code $rc; recent diagnostics:"
    tail -n 60 "$LOG_DIR/mksquashfs.log" 2>/dev/null || true
    exit "$rc"
  fi
  [[ -s "$tmp" ]] || { log_error "SquashFS output is empty: $tmp"; exit 1; }
  mv -f "$tmp" "$out"
  log_success "SquashFS image created: $out ($(du -h "$out" | awk '{print $1}'))"
}

build_iso(){
  header 'STEP 9: BUILD BOOTABLE ISO'

  local iso="$ISO_OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}-${TARGET_ARCH}.iso"
  local source_bytes=0
  local free_bytes_now=0
  local required_bytes=0
  local safety_bytes=$((2 * 1024 * 1024 * 1024))

  rm -f "$iso" "$iso.sha256"

  # build-boot-artifacts.sh creates the removable-media UEFI loader in the
  # ISO staging tree. Never delete EFI/BOOT here: doing so silently discarded
  # BOOTX64.EFI immediately before grub-mkrescue packaged the tree.
  local uefi_loader="$ISO_DIR/EFI/BOOT/BOOTX64.EFI"
  local generated_uefi_loader="$BUILD_DIR/boot-artifacts/uefi/BOOTX64.EFI"
  if [[ ! -s "$uefi_loader" && -s "$generated_uefi_loader" ]]; then
    mkdir -p "$ISO_DIR/EFI/BOOT"
    cp -f "$generated_uefi_loader" "$uefi_loader"
    log_info "Restored staged UEFI loader from boot-artifact cache."
  fi
  if [[ ! -s "$uefi_loader" ]]; then
    log_error "UEFI loader is missing: $uefi_loader"
    log_error "Expected tools/build-boot-artifacts.sh to create $generated_uefi_loader."
    exit 1
  fi
  log_info "UEFI removable-media loader ready: $uefi_loader"

  source_bytes="$(du -sB1 "$ISO_DIR" 2>/dev/null | awk '{print $1}')"
  free_bytes_now="$(free_bytes "$ISO_OUTPUT_DIR")"

  # Allow room for ISO metadata, GRUB structures, temporary xorriso
  # allocation and filesystem overhead.
  required_bytes=$((source_bytes + safety_bytes))

  log_info "ISO staging size: $((source_bytes / 1024 / 1024 / 1024)) GiB"
  log_info "Current output free space: $((free_bytes_now / 1024 / 1024 / 1024)) GiB"
  log_info "Required output space: $((required_bytes / 1024 / 1024 / 1024)) GiB"

  if [[ "${CHIMERA_SKIP_SPACE_CHECKS:-0}" == 1 ]]; then
    log_info "Final ISO space check skipped (CHIMERA_SKIP_SPACE_CHECKS=1)."
  elif (( free_bytes_now < required_bytes )); then
    log_error "Insufficient space for final ISO."
    log_error "Required: $((required_bytes / 1024 / 1024 / 1024)) GiB"
    log_error "Available: $((free_bytes_now / 1024 / 1024 / 1024)) GiB"
    log_error "Use --storage /mnt/<larger-drive> or --storage-auto."
    exit 1
  fi

  grub-mkrescue \
      -o "$iso" \
      "$ISO_DIR" \
      2>&1 | tee "$LOG_DIR/grub-mkrescue.log"

  [[ -s "$iso" ]] || {
    log_error 'ISO generation produced no file'
    exit 1
  }

  sha256sum "$iso" > "$iso.sha256"

  log_success "ISO: $iso"
}
verify_iso(){
  header 'STEP 10: VERIFY ISO BOOT STRUCTURE'
  local iso="$ISO_OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}-${TARGET_ARCH}.iso"
  [[ -s "$iso" ]] || { log_error 'ISO missing'; exit 1; }
  xorriso -indev "$iso" -report_el_torito plain | tee "$LOG_DIR/iso-el-torito.log"
  grep -qi 'El Torito' "$LOG_DIR/iso-el-torito.log" || { log_error 'ISO has no El Torito boot catalog'; exit 1; }
  grep -qi 'BIOS' "$LOG_DIR/iso-el-torito.log" || { log_error 'ISO has no BIOS El Torito boot entry'; exit 1; }
  grep -qi 'UEFI' "$LOG_DIR/iso-el-torito.log" || { log_error 'ISO has no UEFI El Torito boot entry'; exit 1; }
  grep -q 'multiboot2 /boot/koronos/koronos.elf' "$ISO_DIR/boot/grub/grub.cfg" || { log_error 'GRUB does not load the staged Koronos ELF through Multiboot2'; exit 1; }
  grep -q 'module2 /boot/live/chimera-live-initramfs.img' "$ISO_DIR/boot/grub/grub.cfg" || { log_error 'GRUB live handoff is missing the live initramfs module'; exit 1; }
  xorriso -indev "$iso" -find /boot/grub/grub.cfg -type f | tee "$LOG_DIR/iso-grub-files.log"
  xorriso -indev "$iso" -find /boot/koronos/koronos.elf -type f | tee -a "$LOG_DIR/iso-grub-files.log"
  xorriso -indev "$iso" -find /boot/recovery/chimera-recovery-initramfs.img -type f | tee -a "$LOG_DIR/iso-grub-files.log"

  # Verify the complete graphical boot/installer contract, not only the kernel.
  local required_iso_paths=(
    /boot/grub/grub.cfg
    /boot/koronos/koronos.elf
    /boot/live/chimera-live-initramfs.img
    /boot/live/live-manifest.json
    /boot/grub/aurora-theme.txt
    /boot/visual/aurora-boot.png
    /boot/visual/aurora-menu.png
    /boot/visual/aurora-installer.png
    /boot/visual/aurora-recovery.png
    /boot/visual/aurora-live.png
    /boot/visual/Init.mp4
    /boot/visual/chimera-intro.mp4
    /boot/jasper/jasper.cfg
    /boot/jasper/install.cfg
    /boot/jasper/retro.cfg
    /boot/installation/menu.cfg
    /boot/spitfire/spitfire-menu.cfg
    /EFI/BOOT/BOOTX64.EFI
    /install/installer/installation.img
    /install/installer/installation-manifest.json
    /install/installer/installer-contract.json
  )
  local required_path
  for required_path in "${required_iso_paths[@]}"; do
    if ! xorriso -indev "$iso" -find "$required_path" -type f | grep -q .; then
      log_error "ISO is missing required boot/runtime asset: $required_path"
      exit 1
    fi
  done
  xorriso -indev "$iso" -find /EFI/BOOT/BOOTX64.EFI -type f | tee "$LOG_DIR/iso-uefi-files.log"
  log_success "BIOS/UEFI boot files and graphical boot, installer and Aurora asset contract verified."
  if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    log_info 'Launching a non-asserting QEMU firmware smoke probe; timeout is not proof of boot success.'
    local qemu_probe_rc=0
    timeout "${CHIMERA_QEMU_BOOT_TIMEOUT:-20}" qemu-system-x86_64 -accel tcg -m 512 -cdrom "$iso" -display none -serial none -monitor none -no-reboot -no-shutdown >"$LOG_DIR/qemu-firmware-probe.log" 2>&1 || qemu_probe_rc=$?
    if (( qemu_probe_rc == 124 )); then
      log_warning 'QEMU smoke probe reached its timeout; no boot milestone was asserted. See qemu-firmware-probe.log.'
    elif (( qemu_probe_rc != 0 )); then
      log_warning "QEMU smoke probe exited with status $qemu_probe_rc; see qemu-firmware-probe.log."
    else
      log_info 'QEMU smoke probe exited cleanly, but userspace readiness still requires a dedicated observable acceptance test.'
    fi
  else
    log_warning 'QEMU is unavailable; ISO verification is structural only and does not assert a runtime boot.'
  fi
}

report_build(){
  header 'CHIMERA BUILD REPORT'
  log_success "Build directory: $BUILD_DIR"
  log_success "Rootfs: $ROOTFS_DIR"
  log_success "ISO output: $ISO_OUTPUT_DIR"
  log_success "Chimera II OS comprehensive build completed."
  BUILD_SUCCEEDED=1
}

scan_isa_and_commands_before_network_crawl(){
  local isa_header="$SCRIPT_DIR/kernel/generated/chimera_isa_registry.generated.h"
  local isa_db="$SCRIPT_DIR/isa/isa_database.json"
  log_info "Scanning local ISA registry before any SS64 network crawl"
  [[ -s "$isa_db" ]] || { log_error "Canonical ISA database missing: $isa_db"; return 1; }
  log_info "Regenerating the kernel ISA header from the canonical database before network access"
  python3 "$SCRIPT_DIR/tools/isa/generate_registry.py" || { log_error "ISA registry generation failed"; return 1; }
  log_info "Generated ISA header: $isa_header"
  grep -E 'CHIMERA_ISA|ISA_REGISTRY|instruction|mnemonic' "$isa_header" | head -n 3 || true
  [[ -s "$isa_header" ]] || { log_error "ISA registry header unavailable after generation"; return 1; }
  [[ -s "$isa_db" ]] || { log_error "Canonical ISA database missing: $isa_db"; return 1; }
  python3 - "$isa_db" "$isa_header" "$SCRIPT_DIR/isa/world_architectures.json" <<'PYISA'
import json,sys
from pathlib import Path
db=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
world=json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
arches=db.get("architectures",[]); rows=db.get("instructions",[])
hierarchy=world.get("processor_hierarchy",{}).get("families",[])
if not arches or not rows: raise SystemExit("Canonical ISA database is empty")
if not hierarchy: raise SystemExit("Processor/chip hierarchy metadata is missing")
if any(not x.get("vendor") or not x.get("family") or not x.get("source") for x in hierarchy):
    raise SystemExit("Processor hierarchy entry missing vendor/family/source")
print(f"[ISA] architectures={len(arches)} encoding templates={len(rows)} processor families={len(hierarchy)}")
PYISA
  log_info "Validating and generating binary/hex ISA sample artifacts"
  python3 "$SCRIPT_DIR/tools/validate_isa_catalog.py" || { log_error "ISA sample validation failed"; return 1; }
  python3 "$SCRIPT_DIR/tools/isa/generate_encoding_artifacts.py" || { log_error "ISA encoding artifact generation failed"; return 1; }
  local universal_args=()
  [[ -s "$SCRIPT_DIR/isa/sources/imports/riscv-opcodes.json" ]] && universal_args+=(--input "$SCRIPT_DIR/isa/sources/imports/riscv-opcodes.json")
  python3 "$SCRIPT_DIR/tools/isa/build_universal_catalog.py" "${universal_args[@]}" || { log_error "Universal ISA catalog generation failed"; return 1; }
  [[ -s "$SCRIPT_DIR/isa/generated/isa-encoding-samples.json" ]] || { log_error "ISA sample JSON missing"; return 1; }
  [[ -s "$SCRIPT_DIR/isa/generated/isa-encoding-registry.json" ]] || { log_error "ISA encoding registry JSON missing"; return 1; }
  [[ -s "$SCRIPT_DIR/kernel/generated/chimera_isa_encoding_samples.generated.h" ]] || { log_error "ISA sample header missing"; return 1; }
  log_info "Scanning cached command catalogs before crawling SS64"
  [[ -s "$SCRIPT_DIR/system/commands/ss64-command-catalog.json" ]] && log_info "SS64 catalog cache exists; crawler will merge new discoveries"
  if [[ "${CHIMERA_SKIP_SS64_CRAWL:-0}" != 1 ]]; then
    log_info "SS64 crawl limits: pages/platform=${CHIMERA_SS64_MAX_PAGES:-500}, depth=${CHIMERA_SS64_MAX_DEPTH:-10}, timeout=${CHIMERA_SS64_TIMEOUT:-10}s, platform budget=${CHIMERA_SS64_PLATFORM_BUDGET:-120}s" 
    CHIMERA_SS64_PLATFORM_BUDGET="${CHIMERA_SS64_PLATFORM_BUDGET:-90}" python3 "$SCRIPT_DIR/tools/commands/crawl_ss64.py" --max-pages "${CHIMERA_SS64_MAX_PAGES:-80}" --max-depth "${CHIMERA_SS64_MAX_DEPTH:-2}" --timeout "${CHIMERA_SS64_TIMEOUT:-10}" --retries "${CHIMERA_SS64_RETRIES:-0}"
  else
    log_info "SS64 network crawl skipped by CHIMERA_SKIP_SS64_CRAWL=1"
  fi
  log_info "Reconciling native, shell-builtin, and compatibility-provider command inventory"
  python3 "$SCRIPT_DIR/tools/commands/generate_runtime_manifest.py" || { log_error "Command capability manifest generation failed"; return 1; }
  [[ -s "$SCRIPT_DIR/system/commands/command-runtime-capabilities.json" ]] || { log_error "Command capability manifest missing"; return 1; }
  python3 - "$SCRIPT_DIR/system/commands/command-runtime-capabilities.json" <<'PYCOMMANDS'
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows=d.get("commands",[])
names=[str(x.get("name","")).casefold() for x in rows]
if not rows or len(names)!=len(set(names)): raise SystemExit("Command manifest empty or contains duplicate names")
if any(not x.get("mode") or not x.get("provider") for x in rows): raise SystemExit("Command missing runtime/provider classification")
expected_native = {"pwd", "echo", "ls", "cp", "mv", "touch", "mkdir", "rm", "cat", "clear", "whoami", "hostname", "date", "true", "false"}
actual_native = {str(x.get("name", "")).casefold() for x in rows if x.get("mode") == "native"}
if actual_native != expected_native:
    missing = sorted(expected_native - actual_native)
    extra = sorted(actual_native - expected_native)
    raise SystemExit(
        "Native multicall contract mismatch: "
        f"expected={len(expected_native)} actual={len(actual_native)} "
        f"missing={missing} extra={extra}"
    )
if d.get("mode_counts",{}).get("native") != len(expected_native):
    raise SystemExit("Native command mode_counts does not match the compiled multicall contract")
print(f"[COMMANDS] catalogued={len(rows)} native={len(actual_native)} compatibility={d['mode_counts'].get('compatibility-provider-required',0)}")
PYCOMMANDS
}
build_command_runtime(){
  log_info "Compiling and staging native command multicall binary and compatibility registry"
  CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" bash "$SCRIPT_DIR/tools/build-chimera-command-compat.sh"
  [[ -x "$ROOTFS_DIR/usr/bin/chimera-cmd" ]] || { log_error "Native command binary was not generated"; return 1; }
  log_info "Native command binary staged at $ROOTFS_DIR/usr/bin/chimera-cmd"
}
build_native_sdk(){
  header 'FULL BUILD: COMPILE, TEST AND STAGE CHIMERA SDK'
  local sdk_src="$SCRIPT_DIR/sdk" sdk_build="$BUILD_DIR/sdk" sdk_dest="$ROOTFS_DIR/opt/chimera-sdk"
  [[ -s "$sdk_src/CMakeLists.txt" ]] || { log_error "SDK CMake project is missing: $sdk_src/CMakeLists.txt"; return 1; }
  command -v cmake >/dev/null 2>&1 || { log_error "CMake is required for --full SDK compilation"; return 2; }
  command -v ctest >/dev/null 2>&1 || { log_error "CTest is required for --full SDK validation"; return 2; }
  rm -rf -- "$sdk_build"
  mkdir -p "$sdk_build" "$sdk_dest" "$ISO_DIR/install/sdk"
  cmake -S "$sdk_src" -B "$sdk_build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/chimera-sdk
  cmake --build "$sdk_build" --parallel "${CHIMERA_BUILD_JOBS:-2}"
  ctest --test-dir "$sdk_build" --output-on-failure
  DESTDIR="$ROOTFS_DIR" cmake --install "$sdk_build"
  mkdir -p "$ISO_DIR/install/sdk/source"
  cp -a "$sdk_src/." "$ISO_DIR/install/sdk/source/"
  for manifest in manifest.json SDK_BUILD_MANIFEST.json runtime-profiles.json; do
    [[ -s "$sdk_src/$manifest" ]] && cp -f "$sdk_src/$manifest" "$ISO_DIR/install/sdk/"
  done
  [[ -s "$sdk_dest/share/chimera/sdk/SDK_BUILD_MANIFEST.json" ]] || { log_error "Installed SDK build manifest missing from rootfs"; return 1; }
  log_success "Native SDK compiled, CTest-validated, installed into rootfs and staged in ISO."
}

main(){
  # --docker-only is a true Docker pipeline, not a full ISO build with a flag ignored.
  if [[ "$BUILD_ISO" == 0 ]]; then
    command -v docker >/dev/null 2>&1 || { log_error "Docker CLI is required for --docker-only"; return 2; }
    run_stage docker build_docker
    run_stage docker-publish push_docker_image
    BUILD_SUCCEEDED=1
    log_success "Docker-only pipeline completed."
    return 0
  fi
  if [[ "$BUILD_DOCKER" == 0 && "${CHIMERA_ROOTFS_MODE:-docker}" != "local" ]]; then
    docker image inspect "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null 2>&1 || {
      log_error "--iso-only requires an existing Docker image: $DOCKER_IMAGE:$DOCKER_TAG"
      return 2
    }
  fi
  if [[ "$DOS_FETCH_ON_BUILD" == 1 ]]; then
    export CHIMERA_DOS_FETCH_ON_BUILD=1
  fi
  if [[ "$REFRESH_ONLINE_CATALOGS" == 1 ]]; then
    log_info "Discovering legacy DOS applications and games from the official FreeDOS catalog"
    python3 "$SCRIPT_DIR/tools/commands/dos-payload-builder.py" discover --output "$BUILD_DIR/dos-online-discovery.json" || { log_error "DOS online discovery failed"; return 1; }
    log_info "Refreshing official ISA and OS-command indexes from the internet"
    python3 "$SCRIPT_DIR/tools/catalogs/refresh_online_catalogs.py" --refresh || { log_error "Online catalog refresh failed"; return 1; }
    log_info "Discovering official and machine-readable ISA source entry points"
    python3 "$SCRIPT_DIR/tools/isa/crawl_sources.py" --refresh || { log_error "ISA source discovery failed"; return 1; }
    log_info "Importing source-backed RISC-V opcode masks"
    python3 "$SCRIPT_DIR/tools/isa/import_riscv_opcodes.py" || { log_error "RISC-V opcode import failed"; return 1; }
  fi
  if [[ -f "$SCRIPT_DIR/tools/catalogs/merge_online_catalogs.py" ]]; then
    log_info "Appending source-backed ISA discoveries and command references to the local catalogs"
    python3 "$SCRIPT_DIR/tools/catalogs/merge_online_catalogs.py" || { log_error "Online catalog merge failed"; return 1; }
  fi
  scan_isa_and_commands_before_network_crawl
  [[ "$CLEAN_STATE" == 1 ]] && state_reset
  CURRENT_STAGE="preflight"
  preflight
  check_deps
  CURRENT_STAGE=""
  local completed="$(state_get)"
<<<<<<< HEAD
  for stage in docker rootfs commands docker-publish boot installer branding apache features package-managers games extended linuxboot scripts squashfs iso verify native-iso report; do
=======
  local -a build_stages=(docker rootfs commands)
  if [[ "$FULL_BUILD" == 1 ]]; then
    build_stages+=(sdk)
    log_info "--full enabled: clean rebuild plus native SDK compilation, CTest and ISO staging."
  fi
  build_stages+=(docker-publish boot installer branding apache features package-managers games squashfs iso verify native-iso report)
  for stage in "${build_stages[@]}"; do
>>>>>>> 80664aff1 (build: add clean --full SDK build and ISO staging)
    if [[ "$stage" == docker && "$BUILD_DOCKER" == 0 ]]; then log_info "Skipping Docker build for --iso-only"; continue; fi
    if [[ "$stage" == docker-publish && "$BUILD_DOCKER" == 0 ]]; then log_info "Skipping Docker publish for --iso-only"; continue; fi
    if [[ "$RESUME_BUILD" == 1 && -n "$completed" ]] && state_done "$completed" "$stage"; then log_info "Skipping completed stage: $stage"; continue; fi
    case "$stage" in
      docker) run_stage docker build_docker;;
      docker-publish) run_stage docker-publish push_docker_image;;
      rootfs) run_stage rootfs export_rootfs;;
      commands) run_stage commands build_command_runtime;;
      sdk) run_stage sdk build_native_sdk;;
      boot) run_stage boot create_boot_menu;;
      installer) run_stage installer create_installer;;
      branding) run_stage branding prepare_branding;;
      apache) run_stage apache prepare_apache;;
      features) run_stage features stage_features;;
      package-managers) run_stage package-managers stage_package_managers;;
      games) run_stage games stage_games;;
      extended) run_stage extended stage_extended;;
      linuxboot) run_stage linuxboot stage_linuxboot;;
      scripts) run_stage scripts stage_scripts;;
      squashfs) run_stage squashfs build_squashfs;;
      iso) run_stage iso build_iso;;
      verify) run_stage verify verify_iso;;
      native-iso) run_stage native-iso build_native_iso_pipeline;;
      report) run_stage report report_build;;
    esac
    completed="$stage"
  done
  cleanup_final_success_artifacts
}

trap 'rc=$?; stop_watchdog || true; if ((rc!=0)); then log_error "Build stopped during stage: ${CURRENT_STAGE:-unknown}"; log_debug "Failure command omitted to avoid exposing command-line secrets"; log_error "Failure source: ${BASH_SOURCE[0]:-unknown}:${BASH_LINENO[0]:-0}"; log_error "Bash version: ${BASH_VERSION}; PID: ${BASHPID:-unknown}"; process_snapshot || true; printf "%s\n" "${CURRENT_STAGE:-unknown}" > "$FAILED_FILE" 2>/dev/null || log_warning "Could not persist failed-stage marker at $FAILED_FILE"; fi; exit "$rc"' EXIT
main "$@"
