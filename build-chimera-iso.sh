#!/usr/bin/env bash
set -Eeuo pipefail

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
WATCHDOG_PID=""
STATE_FILE="${CHIMERA_BUILD_STATE_FILE:-$BUILD_DIR/.chimera-build-state}"
FAILED_FILE="${CHIMERA_FAILED_STAGE_FILE:-$BUILD_DIR/.chimera-failed-stage}"
RESUME_BUILD=0
CLEAN_STATE=0
STORAGE_AUTO="${CHIMERA_STORAGE_AUTO:-0}"
STORAGE_PROMPT="${CHIMERA_STORAGE_PROMPT:-1}"
CURRENT_STAGE=""
BUILD_SUCCEEDED=0

mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_DIR/boot/live" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"
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
    pstree -ap $$ 2>/dev/null | head -n 80 || true
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
  LOG_DIR="$BUILD_DIR/logs"; mkdir -p "$LOG_DIR"; stop_watchdog || true
  local label="$1" interval="${CHIMERA_BUILD_WATCHDOG_INTERVAL:-5}"
  (while :; do log_both "[WATCHDOG] $label still active"; process_snapshot; sleep "$interval"; done) &
  WATCHDOG_PID=$!
}
stop_watchdog(){
  if [[ -n "$WATCHDOG_PID" ]]; then kill "$WATCHDOG_PID" 2>/dev/null || true; wait "$WATCHDOG_PID" 2>/dev/null || true; WATCHDOG_PID=""; fi
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
  mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_DIR/boot/live" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"
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
  mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_DIR/boot/live" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"
  export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" TMPDIR="$ISO_TMP_DIR"
  log_success "Build storage switched to $best"
}
preflight(){
  header 'LARGE ISO / STORAGE PREFLIGHT'
  local rg="$(free_gib "$ROOTFS_DIR")" og="$(free_gib "$ISO_OUTPUT_DIR")"
  log_info "Rootfs filesystem free: ${rg} GiB"; log_info "ISO output filesystem free: ${og} GiB"
  if ((rg<20 || og<20)); then
    if [[ "$STORAGE_AUTO" == 1 ]]; then choose_storage 20 || { log_error 'No suitable larger storage found'; exit 1; }
    elif [[ "$STORAGE_PROMPT" == 1 && -t 0 ]]; then
      read -r -p 'Storage path for large Chimera build: ' p
      [[ -d "$p" ]] || { log_error 'No storage selected'; exit 1; }
      export CHIMERA_BUILD_STORAGE_ROOT="$p"; root="${p%/}"; BUILD_DIR="$root/chimera-build"; ISO_DIR="$BUILD_DIR/iso"; ROOTFS_DIR="$BUILD_DIR/rootfs"; ISO_OUTPUT_DIR="$root/chimera-output"; ISO_TMP_DIR="$BUILD_DIR/logs/chimera-iso-build"; STATE_FILE="$BUILD_DIR/.chimera-build-state"; FAILED_FILE="$BUILD_DIR/.chimera-failed-stage"; mkdir -p "$BUILD_DIR" "$ISO_DIR/live" "$ISO_DIR/boot" "$ISO_DIR/boot/live" "$ISO_OUTPUT_DIR" "$ISO_TMP_DIR"; export CHIMERA_BUILD_DIR="$BUILD_DIR" CHIMERA_ROOTFS_DIR="$ROOTFS_DIR" CHIMERA_ISO_OUTPUT_DIR="$ISO_OUTPUT_DIR" TMPDIR="$ISO_TMP_DIR"
    else log_error 'Insufficient storage; use --storage /mnt/d or --storage-auto'; exit 1; fi
  fi
  command -v mksquashfs >/dev/null || { log_error 'mksquashfs is required'; exit 2; }
}
state_get(){ [[ -f "$STATE_FILE" ]] && sed -n 's/^completed=//p' "$STATE_FILE" | tail -1 || true; }
state_mark(){ printf 'schema=2\ncompleted=%s\nupdated=%s\n' "$1" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$STATE_FILE"; }
state_reset(){ rm -f "$STATE_FILE" "$FAILED_FILE"; }
state_done(){
  local c="$1" t="$2"; [[ -n "$c" ]] || return 1
  local order='docker rootfs boot branding apache features games squashfs iso verify report'; local ci ti
  ci=$(printf '%s\n' "$order" | awk -v x="$c" '{for(i=1;i<=NF;i++)if($i==x)print i}'); ti=$(printf '%s\n' "$order" | awk -v x="$t" '{for(i=1;i<=NF;i++)if($i==x)print i}')
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
  local rc="${PIPESTATUS[0]}"; set -e; stop_watchdog; ((rc==0)) || { log_error "Docker build failed; full log: $LOG_DIR/docker-build.log"; exit "$rc"; }
}

export_rootfs(){
  header 'STEP 2: EXPORT DOCKER ROOTFS'; mkdir -p "$ROOTFS_DIR"; rm -rf "$ROOTFS_DIR"/*
  local cname="chimera-export-$BASHPID"; docker rm -f "$cname" >/dev/null 2>&1 || true; docker create --name "$cname" "$DOCKER_IMAGE:$DOCKER_TAG" >/dev/null
  start_watchdog "Docker rootfs export / tar extraction"; set +e
  if command -v pv >/dev/null 2>&1; then docker export "$cname" | pv -brt 2> >(tee -a "$LOG_DIR/docker-export.progress" >&2) | tar -xpf - -C "$ROOTFS_DIR" --checkpoint=10000 --checkpoint-action="echo=[ROOTFS] extracted %T"; else docker export "$cname" | tar -xpf - -C "$ROOTFS_DIR" --checkpoint=10000 --checkpoint-action="echo=[ROOTFS] extracted %T"; fi
  local s=("${PIPESTATUS[@]}"); set -e; stop_watchdog; docker rm -f "$cname" >/dev/null 2>&1 || true
  (( ${s[0]:-1}==0 && ${s[1]:-1}==0 )) || { log_error 'Docker rootfs export failed'; exit 1; }
  [[ -d "$ROOTFS_DIR/bin" || -d "$ROOTFS_DIR/usr/bin" ]] || { log_error 'Rootfs export is incomplete'; exit 1; }
}

create_boot_menu(){
  header 'STEP 3: BUILD BOOT ARTIFACTS'
  "$SCRIPT_DIR/kernel/build-koronos.sh"
  local k="$SCRIPT_DIR/build/koronos/x86_64/koronos.elf"; [[ -s "$k" ]] || { log_error 'Koronos ELF missing'; exit 1; }
  mkdir -p "$ISO_DIR/boot/koronos" "$ISO_DIR/boot/jasper" "$ISO_DIR/boot/spitfire" "$ISO_DIR/boot/grub" "$ISO_DIR/boot/live" "$ISO_DIR/EFI/BOOT"
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
  [[ -f "$SCRIPT_DIR/boot/iso/grub.cfg" ]] && cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$ISO_DIR/boot/grub/grub.cfg"
  [[ -f "$SCRIPT_DIR/boot/jasper/recovery.cfg" ]] && cp "$SCRIPT_DIR/boot/jasper/recovery.cfg" "$ISO_DIR/boot/jasper/recovery.cfg"
  [[ -f "$SCRIPT_DIR/boot/jasper/live.cfg" ]] && cp "$SCRIPT_DIR/boot/jasper/live.cfg" "$ISO_DIR/boot/jasper/live.cfg"
  [[ -f "$SCRIPT_DIR/boot/jasper/jasper.cfg" ]] && cp "$SCRIPT_DIR/boot/jasper/jasper.cfg" "$ISO_DIR/boot/jasper/jasper.cfg"
  [[ -f "$SCRIPT_DIR/boot/jasper/safe-mode.cfg" ]] && cp "$SCRIPT_DIR/boot/jasper/safe-mode.cfg" "$ISO_DIR/boot/jasper/safe-mode.cfg"
  [[ -f "$SCRIPT_DIR/boot/jasper/diagnostics.cfg" ]] && cp "$SCRIPT_DIR/boot/jasper/diagnostics.cfg" "$ISO_DIR/boot/jasper/diagnostics.cfg"
  [[ -f "$SCRIPT_DIR/boot/spitfire/spitfire-menu.cfg" ]] && cp "$SCRIPT_DIR/boot/spitfire/spitfire-menu.cfg" "$ISO_DIR/boot/spitfire/spitfire-menu.cfg"
  [[ -f "$SCRIPT_DIR/boot/iso/grub.cfg" ]] || { log_error 'GRUB configuration missing'; exit 1; }
  [[ -s "$ISO_DIR/boot/grub/grub.cfg" ]] || { log_error 'Staged GRUB configuration is empty'; exit 1; }
  [[ -s "$ISO_DIR/boot/recovery/chimera-recovery-initramfs.img" ]] || { log_error 'Recovery initramfs missing'; exit 1; }
  [[ -s "$ISO_DIR/boot/live/chimera-live-initramfs.img" ]] || { log_error 'Live initramfs missing'; exit 1; }
}

prepare_branding(){
  header 'STEP 4: BRANDING / AURORA'
  mkdir -p "$ROOTFS_DIR/usr/share/chimera/aurora" "$ISO_DIR/boot/visual"
  local bg="${CHIMERA_AURORA_ASSET:-}"
  if [[ -n "$bg" && -f "$bg" ]]; then
    cp -f "$bg" "$ISO_DIR/boot/visual/aurora-background.jpg"
  elif [[ -f "$SCRIPT_DIR/boot/jasper/background.jpg" ]]; then
    cp -f "$SCRIPT_DIR/boot/jasper/background.jpg" "$ISO_DIR/boot/visual/aurora-background.jpg"
  elif [[ -f "$SCRIPT_DIR/boot/jasper/background.png" ]]; then
    cp -f "$SCRIPT_DIR/boot/jasper/background.png" "$ISO_DIR/boot/visual/aurora-background.png"
  fi
}

prepare_apache(){ [[ "${APACHE_ECOSYSTEM:-1}" == 0 ]] && return 0; local src="$SCRIPT_DIR/services/apache" dst="$ROOTFS_DIR/opt/chimera/apache"; [[ -d "$src" ]] || return 0; mkdir -p "$dst"; for f in apache-projects.json README.md apache-sync.py; do [[ -f "$src/$f" ]] && cp -f "$src/$f" "$dst/"; done; }
stage_features(){
  [[ -x "$SCRIPT_DIR/tools/stage-chimera-runtime.sh" ]] && bash "$SCRIPT_DIR/tools/stage-chimera-runtime.sh" "$ROOTFS_DIR" "$SCRIPT_DIR"
  if [[ "${CHIMERA_BUILD_EMULATORS:-0}" == 1 && -x "$SCRIPT_DIR/tools/build-emulator-stack.sh" ]]; then bash "$SCRIPT_DIR/tools/build-emulator-stack.sh" >> "$LOG_DIR/emulator-build.log" 2>&1 || printf "[WARN] Emulator build staging failed; continuing ISO build.\n" | tee -a "$LOG_DIR/chimera-build.log"; fi
  if [[ -d "$BUILD_DIR/emulators/payloads" ]]; then mkdir -p "$ROOTFS_DIR/usr/lib/chimera/emulators/payloads"; cp -a "$BUILD_DIR/emulators/payloads/." "$ROOTFS_DIR/usr/lib/chimera/emulators/payloads/"; fi
  mkdir -p "$ISO_DIR/system" "$ISO_DIR/desktop" "$ISO_DIR/network" "$ISO_DIR/drivers" "$ISO_DIR/install"
  for d in services userland desktop network installer system/security; do [[ -d "$SCRIPT_DIR/$d" ]] && cp -a "$SCRIPT_DIR/$d" "$ISO_DIR/system/" 2>/dev/null || true; done
  mkdir -p "$ROOTFS_DIR/etc/chimera" "$ROOTFS_DIR/usr/share/chimera"
  [[ -f "$SCRIPT_DIR/system/storage/chimera-storage.conf" ]] && cp -f "$SCRIPT_DIR/system/storage/chimera-storage.conf" "$ROOTFS_DIR/etc/chimera/"
  [[ -f "$SCRIPT_DIR/system/hardware/chimera-hardware-profile.json" ]] && cp -f "$SCRIPT_DIR/system/hardware/chimera-hardware-profile.json" "$ROOTFS_DIR/usr/share/chimera/"
  local aurora_dir aurora_config_dir
  aurora_dir="$ROOTFS_DIR/usr/share/chimera/aurora"
  aurora_config_dir="$aurora_dir/config"
  mkdir -p "$aurora_dir"
  if [[ -e "$aurora_config_dir" && ! -d "$aurora_config_dir" ]] || [[ -L "$aurora_config_dir" ]]; then rm -rf -- "$aurora_config_dir"; fi
  mkdir -p "$aurora_config_dir" "$ROOTFS_DIR/usr/share/chimera/docs"
  for f in config/aurora/desktop-parity.json config/aurora/emulators.json config/aurora/free-roms.json config/aurora/emulator-windows.json config/aurora/emulator-associations.json config/chimera/kernel-desktop-parity.json config/chimera/platform-feature-policy.json; do [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$aurora_config_dir/"; done
  [[ -f "$SCRIPT_DIR/docs/kernel-desktop-implementation.md" ]] && cp -f "$SCRIPT_DIR/docs/kernel-desktop-implementation.md" "$ROOTFS_DIR/usr/share/chimera/docs/"
  [[ -f "$SCRIPT_DIR/system/boot/chimera-log.conf" ]] && cp -f "$SCRIPT_DIR/system/boot/chimera-log.conf" "$ROOTFS_DIR/etc/chimera/" || true
  [[ -f "$SCRIPT_DIR/system/aurora/chimera-log-window.desktop" ]] && cp -f "$SCRIPT_DIR/system/aurora/chimera-log-window.desktop" "$ROOTFS_DIR/usr/share/applications/" 2>/dev/null || true
  [[ -f "$SCRIPT_DIR/system/aurora/chimera-log-window.service" ]] && cp -f "$SCRIPT_DIR/system/aurora/chimera-log-window.service" "$ROOTFS_DIR/etc/systemd/system/" 2>/dev/null || true
}

stage_games(){ local d="$ISO_DIR/games"; mkdir -p "$d"; [[ -f "$SCRIPT_DIR/appcenter/catalog/game-registry.json" ]] && cp -f "$SCRIPT_DIR/appcenter/catalog/game-registry.json" "$d/"; [[ -f "$SCRIPT_DIR/appcenter/catalog/game-capability-policy.json" ]] && cp -f "$SCRIPT_DIR/appcenter/catalog/game-capability-policy.json" "$d/"; [[ -d "$SCRIPT_DIR/games" ]] && cp -a "$SCRIPT_DIR/games/." "$d/" 2>/dev/null || true; }

create_installer(){
  local p; mkdir -p "$ISO_DIR/install/installer"; p="$(mktemp -d "$ISO_TMP_DIR/installer.XXXXXX")"
  mkdir -p "$p"/{bin,dev,proc,sys,run,tmp,mnt,target,etc,chimera/installer,lib,lib/firmware,lib/chimera/drivers} "$p/run/chimera" "$p/var/log/mesgs/archive"
  ln -sfn /var/log/mesgs "$p/var/log/chimera"; ln -sfn mesgs "$p/var/log/messages"
  local bb="$(command -v busybox || true)"; [[ -n "$bb" ]] && { cp "$bb" "$p/bin/busybox"; for x in sh mount umount switch_root mkdir cat echo ls cp mv sleep sync ps top tail date clear sed awk head wget ip udhcpc nslookup gzip; do ln -sf busybox "$p/bin/$x"; done; }
  [[ -f "$SCRIPT_DIR/tools/chimera-installer-runtime.sh" ]] && cp -f "$SCRIPT_DIR/tools/chimera-installer-runtime.sh" "$p/bin/chimera-installer-runtime.sh" && chmod +x "$p/bin/chimera-installer-runtime.sh"
  for f in tools/chimera-driver-manager.sh tools/chimera-logrotate.sh; do [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$p/bin/"; done
  [[ -f "$SCRIPT_DIR/config/drivers/driver-repositories.json" ]] && mkdir -p "$p/etc/chimera/drivers" && cp -f "$SCRIPT_DIR/config/drivers/driver-repositories.json" "$p/etc/chimera/drivers/"
  [[ -f "$SCRIPT_DIR/config/drivers/driver-policy.json" ]] && mkdir -p "$p/etc/chimera/drivers" && cp -f "$SCRIPT_DIR/config/drivers/driver-policy.json" "$p/etc/chimera/drivers/"
  for f in "$SCRIPT_DIR/install/installer-contract.json" "$SCRIPT_DIR/installer/installation_phases.json" "$SCRIPT_DIR/installer/installer_profiles.json" "$SCRIPT_DIR/installer/profiles/chimera-installer-features.json" "$SCRIPT_DIR/installer/profiles/filesystem-support.json"; do [[ -f "$f" ]] && cp -f "$f" "$p/chimera/installer/"; done
  cat > "$p/bin/chimera-installer-monitor" <<'EOF'
#!/bin/sh
while :; do date; sleep 5; done
EOF
  chmod +x "$p/bin/chimera-installer-monitor"
  if [[ -x "$SCRIPT_DIR/tools/build-installation-media.sh" ]]; then bash "$SCRIPT_DIR/tools/build-installation-media.sh" "$p"; fi
  if [[ -f "$p/installation.img" ]]; then cp -f "$p/installation.img" "$ISO_DIR/install/installer/installation.img"; else dd if=/dev/zero of="$ISO_DIR/install/installer/installation.img" bs=1M count=8 status=none; fi
  [[ -f "$SCRIPT_DIR/install/installation-manifest.json" ]] && cp -f "$SCRIPT_DIR/install/installation-manifest.json" "$ISO_DIR/install/installer/"
  [[ -f "$SCRIPT_DIR/install/installer-contract.json" ]] && cp -f "$SCRIPT_DIR/install/installer-contract.json" "$ISO_DIR/install/installer/"
  [[ -f "$SCRIPT_DIR/installer/installation_phases.json" ]] && cp -f "$SCRIPT_DIR/installer/installation_phases.json" "$ISO_DIR/install/installer/"
  [[ -f "$SCRIPT_DIR/installer/installer_profiles.json" ]] && cp -f "$SCRIPT_DIR/installer/installer_profiles.json" "$ISO_DIR/install/installer/"
  rm -rf "$p"
}

build_squashfs(){
  header 'STEP 8: BUILD ROOTFS SQUASHFS'
  mkdir -p "$ISO_DIR/live"
  local tmp="$ISO_TMP_DIR/filesystem.squashfs.tmp" out="$ISO_DIR/live/filesystem.squashfs"
  rm -f "$tmp"
  start_watchdog "mksquashfs root filesystem"
  set +e
  mksquashfs "$ROOTFS_DIR" "$tmp" -comp zstd -noappend -progress 2>&1 | tee "$LOG_DIR/mksquashfs.log"
  local rc="${PIPESTATUS[0]}"
  set -e
  stop_watchdog
  ((rc==0)) || { log_error 'mksquashfs failed'; exit "$rc"; }
  [[ -s "$tmp" ]] || { log_error 'SquashFS output is empty'; exit 1; }
  mv -f "$tmp" "$out"
}

build_iso(){
  header 'STEP 9: BUILD BOOTABLE ISO'

  local iso="$ISO_OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}.iso"
  local source_bytes=0
  local free_bytes_now=0
  local required_bytes=0
  local safety_bytes=$((2 * 1024 * 1024 * 1024))

  rm -f "$iso" "$iso.sha256"

  rm -rf "$ISO_DIR/EFI/BOOT"
  mkdir -p "$ISO_DIR/EFI/BOOT"

  source_bytes="$(du -sB1 "$ISO_DIR" 2>/dev/null | awk '{print $1}')"
  free_bytes_now="$(free_bytes "$ISO_OUTPUT_DIR")"

  # Allow room for ISO metadata, GRUB structures, temporary xorriso
  # allocation and filesystem overhead.
  required_bytes=$((source_bytes + safety_bytes))

  log_info "ISO staging size: $((source_bytes / 1024 / 1024 / 1024)) GiB"
  log_info "Current output free space: $((free_bytes_now / 1024 / 1024 / 1024)) GiB"
  log_info "Required output space: $((required_bytes / 1024 / 1024 / 1024)) GiB"

  if (( free_bytes_now < required_bytes )); then
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
  local iso="$ISO_OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}.iso"
  [[ -s "$iso" ]] || { log_error 'ISO missing'; exit 1; }
  xorriso -indev "$iso" -report_el_torito plain | tee "$LOG_DIR/iso-el-torito.log"
  grep -qi 'El Torito' "$LOG_DIR/iso-el-torito.log" || { log_error 'ISO has no El Torito boot catalog'; exit 1; }
  xorriso -indev "$iso" -find /boot/grub/grub.cfg -print | tee "$LOG_DIR/iso-grub-files.log"
  xorriso -indev "$iso" -find /boot/koronos/koronos.elf -print | tee -a "$LOG_DIR/iso-grub-files.log"
  xorriso -indev "$iso" -find /boot/recovery/chimera-recovery-initramfs.img -print | tee -a "$LOG_DIR/iso-grub-files.log"
  if ! xorriso -indev "$iso" -find /EFI/BOOT/BOOTX64.EFI -print | tee "$LOG_DIR/iso-uefi-files.log"; then
    log_warning 'UEFI BOOTX64.EFI lookup failed; inspect ISO El Torito report before deployment.'
  fi
  if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    log_info 'QEMU BIOS boot probe available; launching headless firmware probe.'
    timeout "${CHIMERA_QEMU_BOOT_TIMEOUT:-20}" qemu-system-x86_64 -accel tcg -m 512 -cdrom "$iso" -display none -serial none -monitor none -no-reboot -no-shutdown >/dev/null 2>&1 || true
  fi
}

report_build(){
  header 'CHIMERA BUILD REPORT'
  log_success "Build directory: $BUILD_DIR"
  log_success "Rootfs: $ROOTFS_DIR"
  log_success "ISO output: $ISO_OUTPUT_DIR"
  log_success "Chimera II OS comprehensive build completed."
}

main(){
  [[ "$CLEAN_STATE" == 1 ]] && state_reset
  preflight
  check_deps
  local completed="$(state_get)"
  for stage in docker rootfs boot branding apache features games squashfs iso verify report; do
    if [[ "$RESUME_BUILD" == 1 && -n "$completed" ]] && state_done "$completed" "$stage"; then log_info "Skipping completed stage: $stage"; continue; fi
    case "$stage" in
      docker) run_stage docker build_docker;;
      rootfs) run_stage rootfs export_rootfs;;
      boot) run_stage boot create_boot_menu;;
      branding) run_stage branding prepare_branding;;
      apache) run_stage apache prepare_apache;;
      features) run_stage features stage_features;;
      games) run_stage games stage_games;;
      squashfs) run_stage squashfs build_squashfs;;
      iso) run_stage iso build_iso;;
      verify) run_stage verify verify_iso;;
      report) run_stage report report_build;;
    esac
    completed="$stage"
  done
}

trap 'rc=$?; stop_watchdog || true; if ((rc!=0)); then log_error "Build stopped during stage: ${CURRENT_STAGE:-unknown}"; printf "%s\n" "${CURRENT_STAGE:-unknown}" > "$FAILED_FILE"; fi; exit "$rc"' EXIT
main "$@"
