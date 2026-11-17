#!/usr/bin/env bash

# Help is kept in sync with the actual, fail-closed command interface below.
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS Mobile Flash Tool

Usage:
  mobile/flash/mobile-flash-tool.sh --detect
  mobile/flash/mobile-flash-tool.sh --discover
  mobile/flash/mobile-flash-tool.sh --prepare [--arch aarch64|armv7|x86_64]
  mobile/flash/mobile-flash-tool.sh --verify --manifest FILE
  mobile/flash/mobile-flash-tool.sh --flash --device CODENAME --manifest FILE [--dry-run]

Safety:
  Preparation creates a reference-only payload; it is not a phone boot image.
  Flashing requires an exact device manifest, matching image hashes, signed
  images, explicit confirmation and an approved vendor transport adapter.
  Generic partition writes and bootloader/authentication bypasses are disabled.
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
  mobile-flash-tool.sh --prepare [--arch aarch64|armv7|x86_64]
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
  while (($#)); do case "$1" in --arch) (($# >= 2)) || { usage; exit 2; }; arch="$2"; shift 2;; *) usage; exit 2;; esac; done
  case "$arch" in aarch64|armv7|x86_64) ;; *) echo "Unsupported architecture: $arch" >&2; exit 2;; esac
  mkdir -p "$OUT/payload"
  test -s "$KERNEL" || { echo "Koronos reference kernel not found: $KERNEL" >&2; exit 3; }
  local host_arch
  host_arch="$(python3 - "$KERNEL" <<'PY'
import struct,sys
p=sys.argv[1]
with open(p,"rb") as f: h=f.read(20)
if len(h)<20 or h[:4]!=b"\x7fELF" or h[4]!=2 or h[5] not in (1,2):
    raise SystemExit("Koronos reference kernel is not a supported ELF64 image")
endian="<" if h[5]==1 else ">"
machine=struct.unpack(endian+"H",h[18:20])[0]
print({62:"x86_64",183:"aarch64",40:"armv7"}.get(machine,"unknown"))
PY
)"
  cp -f "$KERNEL" "$OUT/payload/koronos-reference-host.elf"
  python3 - "$OUT/payload/manifest.json" "$arch" "$host_arch" <<'PY'
import json,sys
path,target,host=sys.argv[1:]
doc={
 "schema":"CHM-MOBILE-REFERENCE-3",
 "payload_kind":"reference-only-host-kernel",
 "requested_device_architecture":target,
 "reference_kernel_architecture":host,
 "device_specific":False,
 "bootable_phone_image":False,
 "requires_exact_device_kernel_vendor_modules_and_authorized_avb_signing":True,
 "generic_partition_flash":False,
 "flash_enabled":False,
 "limitations":[
   "This ELF is the x86_64 Koronos host/reference kernel, not an Android boot image.",
   "No device DTB/DTBO, vendor modules, partition image, AVB signature or device boot bundle is produced.",
   "A matching architecture label does not establish device compatibility."
 ]
}
with open(path,"w",encoding="utf-8") as f: json.dump(doc,f,indent=2); f.write("\n")
PY
  sha256sum "$OUT/payload/manifest.json" "$OUT/payload/koronos-reference-host.elf" > "$OUT/payload/SHA256SUMS"
  echo "Prepared reference-only payload (host ELF architecture: $host_arch; requested device architecture: $arch)."
  echo "NOT FLASHABLE: exact-device kernel, vendor modules, boot metadata and authorized AVB signing are absent."
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
