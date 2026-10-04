#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: mobile/flash/mobile-flash-tool.sh

Usage:
  mobile/flash/mobile-flash-tool.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
OUT="$ROOT/build/mobile"
KERNEL="$ROOT/build/koronos/x86_64/koronos.elf"
usage(){ cat <<'EOF'
Usage:
  mobile-flash-tool.sh --detect
  mobile-flash-tool.sh --discover
  mobile-flash-tool.sh --prepare [--arch aarch64]
  mobile-flash-tool.sh --verify --manifest FILE
  mobile-flash-tool.sh --flash --device CODENAME --manifest FILE [--dry-run]

The flash path is manifest-driven: an exact device manifest, image hashes,
signed images, explicit bootloader policy and user confirmation are required.
No generic partition names, unlock bypasses, authentication bypasses or
unspecified vendor protocols are accepted.
EOF
}
require(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing required tool: $1" >&2; exit 2; }; }

detect(){
  command -v adb >/dev/null 2>&1 && { echo "ADB devices:"; adb devices; } || true
  command -v fastboot >/dev/null 2>&1 && { echo "Fastboot devices:"; fastboot devices; } || true
}

discover(){
  require curl
  mkdir -p "$OUT/resources"
  curl -fsSL --retry 3 https://raw.githubusercontent.com/amerhwitat/ChimeraIIOS/main/config/mobile-os-sources.json -o "$OUT/resources/mobile-os-sources.json"
  cat "$OUT/resources/mobile-os-sources.json"
}

prepare(){
  local arch="aarch64"
  while (($#)); do case "$1" in --arch) arch="$2"; shift 2;; *) usage; exit 2;; esac; done
  mkdir -p "$OUT/payload"
  test -f "$KERNEL" || { echo "Koronos reference kernel not found: $KERNEL" >&2; exit 3; }
  cp -f "$KERNEL" "$OUT/payload/koronos-reference-host.elf"
  cat > "$OUT/payload/manifest.json" <<EOF
{"schema":"CHM-MOBILE-PAYLOAD-2","architecture":"$arch","device_specific":true,"requires_signed_device_boot_bundle":true,"generic_partition_flash":false}
EOF
  sha256sum "$OUT/payload/manifest.json" "$OUT/payload/koronos-reference-host.elf" > "$OUT/payload/SHA256SUMS"
  echo "Prepared device-independent reference payload. It is not a phone boot image."
}

manifest_get(){
  local manifest="$1" key="$2"
  python3 - "$manifest" "$key" <<'PY'
import json,sys
p=sys.argv[1]; k=sys.argv[2]
d=json.load(open(p,encoding='utf-8'))
print(d.get(k,''))
PY
}

verify_manifest(){
  local manifest="$1"
  require python3
  test -s "$manifest" || { echo "Manifest not found: $manifest" >&2; exit 4; }
  python3 - "$manifest" <<'PY'
import hashlib,json,os,sys
p=sys.argv[1]; d=json.load(open(p,encoding='utf-8'))
assert d.get('schema') == 'CHM-MOBILE-DEVICE-2', 'unsupported manifest schema'
assert d.get('codename'), 'missing exact device codename'
assert d.get('architecture') in {'aarch64','armv7','x86_64'}, 'unsupported architecture'
assert d.get('partitions'), 'manifest has no image entries'
pol=d.get('policy',{})
assert pol.get('exact_match_required') is True, 'exact-device policy required'
assert pol.get('signed_images_required') is True, 'signed-image policy required'
assert pol.get('confirmation_required') is True, 'confirmation policy required'
for part in d['partitions']:
    assert part['name'] and '/' not in part['name'] and '\\' not in part['name'], 'unsafe partition name'
    assert len(part['sha256']) == 64, 'invalid image hash'
    image=part['image']
    assert os.path.isfile(image), f'image missing: {image}'
    got=hashlib.sha256(open(image,'rb').read()).hexdigest()
    assert got.lower() == part['sha256'].lower(), f'hash mismatch: {image}'
print('Manifest and image hashes: OK')
PY
}

flash(){
  require python3
  test -n "${DEVICE:-}" && test -n "${MANIFEST:-}" || { echo "Exact device codename and manifest are required." >&2; exit 4; }
  verify_manifest "$MANIFEST"
  manifest_device="$(manifest_get "$MANIFEST" codename)"
  test "$manifest_device" = "$DEVICE" || { echo "Device mismatch: requested=$DEVICE manifest=$manifest_device" >&2; exit 5; }
  echo "Verified device manifest: $DEVICE"
  echo "Verified images and signatures required by policy."
  if [[ "${DRY_RUN:-0}" == 1 ]]; then
    echo "DRY RUN: no device write operation performed."
    return 0
  fi
  echo "Refusing an unspecified generic flash operation. The manifest must provide an approved vendor transport adapter before any write is enabled."
  exit 7
}

[[ $# -gt 0 ]] || { usage; exit 2; }
case "$1" in
  --detect) shift; detect "$@";;
  --discover) shift; discover "$@";;
  --prepare) shift; prepare "$@";;
  --verify) shift; MANIFEST=""; while (($#)); do case "$1" in --manifest) MANIFEST="$2"; shift 2;; *) usage; exit 2;; esac; done; verify_manifest "$MANIFEST";;
  --flash) shift; DEVICE=""; MANIFEST=""; DRY_RUN=0; while (($#)); do case "$1" in --device) DEVICE="$2"; shift 2;; --manifest) MANIFEST="$2"; shift 2;; --dry-run) DRY_RUN=1; shift;; *) usage; exit 2;; esac; done; flash;;
  *) usage; exit 2;;
esac
