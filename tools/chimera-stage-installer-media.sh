#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-stage-installer-media.sh

Usage:
  tools/chimera-stage-installer-media.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:?usage: chimera-stage-installer-media.sh <iso-tree>}"
mkdir -p "$DEST/install/installer"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
P="$WORK/initramfs"
mkdir -p "$P"/{bin,dev,proc,sys,run,tmp,mnt,target,etc,chimera/installer,var/log}
BB="$(command -v busybox || true)"
if [[ -z "$BB" ]]; then echo "ERROR: busybox is required to build installation.img" >&2; exit 2; fi
cp "$BB" "$P/bin/busybox"
for x in sh mount umount switch_root mkdir cat echo ls cp mv sleep sync ps top tail date clear sed awk head ip udhcpc nslookup gzip; do ln -sf busybox "$P/bin/$x"; done
if [[ -f "$ROOT/tools/chimera-installer-runtime.sh" ]]; then cp -f "$ROOT/tools/chimera-installer-runtime.sh" "$P/bin/"; chmod +x "$P/bin/chimera-installer-runtime.sh"; fi
for f in "$ROOT/install/installer-contract.json" "$ROOT/installer/installation_phases.json" "$ROOT/installer/installer_profiles.json" "$ROOT/installer/profiles/chimera-installer-features.json" "$ROOT/installer/profiles/filesystem-support.json"; do [[ -f "$f" ]] && cp -f "$f" "$P/chimera/installer/"; done
cat > "$P/init" <<'EOF'
#!/bin/sh
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mount -t tmpfs tmpfs /run 2>/dev/null || true
mount -t tmpfs tmpfs /tmp 2>/dev/null || true
echo "[INSTALL] Chimera II OS installer environment"
if [ -x /bin/chimera-installer-runtime.sh ]; then /bin/chimera-installer-runtime.sh || echo "[INSTALL] Runtime initialization returned a nonzero status"; fi
echo "[INSTALL] Interactive recovery shell ready; disk operations remain disabled until an explicit install backend is configured."
exec /bin/sh
EOF
chmod +x "$P/init"
( cd "$P" && find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -9 ) > "$DEST/install/installer/installation.img"
cp -f "$DEST/install/installer/installation.img" "$DEST/install/installer/installer-initrd.img"
for f in "$ROOT/install/installation-manifest.json" "$ROOT/install/installer-contract.json" "$ROOT/installer/installation_phases.json" "$ROOT/installer/installer_profiles.json" "$ROOT/installer/profiles/chimera-installer-features.json" "$ROOT/installer/profiles/filesystem-support.json"; do [[ -f "$f" ]] && cp -f "$f" "$DEST/install/installer/"; done
printf '[INFO] Installer media staged in %s/install/installer\n' "$DEST"
