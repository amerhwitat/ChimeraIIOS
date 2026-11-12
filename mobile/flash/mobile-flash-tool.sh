#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/mobile"

usage() {
  cat <<'EOF'
Chimera II Mobile Flash Tool

  mobile-flash-tool.sh --detect
  mobile-flash-tool.sh --prepare-reference [--arch aarch64]
  mobile-flash-tool.sh --verify --manifest FILE --signature FILE --public-key FILE
  mobile-flash-tool.sh --flash --device CODENAME --serial SERIAL \
      --manifest FILE --signature FILE --public-key FILE [--dry-run]

A flash manifest is signed with a trusted release key. The tool never unlocks
bootloaders, bypasses verified boot, flashes a generic disk, or guesses a device.
Actual writes require CHIMERA_FLASH_CONFIRM=YES and typing FLASH <serial>.
EOF
}

require() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required tool: $1" >&2; exit 2; }; }

detect() {
  if command -v adb >/dev/null 2>&1; then adb devices -l; else echo "ADB: unavailable"; fi
  if command -v fastboot >/dev/null 2>&1; then fastboot devices; else echo "Fastboot: unavailable"; fi
}

prepare_reference() {
  local arch=aarch64
  while (($#)); do
    case "$1" in --arch) (($# >= 2)) || { usage; exit 2; }; arch="$2"; shift 2;; *) usage; exit 2;; esac
  done
  [[ "$arch" == aarch64 ]] || { echo "Only the ARM64 reference build is defined." >&2; exit 3; }
  local kernel="$ROOT/build/koronos/arm64/koronos.elf"
  [[ -s "$kernel" ]] || { echo "ARM64 Koronos ELF missing: $kernel" >&2; exit 3; }
  require readelf; require sha256sum
  readelf -h "$kernel" | grep -Eq 'Machine:.*AArch64' || { echo "Kernel is not an AArch64 ELF." >&2; exit 3; }
  mkdir -p "$OUT/reference"
  install -m 0644 "$kernel" "$OUT/reference/koronos-arm64-reference.elf"
  sha256sum "$OUT/reference/koronos-arm64-reference.elf" > "$OUT/reference/SHA256SUMS"
  cat > "$OUT/reference/README.txt" <<'EOF'
Development reference payload only. This is not a bootable phone image.
A device-specific boot/vendor bundle, DTB/DTBO, initramfs, signed AVB metadata,
and hardware validation are required before a phone image can be released.
EOF
  echo "Prepared ARM64 development reference; no phone was modified."
}

verify_manifest() {
  local manifest="$1" signature="$2" public_key="$3"
  require python3; require openssl
  [[ -s "$manifest" && -s "$signature" && -s "$public_key" ]] || {
    echo "Manifest, detached signature, and public key must all exist." >&2; exit 4;
  }
  openssl dgst -sha256 -verify "$public_key" -signature "$signature" "$manifest" >/dev/null || {
    echo "Manifest signature verification FAILED." >&2; exit 5;
  }
  python3 - "$manifest" <<'PY'
import hashlib, json, pathlib, re, sys
p = pathlib.Path(sys.argv[1]).resolve()
d = json.loads(p.read_text(encoding="utf-8"))
assert d.get("schema") == "CHM-MOBILE-DEVICE-2", "unsupported manifest schema"
assert d.get("codename") and re.fullmatch(r"[A-Za-z0-9_.-]+", d["codename"]), "invalid device codename"
assert d.get("architecture") in {"aarch64", "armv7", "x86_64"}, "unsupported architecture"
assert d.get("bootloader_mode") == "fastboot", "only explicit fastboot manifests are currently supported"
pol = d.get("policy", {})
assert pol.get("exact_match_required") is True, "exact-device matching is mandatory"
assert pol.get("signed_images_required") is True, "signed images are mandatory"
assert pol.get("confirmation_required") is True, "typed confirmation is mandatory"
assert pol.get("generic_partition_names_forbidden") is True, "generic partition mapping must be forbidden"
parts = d.get("partitions")
assert isinstance(parts, list) and parts, "no partition payloads"
for item in parts:
    name = item.get("name", "")
    assert re.fullmatch(r"[A-Za-z0-9_.-]+", name), f"unsafe partition name: {name!r}"
    image = pathlib.Path(item.get("image", ""))
    image = (p.parent / image).resolve() if not image.is_absolute() else image.resolve()
    assert p.parent == image.parent or p.parent in image.parents, "image path escapes manifest directory"
    assert image.is_file() and image.stat().st_size > 0, f"missing/empty image: {image}"
    expected = item.get("sha256", "")
    assert re.fullmatch(r"[0-9a-fA-F]{64}", expected), f"invalid SHA-256 for {name}"
    actual = hashlib.sha256(image.read_bytes()).hexdigest()
    assert actual.lower() == expected.lower(), f"image digest mismatch: {name}"
print(f"Signed manifest and {len(parts)} image(s) verified for {d['codename']}.")
PY
}

flash_device() {
  local device="$1" serial="$2" manifest="$3" signature="$4" public_key="$5" dry_run="$6"
  require fastboot; require python3
  verify_manifest "$manifest" "$signature" "$public_key"
  local codename mode unlock_required
  codename="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["codename"])' "$manifest")"
  mode="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["bootloader_mode"])' "$manifest")"
  unlock_required="$(python3 -c 'import json,sys;print(str(json.load(open(sys.argv[1])).get("policy",{}).get("unlock_required",False)).lower())' "$manifest")"
  [[ "$device" == "$codename" ]] || { echo "Requested codename does not match signed manifest." >&2; exit 6; }
  [[ "$mode" == fastboot ]] || { echo "Manifest transport is not fastboot." >&2; exit 6; }
  local devices
  devices="$(fastboot devices | awk 'NF >= 2 {print $1}')"
  [[ "$(printf '%s\n' "$devices" | grep -xcF "$serial")" == 1 && "$(printf '%s\n' "$devices" | grep -c .)" == 1 ]] || {
    echo "Exactly one connected fastboot device with serial $serial is required." >&2; exit 7;
  }
  local product
  product="$(fastboot -s "$serial" getvar product 2>&1 | sed -nE 's/.*product:[[:space:]]*([^[:space:]]+).*/\1/p' | tail -n1)"
  [[ -n "$product" && "$product" == "$codename" ]] || {
    echo "Connected product '$product' does not exactly match '$codename'." >&2; exit 8;
  }
  if [[ "$unlock_required" == true ]]; then
    local unlocked
    unlocked="$(fastboot -s "$serial" getvar unlocked 2>&1 | sed -nE 's/.*unlocked:[[:space:]]*([^[:space:]]+).*/\1/p' | tail -n1)"
    [[ "$unlocked" == yes || "$unlocked" == true ]] || {
      echo "Manifest requires an already-unlocked bootloader. Tool will not unlock it." >&2; exit 9;
    }
  fi
  if [[ "$dry_run" == 1 ]]; then
    echo "DRY RUN: signed images, manifest, serial and product match; no writes performed."
    return 0
  fi
  [[ "${CHIMERA_FLASH_CONFIRM:-}" == YES ]] || {
    echo "Set CHIMERA_FLASH_CONFIRM=YES after reviewing the exact device and backup." >&2; exit 10;
  }
  [[ -t 0 ]] || { echo "Interactive typed confirmation is required." >&2; exit 10; }
  printf 'Type exactly: FLASH %s : ' "$serial"
  local answer; IFS= read -r answer
  [[ "$answer" == "FLASH $serial" ]] || { echo "Confirmation mismatch; aborted." >&2; exit 10; }
  echo "Flash writes are intentionally not enabled in this release: device-specific"
  echo "partition-size, slot, AVB and read-back verification adapters are not yet certified."
  echo "No device was modified."
  exit 11
}

[[ $# -gt 0 ]] || { usage; exit 2; }
cmd="$1"; shift
case "$cmd" in
  --help|-h) usage;;
  --detect) detect;;
  --prepare-reference) prepare_reference "$@";;
  --verify|--flash)
    device=""; serial=""; manifest=""; signature=""; public_key=""; dry_run=0
    while (($#)); do
      case "$1" in
        --device) (($# >= 2)) || { usage; exit 2; }; device="$2"; shift 2;;
        --serial) (($# >= 2)) || { usage; exit 2; }; serial="$2"; shift 2;;
        --manifest) (($# >= 2)) || { usage; exit 2; }; manifest="$2"; shift 2;;
        --signature) (($# >= 2)) || { usage; exit 2; }; signature="$2"; shift 2;;
        --public-key) (($# >= 2)) || { usage; exit 2; }; public_key="$2"; shift 2;;
        --dry-run) dry_run=1; shift;;
        *) usage; exit 2;;
      esac
    done
    [[ -n "$manifest" && -n "$signature" && -n "$public_key" ]] || { usage; exit 2; }
    if [[ "$cmd" == --verify ]]; then verify_manifest "$manifest" "$signature" "$public_key"
    else
      [[ -n "$device" && -n "$serial" ]] || { usage; exit 2; }
      flash_device "$device" "$serial" "$manifest" "$signature" "$public_key" "$dry_run"
    fi;;
  *) usage; exit 2;;
esac
