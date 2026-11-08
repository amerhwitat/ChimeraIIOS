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
if command -v file >/dev/null 2>&1 && ! file "$BB" | grep -qi 'statically linked'; then
  echo "ERROR: a statically linked BusyBox is required for the initramfs; install busybox-static." >&2
  exit 2
fi
cp "$BB" "$P/bin/busybox"
# Expose every applet implemented by the shipped BusyBox binary, not just a hand-picked subset.
while IFS= read -r applet; do
  [[ -n "$applet" && "$applet" != "busybox" ]] || continue
  [[ "$applet" == */* ]] && continue
  ln -sf busybox "$P/bin/$applet"
done < <("$BB" --list)
# Keep compatibility aliases required by the init scripts even if a BusyBox
# build omits an optional applet.
for x in sh mount umount switch_root mkdir cat echo ls cp mv sleep sync ps top tail date clear sed awk head ip udhcpc nslookup gzip; do ln -sf busybox "$P/bin/$x"; done

# Embed the complete command/ISA catalogues and an evidence-based implementation map.
install -d "$P/etc/chimera/catalogs"
for rel in system/commands/chimera-command-list.json system/commands/ss64-command-catalog.json system/commands/ss64-command-catalog.ar.json system/commands/native-command-candidates.json system/commands/command-runtime-capabilities.json system/commands/compatibility-binary-policy.json system/commands/native-provider-aliases.json config/linux-command-registry.json tools/commands/os-command-runtime.json ISA.csv isa/catalog.json isa/generated/universal-instruction-catalog.json isa/generated/isa-encoding-registry.json data/isa/online-isa-index.json \
isa/generated/isa-encoding-samples.json    isa/generated/source-discovery-index.json    isa/instructions.json isa/isa_database.json isa/isa_database.sql isa/schema.json    isa/world_architectures.json isa/spec/chimera_isa.yaml isa/spec/compatibility_targets.yaml    tools/isa/architecture-backends.json tools/isa/instruction-semantics.schema.json    tools/isa/isa_bitfields.schema.json tools/isa/local_isa_catalog.json    tools/isa/cisc-coverage.json tools/isa/rv32i-coverage.json    tools/isa/rv32-machine-tested-subset.json; do
  if [[ -s "$ROOT/$rel" ]]; then install -D -m 0644 "$ROOT/$rel" "$P/etc/chimera/catalogs/$(basename "$rel")"; fi
done
install -D -m 0644 "$ROOT/aurora/terminals/registry.json" "$P/etc/chimera/catalogs/terminals-registry.json"
install -D -m 0644 "$ROOT/aurora/shells/registry.json" "$P/etc/chimera/catalogs/shells-registry.json"
bash "$ROOT/tools/commands/install-busybox-applets.sh" "$P"
python3 "$ROOT/tools/commands/build-command-isa-coverage.py" \
  --root "$ROOT" --busybox "$BB" --rootfs "$P" \
  --output "$P/etc/chimera/catalogs/command-isa-coverage.json"
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
( cd "$P" && find . -print0 | cpio --null -o -H newc ) > "$DEST/install/installer/installation.cpio"
(cd "$DEST/install/installer" && sha256sum installation.cpio > installation.cpio.sha256)
( cd "$P" && find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -9 ) > "$DEST/install/installer/installation.img"
cp -f "$DEST/install/installer/installation.img" "$DEST/install/installer/installer-initrd.img"
for f in "$ROOT/install/installation-manifest.json" "$ROOT/install/installer-contract.json" "$ROOT/installer/installation_phases.json" "$ROOT/installer/installer_profiles.json" "$ROOT/installer/profiles/chimera-installer-features.json" "$ROOT/installer/profiles/filesystem-support.json"; do [[ -f "$f" ]] && cp -f "$f" "$DEST/install/installer/"; done
printf '[INFO] Installer media staged in %s/install/installer\n' "$DEST"
