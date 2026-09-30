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

log_file(){ mkdir -p "$LOG_DIR"; printf "[%s] %s\\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG_DIR/chimera-build.log"; }
log_both(){ log_info "$*"; log_file "$*"; }
process_snapshot(){
  mkdir -p "$LOG_DIR"
  {
    echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) PROCESS SNAPSHOT ====="
    echo "-- host processes --"
    ps -eo pid,ppid,stat,%cpu,%mem,etime,cmd --sort=-%cpu 2>/dev/null | head -n 35 || true
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
  [[ -s "$BUILD_DIR/live-boot/boot/vmlinuz" ]] && cp "$BUILD_DIR/live-boot/boot/vmlinuz" "$ISO_DIR/boot/live/" || true
  [[ -f "$SCRIPT_DIR/boot/iso/grub.cfg" ]] && cp "$SCRIPT_DIR/boot/iso/grub.cfg" "$ISO_DIR/boot/grub/grub.cfg" || cat > "$ISO_DIR/boot/grub/grub.cfg" <<'EOF'
set timeout=5
menuentry 'Chimera II OS Live' { multiboot2 /boot/kernel.bin; boot }
EOF
}

add_branding(){
  mkdir -p "$ROOTFS_DIR/etc" "$ROOTFS_DIR/var/log/chimera" "$ROOTFS_DIR/usr/share/chimera/aurora"
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
  mkdir -p "$ISO_DIR/system" "$ISO_DIR/desktop" "$ISO_DIR/network" "$ISO_DIR/drivers" "$ISO_DIR/install"
  for d in services userland desktop network installer system/security; do [[ -d "$SCRIPT_DIR/$d" ]] && cp -a "$SCRIPT_DIR/$d" "$ISO_DIR/system/" 2>/dev/null || true; done
  [[ -f "$SCRIPT_DIR/appcenter/catalog/game-registry.json" ]] && true
  mkdir -p "$ROOTFS_DIR/etc/chimera" "$ROOTFS_DIR/usr/share/chimera"
  [[ -f "$SCRIPT_DIR/system/storage/chimera-storage.conf" ]] && cp -f "$SCRIPT_DIR/system/storage/chimera-storage.conf" "$ROOTFS_DIR/etc/chimera/"
  [[ -f "$SCRIPT_DIR/system/hardware/chimera-hardware-profile.json" ]] && cp -f "$SCRIPT_DIR/system/hardware/chimera-hardware-profile.json" "$ROOTFS_DIR/usr/share/chimera/"
  mkdir -p "$ROOTFS_DIR/usr/share/chimera/aurora/config" "$ROOTFS_DIR/usr/share/chimera/docs"
  for f in config/aurora/desktop-parity.json config/aurora/emulators.json config/aurora/free-roms.json config/aurora/emulator-windows.json config/aurora/emulator-associations.json config/chimera/kernel-desktop-parity.json config/chimera/platform-feature-policy.json; do
    [[ -f "$SCRIPT_DIR/$f" ]] && cp -f "$SCRIPT_DIR/$f" "$ROOTFS_DIR/usr/share/chimera/aurora/config/"
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
  mkdir -p "$p"/{bin,dev,proc,sys,run,tmp,mnt,target,etc,chimera/installer} "$p/run/chimera" "$p/var/log/chimera"
  local bb="$(command -v busybox || true)"; [[ -n "$bb" ]] && { cp "$bb" "$p/bin/busybox"; for x in sh mount umount switch_root mkdir cat echo ls cp mv sleep sync ps top tail date clear sed awk head; do ln -sf busybox "$p/bin/$x"; done; }
  for f in "$SCRIPT_DIR/install/installer-contract.json" "$SCRIPT_DIR/installer/installation_phases.json" "$SCRIPT_DIR/installer/installer_profiles.json" "$SCRIPT_DIR/installer/profiles/chimera-installer-features.json" "$SCRIPT_DIR/installer/profiles/filesystem-support.json"; do [[ -f "$f" ]] && cp -f "$f" "$p/chimera/installer/"; done
  cat > "$p/bin/chimera-installer-monitor" <<'EOF'
#!/bin/sh
while :; do
  clear
  echo "CHIMERA II OS — INSTALLER LOG / PROCESSES"
  echo "------------------------------------------"
  ps 2>/dev/null || true
  echo
  echo "INSTALLER LOG"
  tail -n 22 /run/chimera/installer.log 2>/dev/null || true
  sleep 1
done
EOF
  chmod +x "$p/bin/chimera-installer-monitor"
  cat > "$p/init" <<'EOF'
#!/bin/sh
set -eu
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
echo 'Chimera II OS Native Installation Environment'
mkdir -p /run/chimera /var/log/chimera
printf '[INST] Installer environment started\\n' >> /run/chimera/installer.log
( /bin/chimera-installer-monitor > /dev/console 2>&1 ) &
exec /bin/sh
EOF
  chmod +x "$p/init"
  (cd "$p" && find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -9) > "$ISO_DIR/install/installer/installation.img"
  cp -f "$ISO_DIR/install/installer/installation.img" "$ISO_DIR/install/installer/installer-initrd.img"
  sha256sum "$ISO_DIR/install/installer/installation.img" > "$ISO_DIR/install/installer/installation.img.sha256"
  sha256sum "$ISO_DIR/install/installer/installer-initrd.img" > "$ISO_DIR/install/installer/installer-initrd.img.sha256"
  cat > "$ISO_DIR/install/installer/installation-manifest.json" <<'EOF'
{"schema":"CHM-INSTALLATION-MEDIA-2","image":"/install/installer/installation.img","legacy_image":"/install/installer/installer-initrd.img","image_format":"gzip-compressed-cpio-newc","boot_manager":"Jasper","kernel":"/boot/koronos/koronos.elf","bootable":true}
EOF
  rm -rf "$p"
}

create_squashfs(){
  header 'STEP 4: CREATING SQUASHFS FILESYSTEM'
  local out="$ISO_DIR/live/filesystem.squashfs" tmp="$ISO_DIR/live/filesystem.squashfs.building"
  [[ -d "$ROOTFS_DIR" ]] || { log_error "Rootfs staging directory missing: $ROOTFS_DIR"; exit 1; }
  mkdir -p "$ISO_DIR/live"

  # CRITICAL: never allow mksquashfs to open an existing filesystem for append.
  # A resumable build may leave a previous image and a recovery file behind.
  # Remove both the final target and temporary target before invoking mksquashfs.
  # The new image is constructed independently and moved into place only after
  # mksquashfs returns zero. This makes retries idempotent and eliminates *_1
  # duplicate directory names caused by accidental append mode.
  rm -f -- "$tmp" "$out"
  find "$ISO_DIR/live" -maxdepth 1 -type f -name 'filesystem.squashfs.*' ! -name 'filesystem.squashfs.building' -delete 2>/dev/null || true
  log_info "mksquashfs: fresh image, explicit -noappend"
  mksquashfs "$ROOTFS_DIR" "$tmp" -noappend -no-progress -processors "${CHIMERA_SQUASHFS_PROCESSORS:-4}" -comp xz
  [[ -s "$tmp" ]] || { log_error 'mksquashfs returned success but produced no image'; exit 1; }
  mv -f -- "$tmp" "$out"
  sha256sum "$out" > "$out.sha256"
  log_success "SquashFS created: $(du -h "$out" | cut -f1)"
  rm -rf "$ROOTFS_DIR"
}

create_iso(){
  header 'STEP 5: CREATING BIOS + UEFI ISO'
  local iso="${ISO_OUTPUT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
  [[ -s "$ISO_DIR/live/filesystem.squashfs" ]] || { log_error 'filesystem.squashfs missing'; exit 1; }
  [[ -s "$ISO_DIR/boot/kernel.bin" ]] || { log_error 'kernel.bin missing'; exit 1; }
  [[ -s "$ISO_DIR/boot/live/chimera-live-initramfs.img" ]] || { log_error 'live initramfs missing'; exit 1; }
  [[ -s "$ISO_DIR/install/installer/installation.img" ]] || { log_error 'installation image missing'; exit 1; }
  local payload="$(du -sb "$ISO_DIR" | awk '{print $1}')" free="$(free_bytes "$ISO_OUTPUT_DIR")" need=$((payload+268435456))
  if ((free<need)); then log_error "ISO output needs $(numfmt --to=iec "$need") but only $(numfmt --to=iec "$free") is free"; exit 1; fi
  grub-mkrescue -o "$iso" "$ISO_DIR" -iso-level 3 -J -R -V CHIMERA_II_OS
  sha256sum "$iso" > "$iso.sha256"
  log_success "ISO created: $iso"
}

verify_iso(){
  local iso="${ISO_OUTPUT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
  [[ -s "$iso" ]] || return 1
  sha256sum -c "$iso.sha256"
  log_success "ISO checksum verified"
}

report(){
  cat > "$SCRIPT_DIR/build-report.txt" <<EOF
Chimera II OS Comprehensive ISO
Build date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
ISO: ${ISO_OUTPUT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso
SquashFS: ${ISO_DIR}/live/filesystem.squashfs
EOF
}

failure(){ local rc=$?; stop_watchdog || true; if ((rc!=0 && BUILD_SUCCEEDED==0)); then printf 'schema=2\nfailed_stage=%s\nexit_code=%s\n' "$CURRENT_STAGE" "$rc" > "$FAILED_FILE"; log_error "Build stopped during stage: ${CURRENT_STAGE:-unknown}"; log_error "Checkpoint retained: $STATE_FILE"; fi; return $rc; }
trap failure EXIT

main(){
  header 'CHIMERA II OS - COMPREHENSIVE ISO BUILD SYSTEM'
  preflight; check_deps
  local completed=""; [[ "$CLEAN_STATE" == 1 ]] && state_reset
  [[ "$RESUME_BUILD" == 1 || -f "$STATE_FILE" ]] && completed="$(state_get)"
  [[ -n "$completed" ]] && log_info "Resuming after completed stage: $completed"

  if ! state_done "$completed" docker; then build_docker; state_mark docker; completed=docker; fi
  if ! state_done "$completed" rootfs; then export_rootfs; state_mark rootfs; completed=rootfs; fi
  if ! state_done "$completed" boot; then run_stage boot create_boot_menu; completed=boot; fi
  if ! state_done "$completed" branding; then run_stage branding add_branding; completed=branding; fi
  if ! state_done "$completed" apache; then run_stage apache prepare_apache; completed=apache; fi
  if ! state_done "$completed" features; then run_stage features stage_features; completed=features; fi
  if ! state_done "$completed" games; then run_stage games stage_games; completed=games; fi
  if ! state_done "$completed" squashfs; then create_installer; run_stage squashfs create_squashfs; completed=squashfs; fi
  if ! state_done "$completed" iso; then run_stage iso create_iso; completed=iso; fi
  if ! state_done "$completed" verify; then run_stage verify verify_iso; completed=verify; fi
  if ! state_done "$completed" report; then run_stage report report; completed=report; fi
  BUILD_SUCCEEDED=1; state_reset
  log_success "BUILD COMPLETED SUCCESSFULLY"
  log_success "ISO: ${ISO_OUTPUT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
}

main "$@"
