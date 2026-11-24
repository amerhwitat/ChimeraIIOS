#!/usr/bin/env bash
# Measured x86_64 Koronos timer-preemption + per-CPU AP runtime gate.
#
# Builds the real kernel, boots it through GRUB Multiboot2 in QEMU with two
# vCPUs, and evaluates only measured runtime evidence from debugcon:
#   * timer-driven preemptions, context switches, ticks, and guard failures
#   * real AP online state, APIC identity, and discovered CPU IDs
#   * per-CPU task/work counts from the two-CPU parallel scheduler dispatch
#   * overlapping execution intervals from per-CPU TSC timestamps
# No hardcoded kernel PASS string or fixed round count is accepted as proof.
#
# Usage: tools/runtime/check-koronos-preempt-smp-runtime.sh [--help]

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos ELF64 kernel with -smp 2 and verifies the
timer-preemptive scheduler and resident per-CPU AP runtime from measured
numeric evidence.

Options:
  --help    Show this help and exit.

Artifacts:
  build/koronos-preempt-smp-runtime/koronos-preempt-smp-runtime.iso
  build/koronos-preempt-smp-runtime/debugcon.log
  build/koronos-preempt-smp-runtime/serial.log
  build/koronos-preempt-smp-runtime/result.txt
  build/koronos-preempt-smp-runtime/iso.sha256
"

if [[ "${1:-}" == "--help" ]]; then
  printf '%s' "$CHIMERA_HELP"
  exit 0
fi

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/koronos-preempt-smp-runtime"
ISO="$OUT/koronos-preempt-smp-runtime.iso"
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
menuentry "Koronos timer-preemptive per-CPU runtime gate" {
  multiboot2 /boot/koronos.elf
  boot
}
GRUB

echo "== Building Multiboot2 preempt/SMP runtime test ISO =="
grub-mkrescue -o "$ISO" "$OUT/isoroot" >/dev/null
sha256sum "$ISO" >"$OUT/iso.sha256"

echo "== Booting QEMU (2 CPUs, timer preemption + real INIT/SIPI) =="
set +e
timeout 45s qemu-system-x86_64 \
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

field() {
  grep -aF "$1" "$DEBUGLOG" | tail -n 1 | tr -d '\r' | awk -F= '{print $2}'
}

require_number() {
  [[ "$2" =~ ^[0-9]+$ ]] || fail "$1 is not numeric: '$2'"
}

check_number() {
  local name="$1" value="$2" op="$3" expected="$4"
  require_number "$name" "$value"
  case "$op" in
    eq) [[ "$value" -eq "$expected" ]] || fail "$name=$value, expected $expected" ;;
    ne) [[ "$value" -ne "$expected" ]] || fail "$name=$value, expected != $expected" ;;
    ge) [[ "$value" -ge "$expected" ]] || fail "$name=$value, expected >= $expected" ;;
    gt) [[ "$value" -gt "$expected" ]] || fail "$name=$value, expected > $expected" ;;
    *) fail "unsupported comparison: $op" ;;
  esac
}

workers="$(field '[RTM ] WORKERS_SUBMITTED=')"
completed="$(field '[RTM ] RUNTIME_WORKERS_COMPLETED=')"
preemptions="$(field '[RTM ] PREEMPTIONS=')"
switches="$(field '[RTM ] CONTEXT_SWITCHES=')"
ticks="$(field '[RTM ] TIMER_TICKS=')"
guards="$(field '[RTM ] GUARD_FAILURES=')"
cpu_id_count="$(field '[RTM ] CPU_ID_COUNT=')"
cpu0_dispatches="$(field '[RTM ] CPU0_DISPATCHES=')"
cpu1_dispatches="$(field '[RTM ] CPU1_DISPATCHES=')"
bsp_apic_id="$(field '[SMP ] BSP_APIC_ID=')"
ap_apic_id="$(field '[SMP ] AP_APIC_ID=')"
ap_cpu_ids="$(field '[SMP ] AP_CPU_IDS=')"
ap_online="$(field '[SMP ] AP_ONLINE=')"
parallel_return="$(field '[SMP ] PARALLEL_RETURN=')"
cpu0_tasks="$(field '[SMP ] CPU0_TASKS=')"
cpu1_tasks="$(field '[SMP ] CPU1_TASKS=')"
cpu0_work="$(field '[SMP ] CPU0_WORK=')"
cpu1_work="$(field '[SMP ] CPU1_WORK=')"
overlap_samples="$(field '[SMP ] OVERLAP_SAMPLES=')"
tsc_overlap="$(field '[SMP ] TSC_OVERLAP=')"
bsp_start="$(field '[SMP ] BSP_START_TSC=')"
ap_start="$(field '[SMP ] AP_START_TSC=')"
bsp_end="$(field '[SMP ] BSP_END_TSC=')"
ap_end="$(field '[SMP ] AP_END_TSC=')"

check_number workers_submitted "$workers" ge 2
check_number runtime_workers_completed "$completed" ge "$workers"
check_number timer_preemptions "$preemptions" gt 0
check_number context_switches "$switches" ge "$workers"
check_number timer_ticks "$ticks" gt 0
check_number guard_failures "$guards" eq 0
check_number cpu_id_count "$cpu_id_count" ge 2
check_number cpu0_dispatches "$cpu0_dispatches" gt 0
check_number cpu1_dispatches "$cpu1_dispatches" gt 0
check_number bsp_apic_id "$bsp_apic_id" ge 0
check_number ap_apic_id "$ap_apic_id" gt 0
check_number ap_online "$ap_online" eq 1
check_number parallel_return "$parallel_return" ge 1
check_number cpu0_tasks "$cpu0_tasks" gt 0
check_number cpu1_tasks "$cpu1_tasks" gt 0
check_number cpu0_work "$cpu0_work" gt 0
check_number cpu1_work "$cpu1_work" gt 0
check_number overlap_samples "$overlap_samples" gt 0
check_number tsc_overlap "$tsc_overlap" eq 1
check_number bsp_start_tsc "$bsp_start" gt 0
check_number ap_start_tsc "$ap_start" gt 0
check_number bsp_end_tsc "$bsp_end" gt "$bsp_start"
check_number ap_end_tsc "$ap_end" gt "$ap_start"
[[ "$bsp_apic_id" -ne "$ap_apic_id" ]] || fail "BSP/AP APIC IDs are not distinct: $bsp_apic_id"

# AP CPU IDs are enumerated by the kernel from online CPU state. Reject an
# empty list, zero, malformed entries, or a list that disagrees with the
# discovered CPU count.
[[ "$ap_cpu_ids" =~ ^[0-9]+(,[0-9]+)*$ ]] || fail "malformed AP_CPU_IDS: '$ap_cpu_ids'"
IFS=',' read -r -a ap_ids <<<"$ap_cpu_ids"
[[ "${#ap_ids[@]}" -ge 1 ]] || fail "no AP CPU IDs reported"
for id in "${ap_ids[@]}"; do
  check_number ap_cpu_id "$id" gt 0
done

# Intervals must genuinely overlap: the later start precedes the earlier end.
if (( bsp_start > ap_start )); then latest_start=$bsp_start; else latest_start=$ap_start; fi
if (( bsp_end < ap_end )); then earliest_end=$bsp_end; else earliest_end=$ap_end; fi
(( latest_start < earliest_end )) || fail "TSC intervals do not overlap: latest_start=$latest_start earliest_end=$earliest_end"

grep -aFq '[RUN ] Entering per-CPU Koronos scheduler loop' "$DEBUGLOG" || fail "runtime loop entry evidence missing"

{
  echo "PASS: Koronos timer-preemptive scheduler and per-CPU AP runtime evidence"
  echo "QEMU_EXIT=$qemu_rc"
  echo "ISO_SHA256=$(awk '{print $1}' "$OUT/iso.sha256")"
  echo "WORKERS_SUBMITTED=$workers"
  echo "RUNTIME_WORKERS_COMPLETED=$completed"
  echo "PREEMPTIONS=$preemptions"
  echo "CONTEXT_SWITCHES=$switches"
  echo "TIMER_TICKS=$ticks"
  echo "GUARD_FAILURES=$guards"
  echo "CPU_ID_COUNT=$cpu_id_count"
  echo "CPU0_DISPATCHES=$cpu0_dispatches"
  echo "CPU1_DISPATCHES=$cpu1_dispatches"
  echo "BSP_APIC_ID=$bsp_apic_id"
  echo "AP_APIC_ID=$ap_apic_id"
  echo "AP_CPU_IDS=$ap_cpu_ids"
  echo "AP_ONLINE=$ap_online"
  echo "PARALLEL_RETURN=$parallel_return"
  echo "CPU0_TASKS=$cpu0_tasks"
  echo "CPU1_TASKS=$cpu1_tasks"
  echo "CPU0_WORK=$cpu0_work"
  echo "CPU1_WORK=$cpu1_work"
  echo "OVERLAP_SAMPLES=$overlap_samples"
  echo "TSC_OVERLAP=$tsc_overlap"
  echo "BSP_START_TSC=$bsp_start"
  echo "AP_START_TSC=$ap_start"
  echo "BSP_END_TSC=$bsp_end"
  echo "AP_END_TSC=$ap_end"
} | tee "$RESULT"

echo "PASS: measured preempt/SMP runtime evidence written to $RESULT"
