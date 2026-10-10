#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/kernel/arch/x86_32"
BUILD="${CHIMERA32_BUILD_DIR:-$ROOT/build/koronos32-bringup}"
ISO="$BUILD/koronos32-probe.iso"
LOG="$BUILD/qemu-serial.log"
TIMEOUT_SECONDS="${CHIMERA32_QEMU_TIMEOUT:-12}"

for tool in make gcc ld grub-mkrescue xorriso qemu-system-i386 timeout readelf; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing required tool: $tool" >&2; exit 2; }
done
mkdir -p "$BUILD"
make -C "$SRC" clean all check BUILD="$BUILD/objects"
mkdir -p "$BUILD/iso/boot/grub"
cp "$BUILD/objects/koronos32-probe.elf" "$BUILD/iso/boot/koronos32-probe.elf"
cat > "$BUILD/iso/boot/grub/grub.cfg" <<'GRUBCFG'
set timeout=0
set default=0
menuentry "Koronos 32-bit bring-up probe" {
    multiboot /boot/koronos32-probe.elf
    boot
}
GRUBCFG
grub-mkrescue -o "$ISO" "$BUILD/iso" >/dev/null
set +e
timeout "$TIMEOUT_SECONDS" qemu-system-i386 -machine pc -m 128M -cdrom "$ISO" -display none -serial file:"$LOG" -monitor none -no-reboot -no-shutdown
qemu_status=$?
set -e
if ! grep -Fq 'KORONOS32_BOOT_OK' "$LOG"; then
  echo "32-bit QEMU boot smoke test failed (qemu exit=$qemu_status); serial log:" >&2
  cat "$LOG" >&2 || true
  exit 1
fi
echo "PASS: 32-bit ELF booted in QEMU and emitted KORONOS32_BOOT_OK"
echo "NOTE: this validates only the isolated serial bring-up probe, not the production Koronos kernel or full ISO."
