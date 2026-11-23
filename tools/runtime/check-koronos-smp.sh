#!/usr/bin/env bash
# Native x86_64 Koronos AP/SMP gate.
#
# Boots the real kernel with two vCPUs, sends real INIT/SIPI from the BSP, and
# requires the in-kernel selftest to prove AP online acknowledgement, distinct
# APIC identities, and simultaneous round progress observed from both CPUs.
# The preemption gate must pass first in the same boot trace.
#
# Usage: tools/runtime/check-koronos-smp.sh [--help]

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos ELF64 kernel with -smp 2 and verifies the
real-AP startup/two-CPU overlap gate.

Options:
  --help    Show this help and exit.

Artifacts:
  build/koronos-smp/koronos-smp-gate.iso
  build/koronos-smp/debugcon.log
  build/koronos-smp/serial.log
  build/koronos-smp/result.txt
  build/koronos-smp/iso.sha256
"

if [[ "${1:-}" == "--help" ]]; then
  printf '%s' "$CHIMERA_HELP"
  exit 0
fi

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/koronos-smp"
ISO="$OUT/koronos-smp-gate.iso"
KERNEL="$ROOT/build/koronos/x86_64/koronos.elf"
DEBUGLOG="$OUT/debugcon.log"
SERIALL="$OUT/serial.log"
RESULT="$OUT/result.txt"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

require() {
  command -v "$1" >/dev/null 2>&1 || fail "required tool not found: $1"
}

for tool in make nasm g++ ld grub-file grub-mkrescue qemu-system-x86_64 timeout sha256sum; do
  require "$tool"
done

mkdir -p "$OUT/isoroot/boot/grub"
rm -f "$ISO" "$DEBUGLOG" "$SERIALL" "$RESULT" "$OUT/iso.sha256"

echo "== Building native Koronos kernel =="
make -C "$ROOT/kernel" -j2
[[ -f "$KERNEL" ]] || fail "kernel ELF not produced at $KERNEL"
grub-file --is-x86-multiboot2 "$KERNEL" || fail "kernel is not Multiboot2"

install -m 0644 "$KERNEL" "$OUT/isoroot/boot/koronos.elf"
cat > "$OUT/isoroot/boot/grub/grub.cfg" <<'GRUB'
set timeout=0
set default=0
insmod serial
serial --unit=0 --speed=115200
terminal_input serial
terminal_output serial
menuentry "Koronos native AP/SMP gate" {
  multiboot2 /boot/koronos.elf
  boot
}
GRUB

echo "== Building Multiboot2 AP/SMP test ISO =="
grub-mkrescue -o "$ISO" "$OUT/isoroot"
sha256sum "$ISO" | tee "$OUT/iso.sha256"

echo "== Booting QEMU (2 CPUs, real INIT/SIPI) =="
set +e
timeout 180s qemu-system-x86_64 \
  -machine pc \
  -cpu max \
  -smp 2 \
  -m 256M \
  -cdrom "$ISO" \
  -boot d \
  -serial "file:$SERIALL" \
  -debugcon "file:$DEBUGLOG" \
  -global isa-debugcon.iobase=0xe9 \
  -display none \
  -no-reboot >"$OUT/qemu.stdout" 2>"$OUT/qemu.stderr"
qemu_rc=$?
set -e
[[ "$qemu_rc" -eq 0 || "$qemu_rc" -eq 124 ]] || fail "QEMU exited with $qemu_rc"

assert_token() {
  grep -aFq "$1" "$DEBUGLOG" || fail "missing debugcon token: $1"
}

field() {
  grep -aF "$1" "$DEBUGLOG" | tail -n 1 | tr -d '\r' | awk -F= '{print $2}'
}

# Ordered native gates: preemption evidence must precede AP/SMP acceptance.
assert_token "[PMT ] SELFTEST PASS"
assert_token "[SMP ] SELFTEST PASS"
assert_token "[SMP ] Native x86_64 AP startup/two-CPU overlap gate passed"
assert_token "[SMP ] tsc_overlap=1"

bsp_id="$(field '[SMP ] bsp_apic_id=')"
ap_id="$(field '[SMP ] ap_apic_id=')"
online="$(field '[SMP ] ap_online=')"
overlap="$(field '[SMP ] overlap_samples=')"
ap_rounds="$(field '[SMP ] ap_saw_bsp_rounds=')"
tsc_overlap="$(field '[SMP ] tsc_overlap=')"

[[ "$online" == "1" ]] || fail "AP online=$online, expected 1"
[[ "$overlap" == "256" ]] || fail "overlap samples=$overlap, expected 256"
[[ "$ap_rounds" == "256" ]] || fail "AP observed BSP rounds=$ap_rounds, expected 256"
[[ "$tsc_overlap" == "1" ]] || fail "TSC intervals did not overlap"
[[ -n "$bsp_id" && -n "$ap_id" && "$bsp_id" != "$ap_id" ]] || fail "BSP/AP APIC IDs are not distinct: bsp=$bsp_id ap=$ap_id"

{
  echo "PASS: Koronos x86_64 real-AP startup/two-CPU overlap gate"
  echo "QEMU_EXIT=$qemu_rc"
  echo "ISO_SHA256=$(awk '{print $1}' "$OUT/iso.sha256")"
  echo "BSP_APIC_ID=$bsp_id"
  echo "AP_APIC_ID=$ap_id"
  echo "AP_ONLINE=$online"
  echo "OVERLAP_SAMPLES=$overlap"
  echo "AP_SAW_BSP_ROUNDS=$ap_rounds"
  echo "TSC_OVERLAP=$tsc_overlap"
  grep -aF '[SMP ] bsp_tsc_start_lo=' "$DEBUGLOG" | tail -n 1 | tr -d '\r'
  grep -aF '[SMP ] ap_tsc_start_lo=' "$DEBUGLOG" | tail -n 1 | tr -d '\r'
  grep -aF '[SMP ] bsp_tsc_end_lo=' "$DEBUGLOG" | tail -n 1 | tr -d '\r'
  grep -aF '[SMP ] ap_tsc_end_lo=' "$DEBUGLOG" | tail -n 1 | tr -d '\r'
} | tee "$RESULT"

echo "PASS: native AP/SMP evidence written to $RESULT"
