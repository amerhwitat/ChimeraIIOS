#!/usr/bin/env bash
set -Eeuo pipefail

# Chimera II OS comprehensive ISO builder.
# The SquashFS stage is deliberately non-append and transactionally replaces
# the final image only after a successful build. This prevents duplicate root
# entries such as bin_1, boot_1, etc. when a resumable build is retried.

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
WATCHDOG_PID=""
STATE_FILE="${CHIMERA_BUILD_STATE_FILE:-$BUILD_DIR/.chimera-build-state}"
FAILED_FILE="${CHIMERA_FAILED_STAGE_FILE:-$BUILD_DIR/.chimera-failed-stage}"
RESUME_BUILD=0
CLEAN_STATE=0
STORAGE_AUTO="${CHIMERA_STORAGE_AUTO:-0}"
STORAGE_PROMPT="${CHIMERA_STORAGE_PROMPT:-1}"
CURRENT_STAGE=""
BUILD_SUCCEEDED=0

mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"
export TMPDIR="$ISO_TMP_DIR" MTOOLS_SKIP_CHECK=1

log_info(){ echo -e "${BLUE}[INFO]${NC} $*"; }
log_success(){ echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning(){ echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error(){ echo -e "${RED}[ERROR]${NC} $*" >&2; }

log_file(){ mkdir -p "$LOG_DIR"; printf "[%s] %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG_DIR/chimera-build.log"; }
log_both(){ log_info "$*"; log_file "$*"; }
process_snapshot(){
  mkdir -p "$LOG_DIR"
  {
    echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) PROCESS SNAPSHOT ====="
    echo "-- host processes --"
    ps -eo pid,ppid,stat,%cpu,%mem,etime,cmd --sort=-%cpu 2>/dev/null || true
    echo "-- process tree --"
    pstree -ap $ 2>/dev/null | head -n 80 || true
    echo "-- docker containers --"
    docker ps -a --no-trunc 2>/dev/null || true
    echo "-- docker disk usage --"
    docker system df 2>/dev/null || true
    echo "-- storage --"
    df -h "$BUILD_DIR" "$ISO_OUTPUT_DIR" 2>/dev/null || true
    echo "-- build directories --"
    du -sh "$BUILD_DIR"/* "$ISO_DIR"/* 2>/dev/null | sort -h | tail -n 20 || true
  } >> "$LOG_DIR/process-snapshots.log" 2>&1
}
start_watchdog(){
  LOG_DIR="$BUILD_DIR/logs"
  mkdir -p "$LOG_DIR"
  stop_watchdog || true
  local label="$1" interval="${CHIMERA_BUILD_WATCHDOG_INTERVAL:-5}"
  (while :; do log_both "[WATCHDOG] $label still active"; process_snapshot; sleep "$interval"; done) &
  WATCHDOG_PID=$!
}
stop_watchdog(){
  if [[ -n "$WATCHDOG_PID" ]]; then
    kill "$WATCHDOG_PID" 2>/dev/null || true
    wait "$WATCHDOG_PID" 2>/dev/null || true
    WATCHDOG_PID=""
  fi
}

header(){ printf '\n==================================================================\n%s\n==================================================================\n' "$*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --docker-only) BUILD_ISO=0; shift;;
    --iso-only) BUILD_DOCKER=0; shift;;
    --resume) RESUME_BUILD=1; shift;;
    --clean-state) CLEAN_STATE=1; shift;;
    --storage-auto) STORAGE_AUTO=1; shift;;
    --no-storage-prompt) STORAGE_PROMPT=0; shift;;
    --storage) [[ -n "${2:-}" ]] || { log_error '--storage requires a path'; exit 2; }; export CHIMERA_BUILD_STORAGE_ROOT="$2"; shift 2;;
    --tag) DOCKER_TAG="$2"; shift 2;;
    --background) export CHIMERA_AURORA_ASSET="$2"; shift 2;;
    --skip-apache) export APACHE_ECOSYSTEM=0; shift;;
    --apache-ecosystem) export APACHE_ECOSYSTEM=1; shift;;
    --push) export CHIMERA_PUSH=1; shift;;
    --registry) export REGISTRY_NAME="$2"; shift 2;;
    *) log_error "Unknown option: $1"; exit 2;;
  esac
done

if [[ -n "${CHIMERA_BUILD_STORAGE_ROOT:-}" ]]; then
  root="${CHIMERA_BUILD_STORAGE_ROOT%/}"
  BUILD_DIR="$root/chimera-build"; ISO_DIR="$BUILD_DIR/iso"; ROOTFS_DIR="$BUILD_DIR/rootfs"; ISO_OUTPUT_DIR="$root/chimera-output"; ISO_TMP_DIR="$BUILD_DIR/logs/chimera-iso-build"; STATE_FILE="$BUILD_DIR/.chimera-build-state"; FAILED_FILE="$BUILD_DIR/.chimera-failed-stage"
  mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"
  export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" TMPDIR="$ISO_TMP_DIR"
fi

free_bytes(){ df -PB1 "$1" 2>/dev/null | awk 'NR==2{print $4}'; }
free_gib(){ local n="$(free_bytes "$1")"; [[ "$n" =~ ^[0-9]+$ ]] && echo $((n/1024/1024/1024)) || echo 0; }
is_wsl(){ grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null || [[ -n "${WSL_INTEROP:-}" ]] || [[ -d /mnt/wsl ]]; }

choose_storage(){
  local need="${1:-20}"; local best="" free path
  if is_wsl; then
    for path in /mnt/*; do [[ -d "$path" ]] || continue; free="$(free_gib "$path")"; ((free>=need)) && [[ "$path" != /mnt/c ]] && { best="$path"; break; }; done
  else
    while read -r path; do free="$(free_gib "$path")"; ((free>=need)) && { best="$path"; break; }; done < <(findmnt -rn -o TARGET 2>/dev/null | grep -Ev '^/(proc|sys|dev|run)(/|$)')
  fi
  [[ -n "$best" ]] || return 1
  BUILD_DIR="$best/chimera-build"; ISO_DIR="$BUILD_DIR/iso"; ROOTFS_DIR="$BUILD_DIR/rootfs"; ISO_OUTPUT_DIR="$best/chimera-output"; ISO_TMP_DIR="$BUILD_DIR/logs/chimera-iso-build"; STATE_FILE="$BUILD_DIR/.chimera-build-state"; FAILED_FILE="$BUILD_DIR/.chimera-failed-stage"
  mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"
  export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" TMPDIR="$ISO_TMP_DIR"
  log_success "Build storage switched to $best"
}

preflight(){
  header 'LARGE ISO / STORAGE PREFLIGHT'
  local rg="$(free_gib "$ROOTFS_DIR")" og="$(free_gib "$ISO_OUTPUT_DIR")"
  log_info "Rootfs filesystem free: ${rg} GiB"
  log_info "ISO output filesystem free: ${og} GiB"
  if ((rg<20 || og<20)); then
    if [[ "$STORAGE_AUTO" == 1 ]]; then choose_storage 20 || { log_error 'No suitable larger storage found'; exit 1; }
    elif [[ "$STORAGE_PROMPT" == 1 && -t 0 ]]; then read -r -p 'Storage path for large Chimera build: ' p; [[ -d "$p" ]] && { export CHIMERA_BUILD_STORAGE_ROOT="$p"; root="${p%/}"; BUILD_DIR="$root/chimera-build"; ISO_DIR="$BUILD_DIR/iso"; ROOTFS_DIR="$BUILD_DIR/rootfs"; ISO_OUTPUT_DIR="$root/chimera-output"; ISO_TMP_DIR="$BUILD_DIR/logs/chimera-iso-build"; STATE_FILE="$BUILD_DIR/.chimera-build-state"; FAILED_FILE="$BUILD_DIR/.chimera-failed-stage"; mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"; export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" TMPDIR="$ISO_TMP_DIR"; } || { log_error 'No storage selected'; exit 1; }; else log_error 'Insufficient storage; use --storage /mnt/d or --storage-auto'; exit 1; fi
  fi
  command -v mksquashfs >/dev/null || { log_error 'mksquashfs is required'; exit 2; }
}

state_get(){ [[ -f "$STATE_FILE" ]] && sed -n 's/^completed=//p' "$STATE_FILE" | tail -1 || true; }
state_mark(){ printf 'schema=2\ncompleted=%s\nupdated=%s\n' "$1" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$STATE_FILE"; }
state_reset(){ rm -f "$STATE_FILE" "$FAILED_FILE"; }
state_done(){
  local c="$1" t="$2"; [[ -n "$c" ]] || return 1
  local order='docker rootfs boot branding apache features games squashfs iso verify report'; local ci ti
  ci=$(awk -v x="$c" '{for(i=1;i<=NF;i++)if($i==x)print i}' <<< "$order"); ti=$(awk -v x="$t" '{for(i=1;i<=NF;i++)if($i==x)print i}' <<< "$order")
  [[ -n "$ci" && -n "$ti" && "$ci" -ge "$ti" ]]
}
run_stage(){ CURRENT_STAGE="$1"; log_info "Starting stage: $1"; "$2"; state_mark "$1"; CURRENT_STAGE=""; }

check_deps(){
  header 'BUILD DEPENDENCIES'
  command -v docker >/dev/null || { log_error 'Docker is required'; exit 2; }
  command -v cpio >/dev/null || { log_error 'cpio is required'; exit 2; }
  command -v grub-mkrescue >/dev/null || { log_error 'grub-mkrescue is required'; exit 2; }
  command -v xorriso >/dev/null || { log_error 'xorriso is required'; exit 2; }
  command -v busybox >/dev/null || log_warning 'busybox unavailable on host; Docker rootfs copy may provide it'
  docker info >/dev/null 2>&1 || { log_error 'Docker daemon unavailable'; exit 2; }
}

build_docker(){
  header 'STEP 1: BUILD DOCKER IMAGE'
  [[ -f "$SCRIPT_DIR/Dockerfile.comprehensive" ]] || { log_error 'Dockerfile.comprehensive not found'; exit 1; }
  start_watchdog "Docker BuildKit image build"; set +e
  BUILDKIT_PROGRESS=plain docker build --progress=plain -f "$SCRIPT_DIR/Dockerfile.comprehensive" -t "$DOCKER_IMAGE:$DOCKER_TAG" -t "$DOCKER_IMAGE:latest" "$SCRIPT_DIR" 2>&1 | tee "$LOG_DIR/docker-build.log"
  local rc="${PIPESTATUS[0]}"; set -e; stop_watchdog
  ((rc==0)) || { log_error "Docker build failed; full log: $LOG_DIR/docker-build.log"; exit "$rc"; }
}

export_rootfs(){
  header 'STEP 2: EXPORT DOCKER ROOTFS'
  mkdir -p "$ROOTFS_DIR"
  rm -rf "$ROOTFS_DIR"/*
  local cname="chimera-export-$BASHPID"
  docker rm -f "$cname" >/dev/null 2>&1 || true
  docker create --name "$cname" "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null
  start_watchdog "Docker rootfs export / tar extraction"; set +e
  if command -v pv >/dev/null 2>&1; then
    docker export "$cname" | pv -brt 2> >(tee -a "$LOG_DIR/docker-export.progress" >&2) | tar -xpf - -C "$ROOTFS_DIR" --checkpoint=10000 --checkpoint-action="echo=[ROOTFS] extracted %T"
  else
    docker export "$cname" | tar -xpf - -C "$ROOTFS_DIR" --checkpoint=10000 --checkpoint-action="echo=[ROOTFS] extracted %T"
  fi
  local s=("${PIPESTATUS[@]}"); set -e; stop_watchdog
  docker rm -f "$cname" >/dev/null 2>&1 || true
  (( ${s[0]:-1}==0 && ${s[1]:-1}==0 )) || { log_error 'Docker rootfs export failed'; exit 1; }
  [[ -d "$ROOTFS_DIR/bin" || -d "$ROOTFS_DIR/usr/bin" ]] || { log_error 'Rootfs export is incomplete'; exit 1; }
}

create_boot_menu(){
  header 'STEP 3: BUILD BOOT ARTIFACTS'
  "$SCRIPT_DIR/kernel/build-koronos.sh"
  local k="$SCRIPT_DIR/build/koronos/x86_64/koronos.elf"; [[ -s "$k" ]] || { log_error 'Koronos ELF missing'; exit 1; }
  mkdir -p "$ISO_DIR/boot/koronos" "$ISO_DIR/boot/jasper" "$ISO_DIR/boot/spitfire" "$ISO_DIR/boot/grub" "$ISO_DIR/EFI/BOOT"
  cp "$k" "$ISO_DIR/boot/kernel.bin"; cp "$k" "$ISO_DIR/boot/koronos/koronos.elf"
  bash "$SCRIPT_DIR/tools/build-boot-artifacts.sh"
  local b="$BUILD_DIR/boot-artifacts"; [[ -s "$b/jasper/jasper.elf" ]] || { log_error 'Jasper ELF missing'; exit 1; }
  cp "$b/jasper/jasper.elf" "$ISO_DIR/boot/jasper/"
  for f in spitfire-sf0-mbr.bin spitfire-stage2.bin spitfire-sf1-longmode.o spitfire-sf2-loader.o; do [[ -s "$b/spitfire/$f" ]] || { log_error "Missing Spit Fire artifact: $f"; exit 1; }; cp "$b/spitfire/$f" "$ISO_DIR/boot/spitfire/"; done
  bash "$SCRIPT_DIR/tools/build-live-boot-binaries.sh"
  cp "$BUILD_DIR/live-boot/boot/live/chimera-live-initramfs.img" "$ISO_DIR/boot/live/"
  cp "$BUILD_DIR/live-boot/boot/live/live-manifest.json" "$ISO_DIR/boot/live/"
  mkdir -p "$ISO_DIR/boot/recovery" "$ISO_DIR/recovery"
  cp "$BUILD_DIR/live-boot/boot/recovery/chimera-recovery-initramfs.img" "$ISO_DIR/boot/recovery/"
  cp "$BUILD_DIR/live-boot/boot/recovery/chimera-recovery-initramfs.img.sha256" "$ISO_DIR/boot/recovery/"
  cp "$BUILD_DIR/live-boot/boot/recovery/recovery-manifest.json" "$ISO_DIR/boot/recovery/"
  cp "$SCRIPT_DIR/config/recovery/chimera-recovery-targets.json" "$ISO_DIR/recovery/"
  cp "$SCRIPT_DIR/docs/recovery-runtime-levels.md" "$ISO_DIR/recovery/"
  [[ -s "$BUILD_DIR/live-boot/boot/vmlinuz" ]] && cp "$BUILD_DIR/live-boot/boot/vmlinuz" "$ISO_DIR/boot/live/" || true
  [[ -f "$SCRIPT_DIR/boot/iso/grub.cfg" ]] && cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$ISO_DIR/boot/grub/grub.cfg" || cat > "$ISO_DIR/boot/grub/grub.cfg" <<'EOF'
set timeout=5
menuentry 'Chimera II OS Live' { multiboot2 /boot/kernel.bin; boot }
EOF
}

add_branding(){
  # Runtime driver/logging staging is installed by stage_features.
  mkdir -p "$ROOTFS_DIR/etc" "$ROOTFS_DIR/var/log/chimera" "$ROOTFS_DIR/usr/share/chimera/aurora" "$ROOTFS_DIR/usr/share/applications" "$ROOTFS_DIR/etc/systemd/system"
  if [[ -f "$SCRIPT_DIR/tools/chimera-process-monitor.sh" ]]; then cp -f "$SCRIPT_DIR/tools/chimera-process-monitor.sh" "$ROOTFS_DIR/usr/bin/chimera-process-monitor"; chmod +x "$ROOTFS_DIR/usr/bin/chimera-process-monitor"; fi
  if [[ -f "$SCRIPT_DIR/tools/chimera-boot-log-window.sh" ]]; then cp -f "$SCRIPT_DIR/tools/chimera-boot-log-window.sh" "$ROOTFS_DIR/usr/bin/chimera-boot-log-window"; chmod +x "$ROOTFS_DIR/usr/bin/chimera-boot-log-window"; fi
  [[ -f "$SCRIPT_DIR/system/aurora/chimera-log-window.json" ]] && cp -f "$SCRIPT_DIR/system/aurora/chimera-log-window.json" "$ROOTFS_DIR/usr/share/chimera/aurora/" || true
  cat > "$ROOTFS_DIR/etc/os-release" <<'EOF'
NAME="Chimera II OS"
VERSION="1.0.0"
ID=chimera
PRETTY_NAME="Chimera II OS 1.0.0 (Comprehensive Edition)"
EOF
}

prepare_apache(){
  [[ "${APACHE_ECOSYSTEM:-1}" == 0 ]] && return 0
  local src="$SCRIPT_DIR/services/apache" dst="$ROOTFS_DIR/opt/chimera/apache"
  [[ -d "$src" ]] || return 0
  mkdir -p "$dst"
  for f in apache-projects.json README.md apache-sync.py; do [[ -f "$src/$f" ]] && cp -f "$src/$f" "$dst/"; done
}

stage_features(){
  [[ -x "$SCRIPT_DIR/tools/stage-chimera-runtime.sh" ]] && bash "$SCRIPT_DIR/tools/stage-chimera-runtime.sh" "$ROOTFS_DIR" "$SCRIPT_DIR"
  if [[ "${CHIMERA_BUILD_EMULATORS:-0}" == 1 && -x "$SCRIPT_DIR/tools/build-emulator-stack.sh" ]]; then
    bash "$SCRIPT_DIR/tools/build-emulator-stack.sh" >> "$LOG_DIR/emulator-build.log" 2>&1 || printf "[WARN] Emulator build staging failed; continuing ISO build.\n" | tee -a "$LOG_DIR/chimera-build.log"
  fi
  if [[ -d "$BUILD_DIR/emulators/payloads" ]]; then
    mkdir -p "$ROOTFS_DIR/usr/lib/chimera/emulators/payloads"
    cp -a "$BUILD_DIR/emulators/payloads/." "$ROOTFS_DIR/usr/lib/chimera/emulators/payloads/"
  fi
  mkdir -p "$ISO_DIR/system" "$ISO_DIR/desktop" "$ISO_DIR/network" "$ISO_DIR/drivers" "$ISO_DIR/install"
  for d in services userland desktop network installer system/security; do [[ -d "$SCRIPT_DIR/$d" ]] && cp -a "$SCRIPT_DIR/$d" "$ISO_DIR/system/" 2>/dev/null || true; done
  [[ -f "$SCRIPT_DIR/appcenter/catalog/game-registry.json" ]] && true
  mkdir -p "$ROOTFS_DIR/etc/chimera" "$ROOTFS_DIR/usr/share/chimera"
  [[ -f "$SCRIPT_DIR/system/storage/chimera-storage.conf" ]] && cp -f "$SCRIPT_DIR/system/storage/chimera-storage.conf" "$ROOTFS_DIR/etc/chimera/"
  [[ -f "$SCRIPT_DIR/system/hardware/chimera-hardware-profile.json" ]] && cp -f "$SCRIPT_DIR/system/hardware/chimera-hardware-profile.json" "$ROOTFS_DIR/usr/share/chimera/"

  # Docker/rootfs images may contain a regular file or stale symlink at the
  # Aurora config mount point.  cp requires the destination to be a directory,
  # so normalize that path before staging multiple configuration files.
  local aurora_dir="$ROOTFS_DIR/usr/share/chimera/aurora"
  local aurora_config_dir="$aurora_dir/config"
  mkdir -p "$aurora_dir"
  if [[ -e "$aurora_config_dir" && ! -d "$aurora_config_dir" ]] || [[ -L "$aurora_config_dir" ]]; then
    log_warning "Replacing non-directory Aurora config path: $aurora_config_dir"
    rm -rf -- "$aurora_config_dir"
  fi
  mkdir -p "$aurora_config_dir" "$ROOTFS_DIR/usr/share/chimera/docs"
  for f in config/aurora/desktop-parity.json config/aurora/emulators.json config/aurora/free-roms.json config/aurora/emulator-windows.json config/aurora/emulator-associations.json config/chimera/kernel-desktop-parity.json config/chimera/platform-feature-policy.json; do
    if [[ -f "$SCRIPT_DIR/$f" ]]; then
      cp -f "$SCRIPT_DIR/$f" "$aurora_config_dir/"
    fi
  done
  [[ -f "$SCRIPT_DIR/docs/kernel-desktop-implementation.md" ]] && cp -f "$SCRIPT_DIR/docs/kernel-desktop-implementation.md" "$ROOTFS_DIR/usr/share/chimera/docs/"
  [[ -f "$SCRIPT_DIR/system/boot/chimera-log.conf" ]] && cp -f "$SCRIPT_DIR/system/boot/chimera-log.conf" "$ROOTFS_DIR/etc/chimera/" || true
  [[ -f "$SCRIPT_DIR/system/aurora/chimera-log-window.desktop" ]] && cp -f "$SCRIPT_DIR/system/aurora/chimera-log-window.desktop" "$ROOTFS_DIR/usr/share/applications/" 2>/dev/null || true
  [[ -f "$SCRIPT_DIR/system/aurora/chimera-log-window.service" ]] && cp -f "$SCRIPT_DIR/system/aurora/chimera-log-window.service" "$ROOTFS_DIR/etc/systemd/system/" 2>/dev/null || true
}

stage_games(){
  local d="$ISO_DIR/games"; mkdir -p "$d"
  [[ -f "$SCRIPT_DIR/appcenter/catalog/game-registry.json" ]] && cp -f "$SCRIPT_DIR/appcenter/catalog/game-registry.json" "$d/"
  [[ -f "$SCRIPT_DIR/appcenter/catalog/game-capability-policy.json" ]] && cp -f "$SCRIPT_DIR/appcenter/catalog/game-capability-policy.json" "$d/"
  [[ -d "$SCRIPT_DIR/games" ]] && cp -a "$SCRIPT_DIR/games/." "$d/" 2>/dev/null || true
}

create_installer(){
  local p; mkdir -p "$ISO_DIR/install/installer"; p="$(mktemp -d "$ISO_TMP_DIR/installer.XXXXXX")"
  mkdir -p "$p"/{bin,dev,proc,sys,run,tmp,mnt,target,etc,chimera/installer,lib,lib/firmware,lib/chimera/drivers} "$p/run/chimera" "$p/var/log/mesgs/archive"
  ln -sfn /var/log/mesgs "$p/var/log/chimera"
  ln -sfn mesgs "$p/var/log/messages"
  local bb="$(command -v busybox || true)"; [[ -n "$bb" ]] && { cp "$bb" "$p/bin/busybox"; for x in sh mount umount switch_root mkdir cat echo ls cp mv sleep sync ps top tail date clear sed awk head wget ip udhcpc nslookup gzip; do ln -sf busybox "$p/bin/$x"; done; }
  [[ -f "$SCRIPT_DIR/tools/chimera-installer-runtime.sh" ]] && cp -f "$SCRIPT_DIR/tools/chimera-installer-runtime.sh" "$p/bin/chimera-installer-runtime.sh" && chmod +x "$p/bin/chimera-installer-runtime.sh"
  for f in tools/chimera-driver-manager.sh tools/chimera-logrotate.sh; do [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$p/bin/"; done
  [[ -f "$SCRIPT_DIR/config/drivers/driver-repositories.json" ]] && mkdir -p "$p/etc/chimera/drivers" && cp -f "$SCRIPT_DIR/config/drivers/driver-repositories.json" "$p/etc/chimera/drivers/"
  [[ -f "$SCRIPT_DIR/config/drivers/driver-policy.json" ]] && mkdir -p "$p/etc/chimera/drivers" && cp -f "$SCRIPT_DIR/config/drivers/driver-policy.json" "$p/etc/chimera/drivers/"
  for f in "$SCRIPT_DIR/install/installer-contract.json" "$SCRIPT_DIR/installer/installation_phases.json" "$SCRIPT_DIR/installer/installer_profiles.json" "$SCRIPT_DIR/installer/profiles/chimera-installer-features.json" "$SCRIPT_DIR/installer/profiles/filesystem-support.json"; do [[ -f "$f" ]] && cp -f "$f" "$p/chimera/installer/"; done
  cat > "$p/bin/chimera-installer-monitor" <<'EOF'
#!/bin/sh
while :; do
  printf '[INSTALLER] target=%s rootfs=%s\n' "${1:-unknown}" "${2:-/target}" >> /var/log/mesgs
  sleep 5
done
EOF
  chmod +x "$p/bin/chimera-installer-monitor"
  (cd "$p" && find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -9) > "$ISO_DIR/install/installer/chimera-installer-initramfs.img"
  rm -rf "$p"
}

create_squashfs(){
  header 'STEP: BUILD SQUASHFS'
  mkdir -p "$ISO_DIR/live"
  local tmp="$ISO_TMP_DIR/filesystem.squashfs.tmp"
  rm -f "$tmp"
  mksquashfs "$ROOTFS_DIR" "$tmp" -noappend -comp zstd -wildcards
  mv -f "$tmp" "$ISO_DIR/live/filesystem.squashfs"
}

verify_iso(){
  [[ -s "$ISO_DIR/live/filesystem.squashfs" ]] || { log_error 'filesystem.squashfs missing'; exit 1; }
  [[ -s "$ISO_DIR/boot/live/chimera-live-initramfs.img" ]] || { log_error 'live initramfs missing'; exit 1; }
  [[ -f "$ISO_DIR/boot/live/live-manifest.json" ]] || { log_error 'live manifest missing'; exit 1; }
  [[ -s "$ISO_DIR/boot/jasper/jasper.elf" ]] || { log_error 'Jasper ELF missing from ISO'; exit 1; }
  [[ -s "$ISO_DIR/boot/koronos/koronos.elf" ]] || { log_error 'Koronos ELF missing from ISO'; exit 1; }
}

build_iso(){
  header 'BUILD ISO IMAGE'
  local out="$ISO_OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}.iso"
  xorriso -as mkisofs -R -J -V "CHIMERA2" -o "$out" "$ISO_DIR"
  [[ -s "$out" ]] || { log_error 'ISO was not created'; exit 1; }
  sha256sum "$out" > "$out.sha256"
  log_success "ISO: $out"
}

report(){
  header 'CHIMERA BUILD REPORT'
  log_success "Build directory: $BUILD_DIR"
  log_success "Rootfs: $ROOTFS_DIR"
  log_success "ISO output: $ISO_OUTPUT_DIR"
}

main(){
  [[ "$CLEAN_STATE" == 1 ]] && state_reset
  check_deps
  preflight
  local completed="$(state_get)"
  if [[ "$RESUME_BUILD" == 1 && -n "$completed" ]]; then log_info "Resuming after stage: $completed"; fi
  run_stage_if_needed(){ local name="$1" fn="$2"; if [[ "$RESUME_BUILD" == 1 ]] && state_done "$completed" "$name"; then log_info "Skipping completed stage: $name"; else run_stage "$name" "$fn"; fi; }
  run_stage_if_needed docker build_docker
  run_stage_if_needed rootfs export_rootfs
  run_stage_if_needed boot create_boot_menu
  run_stage_if_needed branding add_branding
  run_stage_if_needed apache prepare_apache
  run_stage_if_needed features stage_features
  run_stage_if_needed games stage_games
  run_stage_if_needed squashfs create_squashfs
  run_stage_if_needed iso build_iso
  run_stage_if_needed verify verify_iso
  run_stage_if_needed report report
  rm -f "$FAILED_FILE"
  BUILD_SUCCEEDED=1
  log_success 'Chimera II OS comprehensive build completed.'
}

on_exit(){
  local rc=$?
  stop_watchdog || true
  if ((rc!=0 && BUILD_SUCCEEDED==0)); then
    printf '%s\n' "$CURRENT_STAGE" > "$FAILED_FILE" 2>/dev/null || true
    log_error "Build stopped during stage: ${CURRENT_STAGE:-unknown}"
    log_error "Checkpoint retained: $STATE_FILE"
  fi
  exit "$rc"
}
trap on_exit EXIT

main "$@"
