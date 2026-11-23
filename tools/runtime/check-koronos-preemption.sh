#!/usr/bin/env bash
# Native x86_64 Koronos preemption gate.
#
# Builds the real kernel, boots it through GRUB Multiboot2 in QEMU with one CPU,
# and requires the in-kernel selftest to prove assembly callee-saved context
# save/restore, independent guarded task stacks, PIT preemption, and two-task
# interleaving. A timeout is expected once the kernel returns to its idle loop.
#
# Usage: tools/runtime/check-koronos-preemption.sh [--help]

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos ELF64 kernel and verifies the x86_64
preemptive scheduler gate.

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
menuentry "Koronos native preemption gate" {
  multiboot2 /boot/koronos.elf
  boot
}
GRUB

echo "== Building Multiboot2 preemption test ISO =="
grub-mkrescue -o "$ISO" "$OUT/isoroot"
sha256sum "$ISO" | tee "$OUT/iso.sha256"

echo "== Booting QEMU (1 CPU, PIT preemption enabled) =="
set +e
timeout 30s qemu-system-x86_64 \
  -machine pc \
  -cpu max \
  -smp 1 \
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

assert_token "[PMT ] x86_64 CALLEE-SAVED CONTEXT SWITCH (GPR+RSP+IRETQ)"
assert_token "[PMT ] task entry id=1"
assert_token "[PMT ] task entry id=2"
assert_token "[PMT ] SELFTEST PASS"
assert_token "[PMT ] guard_failures=0"
assert_token "[PMT ] Native x86_64 context-save/timer-preemption gate passed"

task_a="$(field '[PMT ] task_A_iterations=')"
task_b="$(field '[PMT ] task_B_iterations=')"
timers="$(field '[PMT ] timer_preemptions=')"
switches="$(field '[PMT ] context_switches=')"
interleavings="$(field '[PMT ] interleavings=')"
guards="$(field '[PMT ] guard_failures=')"

[[ "$task_a" == "8" ]] || fail "task A iterations=$task_a, expected 8"
[[ "$task_b" == "8" ]] || fail "task B iterations=$task_b, expected 8"
[[ "$timers" -ge 4 ]] || fail "timer preemptions=$timers, expected >=4"
[[ "$switches" -ge 6 ]] || fail "context switches=$switches, expected >=6"
[[ "$interleavings" -ge 6 ]] || fail "interleavings=$interleavings, expected >=6"
[[ "$guards" == "0" ]] || fail "stack guard failures=$guards"
grep -aEq '^\[PMT \] order=[AB]{16}$' "$DEBUGLOG" || fail "two-task order trace missing or malformed"

{
  echo "PASS: Koronos x86_64 preemptive context-switch/timer gate"
  echo "QEMU_EXIT=$qemu_rc"
  echo "ISO_SHA256=$(awk '{print $1}' "$OUT/iso.sha256")"
  echo "TASK_A_ITERATIONS=$task_a"
  echo "TASK_B_ITERATIONS=$task_b"
  echo "TIMER_PREEMPTIONS=$timers"
  echo "CONTEXT_SWITCHES=$switches"
  echo "INTERLEAVINGS=$interleavings"
  echo "GUARD_FAILURES=$guards"
  grep -aF '[PMT ] order=' "$DEBUGLOG" | tail -n 1 | tr -d '\r'
} | tee "$RESULT"

echo "PASS: native preemption evidence written to $RESULT"
