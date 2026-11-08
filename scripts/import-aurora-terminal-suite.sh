#!/usr/bin/env bash
# Build the complete registered Aurora terminal/shell suite in a target rootfs.
# Package providers are preferred; missing providers are built from source using
# the canonical source builder and its recorded source/build manifests.
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: scripts/import-aurora-terminal-suite.sh

Usage:
  scripts/import-aurora-terminal-suite.sh [options] [arguments]

Environment:
  CHIMERA_ROOTFS_DIR       Target Linux rootfs (default: build/iso/rootfs)
  CHIMERA_TERMINAL_CACHE   Source-build cache (default: build/terminal-cache)
  CHIMERA_TARGET_ARCH      Target architecture (default: read from target dpkg)

Builds and verifies all 8 registered shells and 20 registered terminal emulators.
A missing provider is a hard error; this script never creates placeholder binaries.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${CHIMERA_ROOTFS_DIR:-$ROOT/build/iso/rootfs}"
CACHE="${CHIMERA_TERMINAL_CACHE:-$ROOT/build/terminal-cache}"
MODE="${CHIMERA_TERMINAL_MODE:-package-first-source-fallback}"

if [[ "$MODE" != "package-first-source-fallback" && "$MODE" != "binary-only" ]]; then
  echo "Unsupported CHIMERA_TERMINAL_MODE=$MODE" >&2
  exit 2
fi
if [[ ! -x "$DEST/bin/sh" ]]; then
  echo "Target rootfs is missing or has no /bin/sh: $DEST" >&2
  exit 2
fi
if [[ "$(id -u)" -ne 0 ]]; then
  exec sudo -E env \
    CHIMERA_ROOTFS_DIR="$DEST" \
    CHIMERA_TERMINAL_CACHE="$CACHE" \
    CHIMERA_TERMINAL_MODE="$MODE" \
    CHIMERA_TARGET_ARCH="${CHIMERA_TARGET_ARCH:-}" \
    bash "${BASH_SOURCE[0]}" "$@"
fi

TARGET_ARCH="${CHIMERA_TARGET_ARCH:-}"
if [[ -z "$TARGET_ARCH" ]]; then
  target_dpkg="$(chroot "$DEST" dpkg --print-architecture 2>/dev/null || true)"
  case "$target_dpkg" in
    amd64) TARGET_ARCH=x86_64 ;;
    arm64) TARGET_ARCH=aarch64 ;;
    armel) TARGET_ARCH=armel ;;
    armhf) TARGET_ARCH=armv7 ;;
    i386) TARGET_ARCH=i686 ;;
    riscv64) TARGET_ARCH=riscv64 ;;
    ppc64el) TARGET_ARCH=ppc64le ;;
    s390x) TARGET_ARCH=s390x ;;
    *) echo "Cannot determine target architecture from dpkg ($target_dpkg); set CHIMERA_TARGET_ARCH." >&2; exit 2 ;;
  esac
fi

mkdir -p "$DEST/usr/share/chimera/aurora/terminals" "$DEST/usr/share/chimera/aurora/shells"
install -D -m 0644 "$ROOT/aurora/terminals/registry.json" "$DEST/usr/share/chimera/aurora/terminals/registry.json"
install -D -m 0644 "$ROOT/aurora/terminals/binary-manifest.json" "$DEST/usr/share/chimera/aurora/terminals/binary-manifest.json"
install -D -m 0644 "$ROOT/aurora/shells/registry.json" "$DEST/usr/share/chimera/aurora/shells/registry.json"
install -D -m 0644 "$ROOT/aurora/shells/binary-manifest.json" "$DEST/usr/share/chimera/aurora/shells/binary-manifest.json"

bash "$ROOT/tools/aurora/install-terminal-shell-suite.sh" "$DEST"
if [[ "$MODE" == "binary-only" ]]; then
  if [[ -s "$DEST/usr/share/chimera/aurora/terminal-shell-source-required.tsv" ]]; then
    echo "Unresolved terminal/shell packages remain in binary-only mode:" >&2
    cat "$DEST/usr/share/chimera/aurora/terminal-shell-source-required.tsv" >&2
    exit 2
  fi
else
  CHIMERA_TARGET_ARCH="$TARGET_ARCH" bash "$ROOT/tools/aurora/build-terminal-shell-sources.sh" "$DEST" "$CACHE"
fi

CHIMERA_TERMINAL_REQUIRE_ALL=1 bash "$ROOT/live-image/verify-terminal-shell-suite.sh" "$DEST" "$TARGET_ARCH"
python3 "$ROOT/tools/aurora/verify-terminal-shell-providers.py" \
  --rootfs "$DEST" \
  --shell-registry "$ROOT/aurora/shells/registry.json" \
  --terminal-registry "$ROOT/aurora/terminals/registry.json" \
  --output "$DEST/usr/share/chimera/aurora/terminal-shell-provider-status.json"

python3 - "$DEST/usr/share/chimera/aurora/terminal-shell-provider-status.json" <<'PY'
import json,sys
data=json.load(open(sys.argv[1],encoding="utf-8"))
summary=data.get("summary",{})
if summary.get("shells_registered")!=8 or summary.get("terminals_registered")!=20:
    raise SystemExit(f"unexpected registry counts: {summary}")
missing=[x.get("id") for section in ("shells","terminals") for x in data.get(section,[])
         if x.get("status") not in ("verified-elf-provider","verified-script-provider")]
if missing:
    raise SystemExit("terminal/shell providers missing or unverified: "+", ".join(missing))
print("Verified all 8 shell and 20 terminal registry providers.")
PY
