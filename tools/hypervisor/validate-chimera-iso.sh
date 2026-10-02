#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ISO="${1:-$ROOT/build/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso}"

fail(){ echo "[FAIL] $*" >&2; exit 1; }
ok(){ echo "[OK] $*"; }
[[ -s "$ISO" ]] || fail "ISO not found: $ISO"
command -v xorriso >/dev/null 2>&1 || fail "xorriso is required"
command -v file >/dev/null 2>&1 || fail "file is required"

REPORT="$(mktemp)"
trap 'rm -f "$REPORT"' EXIT
xorriso -indev "$ISO" -report_el_torito plain -report_system_area plain 2>&1 | tee "$REPORT"

grep -Eqi 'BIOS|i386-pc|no-emulation' "$REPORT" || fail "BIOS El Torito boot entry not detected"
grep -Eqi 'UEFI|EFI|x86_64-efi' "$REPORT" || fail "UEFI El Torito boot entry not detected"
ok "BIOS + UEFI El Torito entries detected"

EFI_LIST="$(mktemp)"
trap 'rm -f "$REPORT" "$EFI_LIST"' EXIT
xorriso -indev "$ISO" -find /EFI/BOOT -type f -print 2>&1 | tee "$EFI_LIST"
grep -Eqi '/EFI/BOOT/BOOTX64\.EFI$' "$EFI_LIST" || fail "UEFI fallback /EFI/BOOT/BOOTX64.EFI is missing"
ok "UEFI fallback BOOTX64.EFI present"

if command -v grub-file >/dev/null 2>&1; then
  if [[ -f "$ROOT/build/iso/boot/koronos/koronos.elf" ]]; then
    grub-file --is-x86-multiboot2 "$ROOT/build/iso/boot/koronos/koronos.elf" || fail "Koronos is not recognized as Multiboot2"
    ok "Koronos Multiboot2 payload"
  fi
fi

if command -v isoinfo >/dev/null 2>&1; then
  isoinfo -i "$ISO" -f 2>/dev/null | grep -Eqi '/BOOTX64\.EFI$' || fail "isoinfo cannot see /BOOTX64.EFI in ISO"
  ok "isoinfo sees UEFI BOOTX64.EFI"
fi

file "$ISO"
ok "ISO structure is suitable for BIOS/UEFI CD/DVD attachment"
echo ""
echo "Hyper-V: Generation 1 uses BIOS; Generation 2 uses UEFI."
echo "VMware: firmware=\"bios\" uses BIOS; firmware=\"efi\" uses UEFI."
echo "Secure Boot: disabled by the provided hypervisor helpers because the current Chimera BOOTX64.EFI is not Microsoft-signed."
