#!/usr/bin/env bash
# Native x86_64 Koronos timer-preemption gate.
#
# Builds the real kernel, boots it through GRUB Multiboot2 in QEMU with one CPU,
# and requires measured timer ticks, preemptions, context switches, completed
# scheduler tasks, and clean stack guards. A timeout is expected once the
# kernel enters its non-terminating per-CPU scheduler loop.
#
# Usage: tools/runtime/check-koronos-preemption.sh [--help]

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos ELF64 kernel and verifies measured
x86_64 timer-preemption evidence.

Options:
  --help    Show this help and exit.

Artifacts:
  build/koronos-preemption/koronos-preemptive-sched.iso
  build/koronos-preemption/debugcon.log
  build/koronos-preemption/serial.log
  build/koronos-preemption/result.txt
  build/koronos-preemption/iso.sha256
"

if [[ "${1:-}" == "--help" ]]; then
  printf '%s' "$CHIMERA_HELP"
  exit 0
fi

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/koronos-preemption"
ISO="$OUT/koronos-preemptive-sched.iso"
KERNEL="$ROOT/build/koronos/x86_64/koronos.elf"
DEBUGLOG="$OUT/debugcon.log"
SERIALL="$OUT/serial.log"
RESULT="$OUT/result.txt"

fail() { echo "FAIL: $*" >&2; exit 1; }
require() { command -v "$1" >/dev/null 2>&1 || fail "required tool not found: $1"; }

for tool in bash make nasm g++ ld grub-file grub-mkrescue qemu-system-x86_64 timeout sha256sum; do
  require "$tool"
done

mkdir -p "$OUT/isoroot/boot/grub"
rm -f "$ISO" "$DEBUGLOG" "$SERIALL" "$RESULT" "$OUT/iso.sha256"

echo "== Building native Koronos kernel =="
bash "$ROOT/kernel/build-koronos.sh" >/dev/null
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
menuentry "Koronos native preemption gate" {
  multiboot2 /boot/koronos.elf
  boot
}
GRUB

echo "== Building Multiboot2 preemption test ISO =="
grub-mkrescue -o "$ISO" "$OUT/isoroot" >/dev/null
sha256sum "$ISO" >"$OUT/iso.sha256"

echo "== Booting QEMU (1 CPU, PIT preemption enabled) =="
set +e
timeout 30s qemu-system-x86_64 \
  -machine pc -cpu max -smp 1 -m 256M \
  -cdrom "$ISO" -boot d \
  -serial "file:$SERIALL" \
  -debugcon "file:$DEBUGLOG" \
  -global isa-debugcon.iobase=0xe9 \
  -display none -no-reboot >"$OUT/qemu.stdout" 2>"$OUT/qemu.stderr"
qemu_rc=$?
set -e
[[ "$qemu_rc" -eq 0 || "$qemu_rc" -eq 124 ]] || fail "QEMU exited with $qemu_rc"

field() {
  grep -aF "$1" "$DEBUGLOG" | tail -n 1 | tr -d '\r' | awk -F= '{print $2}'
}
number() {
  [[ "$2" =~ ^[0-9]+$ ]] || fail "$1 is not numeric: '$2'"
}

workers="$(field '[RTM ] WORKERS_SUBMITTED=')"
completed="$(field '[RTM ] RUNTIME_WORKERS_COMPLETED=')"
preemptions="$(field '[RTM ] PREEMPTIONS=')"
switches="$(field '[RTM ] CONTEXT_SWITCHES=')"
ticks="$(field '[RTM ] TIMER_TICKS=')"
guards="$(field '[RTM ] GUARD_FAILURES=')"
number workers_submitted "$workers"
number runtime_workers_completed "$completed"
number preemptions "$preemptions"
number context_switches "$switches"
number timer_ticks "$ticks"
number guard_failures "$guards"
[[ "$workers" -ge 2 ]] || fail "workers_submitted=$workers, expected >=2"
[[ "$completed" -ge "$workers" ]] || fail "runtime_workers_completed=$completed, expected >=$workers"
[[ "$preemptions" -gt 0 ]] || fail "timer preemptions=$preemptions, expected >0"
[[ "$switches" -ge "$workers" ]] || fail "context switches=$switches, expected >=$workers"
[[ "$ticks" -gt 0 ]] || fail "timer ticks=$ticks, expected >0"
[[ "$guards" -eq 0 ]] || fail "stack guard failures=$guards"

{
  echo "PASS: Koronos x86_64 measured timer-preemption gate"
  echo "QEMU_EXIT=$qemu_rc"
  echo "ISO_SHA256=$(awk '{print $1}' "$OUT/iso.sha256")"
  echo "WORKERS_SUBMITTED=$workers"
  echo "RUNTIME_WORKERS_COMPLETED=$completed"
  echo "PREEMPTIONS=$preemptions"
  echo "CONTEXT_SWITCHES=$switches"
  echo "TIMER_TICKS=$ticks"
  echo "GUARD_FAILURES=$guards"
} | tee "$RESULT"

echo "PASS: measured preemption evidence written to $RESULT"
