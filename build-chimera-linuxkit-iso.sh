#!/usr/bin/env bash
set -euo pipefail

# Chimera II OS: Docker image -> bootable LinuxKit BIOS + UEFI ISO.
# Docker supplies the Chimera userspace; LinuxKit supplies kernel/init/boot media.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${CHIMERA_IMAGE:-amerhwitat/chimera2os}:${DOCKER_TAG:-latest}"
LINUXKIT_VERSION="${LINUXKIT_VERSION:-v1.8.2}"
OUT="${SCRIPT_DIR}/build/linuxkit"
TEMPLATE="${SCRIPT_DIR}/boot/linuxkit/chimera2os.yml"
CONFIG="${OUT}/chimera2os.generated.yml"
LINUXKIT="${OUT}/linuxkit"

info(){ printf '[INFO] %s\n' "$*"; }
die(){ printf '[ERROR] %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null || die "docker is required"
command -v curl >/dev/null || die "curl is required"
command -v sha256sum >/dev/null || die "sha256sum is required"
command -v sed >/dev/null || die "sed is required"
docker info >/dev/null 2>&1 || die "Docker daemon is unavailable"
[[ -f "$TEMPLATE" ]] || die "Missing $TEMPLATE"
mkdir -p "$OUT"

if [[ ! -x "$LINUXKIT" ]]; then
  case "$(uname -m)" in
    x86_64|amd64) ARCH=amd64 ;;
    aarch64|arm64) ARCH=arm64 ;;
    s390x) ARCH=s390x ;;
    *) die "Unsupported host architecture: $(uname -m)" ;;
  esac
  URL="https://github.com/linuxkit/linuxkit/releases/download/$LINUXKIT_VERSION/linuxkit-linux-$ARCH"
  info "Downloading LinuxKit $LINUXKIT_VERSION ($ARCH)"
  curl -fL --retry 3 "$URL" -o "$LINUXKIT"
  chmod +x "$LINUXKIT"
fi

info "LinuxKit: $("$LINUXKIT" version 2>/dev/null || true)"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  info "Pulling $IMAGE"
  docker pull "$IMAGE"
fi
docker image inspect "$IMAGE" >/dev/null || die "Cannot inspect $IMAGE"

sed "s#amerhwitat/chimera2os:latest#$IMAGE#g" "$TEMPLATE" > "$CONFIG"
grep -Fq "image: $IMAGE" "$CONFIG" || die "Generated config does not contain $IMAGE"

rm -f "$OUT/ChimeraIIOS-linuxkit-bios.iso" "$OUT/ChimeraIIOS-linuxkit-efi.iso"

info "Building BIOS/El Torito ISO"
"$LINUXKIT" build --format iso-bios \
  --name "$OUT/ChimeraIIOS-linuxkit-bios" "$CONFIG"

info "Building UEFI ISO"
"$LINUXKIT" build --format iso-efi \
  --name "$OUT/ChimeraIIOS-linuxkit-efi" "$CONFIG"

BIOS="$OUT/ChimeraIIOS-linuxkit-bios.iso"
EFI="$OUT/ChimeraIIOS-linuxkit-efi.iso"
[[ -s "$BIOS" ]] || die "BIOS ISO was not produced"
[[ -s "$EFI" ]] || die "UEFI ISO was not produced"

sha256sum "$BIOS" | tee "$BIOS.sha256"
sha256sum "$EFI" | tee "$EFI.sha256"

cat > "$OUT/build-manifest.txt" <<EOF
Chimera II OS LinuxKit ISO build
UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Docker image: $IMAGE
LinuxKit: $LINUXKIT_VERSION
BIOS ISO: $BIOS
$(sha256sum "$BIOS")
UEFI ISO: $EFI
$(sha256sum "$EFI")
Boot chain: Firmware -> LinuxKit bootloader -> LinuxKit kernel -> init/containerd/runc -> Chimera service
EOF

if command -v xorriso >/dev/null 2>&1; then
  xorriso -indev "$BIOS" -report_el_torito plain 2>/dev/null || true
  xorriso -indev "$EFI" -report_el_torito plain 2>/dev/null || true
fi

info "BIOS ISO: $BIOS"
info "UEFI ISO: $EFI"
info "Manifest: $OUT/build-manifest.txt"
