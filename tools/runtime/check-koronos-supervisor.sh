#!/usr/bin/env bash
# Native x86_64 Koronos kernel-owned PID 1 supervisor gate.
#
# Boots the real kernel with a Multiboot2 module cmdline selecting the
# supervisor gate. The kernel verifier drives the real supervisor API and the
# real cooperative scheduler: PID 1 is a resident task, children are submitted
# as scheduler tasks, exit codes come from the work they actually executed,
# zombies are waited/reaped, and a restartable service is restarted. Every
# checked value is measured from the boot trace; no fixed PASS is emitted.
#
# Usage: tools/runtime/check-koronos-supervisor.sh [--help]

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos ELF64 kernel and verifies kernel-owned
PID 1 lifetime, real child scheduling, wait/reap, and service restart.

Options:
  --help    Show this help and exit.

Artifacts:
  build/koronos-supervisor/koronos-supervisor-gate.iso
  build/koronos-supervisor/debugcon.log
  build/koronos-supervisor/serial.log
  build/koronos-supervisor/result.txt
  build/koronos-supervisor/iso.sha256
"

if [[ "${1:-}" == "--help" ]]; then
  printf '%s' "$CHIMERA_HELP"
  exit 0
fi

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/koronos-supervisor"
ISO="$OUT/koronos-supervisor-gate.iso"
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
rm -f "$ISO" "$DEBUGLOG" "$SERIALL" "$RESULT" "$OUT/iso.sha256" \
      "$OUT/qemu.stdout" "$OUT/qemu.stderr"

echo "== Building native Koronos kernel =="
make -C "$ROOT/kernel" -j2
[[ -f "$KERNEL" ]] || fail "kernel ELF not produced at $KERNEL"
grub-file --is-x86-multiboot2 "$KERNEL" || fail "kernel is not Multiboot2"

install -m 0644 "$KERNEL" "$OUT/isoroot/boot/koronos.elf"
# koronos-supervisor-gate selects this verifier. koronos-install-stack with no
# mode= token keeps the historical block/install gates out of this single boot.
printf '%s\n' "koronos-supervisor-gate koronos-install-stack" > "$OUT/isoroot/boot/supervisor.mode"
cat > "$OUT/isoroot/boot/grub/grub.cfg" <<'GRUB'
set timeout=0
set default=0
insmod serial
serial --unit=0 --speed=115200
terminal_input serial
terminal_output serial
menuentry "Koronos kernel-owned PID1 supervisor gate" {
  multiboot2 /boot/koronos.elf
  module2 /boot/supervisor.mode "koronos-supervisor-gate koronos-install-stack"
  boot
}
GRUB

echo "== Building Multiboot2 supervisor test ISO =="
grub-mkrescue -o "$ISO" "$OUT/isoroot"
sha256sum "$ISO" | tee "$OUT/iso.sha256"

echo "== Booting QEMU (1 CPU, kernel-owned PID1 supervisor gate) =="
set +e
timeout 60s qemu-system-x86_64 \
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

assert_token "[SUP ] Kernel-owned PID1 supervisor resident"
assert_token "[SUP ] PID1_STATE=ACTIVE"
assert_token "[SUP ] CHILD_PID="
assert_token "[SUP ] CHILD_EXIT="
assert_token "[SUP ] EXPECTED_EXIT="
assert_token "[SUP ] WORK_COMPLETED="
assert_token "[SUP ] RESTART_PID="
assert_token "[SUP ] REAPED="
assert_token "[SUP ] ZOMBIES="
assert_token "[SUP ] EXITED="
assert_token "[SUP ] PROCESSES="
assert_token "[SUP ] RESTARTS="
assert_token "[SUP ] SELFTEST PASS"

pid1_task="$(field '[SUP ] PID1_TASK=')"
child_pid="$(field '[SUP ] CHILD_PID=')"
child_exit="$(field '[SUP ] CHILD_EXIT=')"
expected_exit="$(field '[SUP ] EXPECTED_EXIT=')"
work_completed="$(field '[SUP ] WORK_COMPLETED=')"
service_pid="$(field '[SUP ] SERVICE_PID=')"
service_exit="$(field '[SUP ] SERVICE_EXIT=')"
service_expected="$(field '[SUP ] SERVICE_EXPECTED=')"
restart_pid="$(field '[SUP ] RESTART_PID=')"
reaped="$(field '[SUP ] REAPED=')"
zombies="$(field '[SUP ] ZOMBIES=')"
exited="$(field '[SUP ] EXITED=')"
processes="$(field '[SUP ] PROCESSES=')"
restarts="$(field '[SUP ] RESTARTS=')"
notifications="$(field '[SUP ] NOTIFICATIONS=')"
dispatches="$(field '[SUP ] DISPATCHES=')"

[[ "$pid1_task" -gt 0 ]] || fail "PID 1 is not a real scheduler task: $pid1_task"
# The kernel allocates child pids sequentially; this gate never assumes 2.
[[ "$child_pid" -gt 1 ]] || fail "child pid was not kernel-allocated: $child_pid"
[[ "$service_pid" -gt "$child_pid" ]] || fail "service pid did not advance: $service_pid"
[[ "$restart_pid" -gt "$service_pid" ]] || fail "restarted service pid did not advance: $restart_pid"
[[ "$work_completed" -gt 0 ]] || fail "child work did not execute: $work_completed"
[[ "$child_exit" == "$expected_exit" ]] || fail "child exit code mismatch: $child_exit vs $expected_exit"
[[ "$service_exit" == "$service_expected" ]] || fail "service code is not from real work: $service_exit"
[[ "$reaped" -ge 4 ]] || fail "children were not reaped: $reaped"
[[ "$zombies" == "0" ]] || fail "zombies remain after reap: $zombies"
[[ "$exited" == "0" ]] || fail "exited children remain unreaped: $exited"
[[ "$processes" == "1" ]] || fail "PID1 is not the only resident process: $processes"
[[ "$restarts" -ge 2 ]] || fail "restartable service was not restarted: $restarts"
[[ "$notifications" -ge 2 ]] || fail "child exit notifications missing: $notifications"
[[ "$dispatches" -gt 0 ]] || fail "scheduler did not run supervisor tasks: $dispatches"

{
  echo "PASS: Koronos x86_64 kernel-owned PID1 supervisor gate"
  echo "QEMU_EXIT=$qemu_rc"
  echo "ISO_SHA256=$(awk '{print $1}' "$OUT/iso.sha256")"
  echo "PID1_TASK=$pid1_task"
  echo "CHILD_PID=$child_pid"
  echo "CHILD_EXIT=$child_exit"
  echo "EXPECTED_EXIT=$expected_exit"
  echo "WORK_COMPLETED=$work_completed"
  echo "SERVICE_PID=$service_pid"
  echo "SERVICE_EXIT=$service_exit"
  echo "SERVICE_EXPECTED=$service_expected"
  echo "RESTART_PID=$restart_pid"
  echo "REAPED=$reaped"
  echo "ZOMBIES=$zombies"
  echo "EXITED=$exited"
  echo "PROCESSES=$processes"
  echo "RESTARTS=$restarts"
  echo "NOTIFICATIONS=$notifications"
  echo "DISPATCHES=$dispatches"
} | tee "$RESULT"

echo "PASS: kernel-owned supervisor evidence written to $RESULT"
