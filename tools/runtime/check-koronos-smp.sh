#!/usr/bin/env bash
# Native x86_64 Koronos AP/SMP gate.
#
# Boots the real kernel with two vCPUs, sends real x2APIC INIT/SIPI from the
# BSP, and requires measured AP online state, distinct APIC identities, real
# per-CPU task/work counts, and overlapping TSC intervals. The measured
# timer-preemption evidence must be present in the same boot trace.
#
# Usage: tools/runtime/check-koronos-smp.sh [--help]

CHIMERA_HELP="Usage: $(basename "$0") [--help]

Builds and boots the native Koronos ELF64 kernel with -smp 2 and verifies the
real-AP startup/two-CPU overlap runtime from measured evidence.

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
menuentry "Koronos native AP/SMP gate" {
  multiboot2 /boot/koronos.elf
  boot
}
GRUB

echo "== Building Multiboot2 AP/SMP test ISO =="
grub-mkrescue -o "$ISO" "$OUT/isoroot" >/dev/null
sha256sum "$ISO" >"$OUT/iso.sha256"

echo "== Booting QEMU (2 CPUs, real INIT/SIPI) =="
set +e
timeout 180s qemu-system-x86_64 \
  -machine pc -cpu max -smp 2 -m 256M \
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

preemptions="$(field '[RTM ] PREEMPTIONS=')"
switches="$(field '[RTM ] CONTEXT_SWITCHES=')"
guards="$(field '[RTM ] GUARD_FAILURES=')"
bsp_id="$(field '[SMP ] BSP_APIC_ID=')"
ap_id="$(field '[SMP ] AP_APIC_ID=')"
ap_ids="$(field '[SMP ] AP_CPU_IDS=')"
online="$(field '[SMP ] AP_ONLINE=')"
parallel="$(field '[SMP ] PARALLEL_RETURN=')"
cpu0_tasks="$(field '[SMP ] CPU0_TASKS=')"
cpu1_tasks="$(field '[SMP ] CPU1_TASKS=')"
cpu0_work="$(field '[SMP ] CPU0_WORK=')"
cpu1_work="$(field '[SMP ] CPU1_WORK=')"
overlap="$(field '[SMP ] OVERLAP_SAMPLES=')"
tsc_overlap="$(field '[SMP ] TSC_OVERLAP=')"
bsp_start="$(field '[SMP ] BSP_START_TSC=')"
ap_start="$(field '[SMP ] AP_START_TSC=')"
bsp_end="$(field '[SMP ] BSP_END_TSC=')"
ap_end="$(field '[SMP ] AP_END_TSC=')"

number preemptions "$preemptions"
number switches "$switches"
number guard_failures "$guards"
number bsp_apic_id "$bsp_id"
number ap_apic_id "$ap_id"
number ap_online "$online"
number parallel_return "$parallel"
number cpu0_tasks "$cpu0_tasks"
number cpu1_tasks "$cpu1_tasks"
number cpu0_work "$cpu0_work"
number cpu1_work "$cpu1_work"
number overlap_samples "$overlap"
number tsc_overlap "$tsc_overlap"
number bsp_start_tsc "$bsp_start"
number ap_start_tsc "$ap_start"
number bsp_end_tsc "$bsp_end"
number ap_end_tsc "$ap_end"

[[ "$preemptions" -gt 0 ]] || fail "timer preemptions=$preemptions, expected >0"
[[ "$switches" -gt 0 ]] || fail "context switches=$switches, expected >0"
[[ "$guards" -eq 0 ]] || fail "guard failures=$guards"
[[ "$online" -eq 1 ]] || fail "AP online=$online, expected 1"
[[ "$bsp_id" -ne "$ap_id" ]] || fail "BSP/AP APIC IDs are not distinct: bsp=$bsp_id ap=$ap_id"
[[ "$parallel" -ge 1 ]] || fail "parallel return=$parallel, expected >=1"
[[ "$cpu0_tasks" -gt 0 && "$cpu1_tasks" -gt 0 ]] || fail "per-CPU tasks missing: cpu0=$cpu0_tasks cpu1=$cpu1_tasks"
[[ "$cpu0_work" -gt 0 && "$cpu1_work" -gt 0 ]] || fail "per-CPU work missing: cpu0=$cpu0_work cpu1=$cpu1_work"
[[ "$overlap" -gt 0 ]] || fail "overlap samples=$overlap, expected >0"
[[ "$tsc_overlap" -eq 1 ]] || fail "TSC overlap flag=$tsc_overlap, expected 1"
[[ "$ap_ids" =~ ^[0-9]+(,[0-9]+)*$ ]] || fail "malformed AP_CPU_IDS: '$ap_ids'"
IFS=',' read -r -a ids <<<"$ap_ids"
[[ "${#ids[@]}" -ge 1 ]] || fail "no AP CPU IDs reported"
for id in "${ids[@]}"; do
  number ap_cpu_id "$id"
  [[ "$id" -gt 0 ]] || fail "AP CPU ID zero is invalid"
done
if (( bsp_start > ap_start )); then latest=$bsp_start; else latest=$ap_start; fi
if (( bsp_end < ap_end )); then earliest=$bsp_end; else earliest=$ap_end; fi
(( latest < earliest )) || fail "TSC intervals do not overlap: latest=$latest earliest=$earliest"

{
  echo "PASS: Koronos x86_64 measured AP startup/two-CPU overlap gate"
  echo "QEMU_EXIT=$qemu_rc"
  echo "ISO_SHA256=$(awk '{print $1}' "$OUT/iso.sha256")"
  echo "BSP_APIC_ID=$bsp_id"
  echo "AP_APIC_ID=$ap_id"
  echo "AP_CPU_IDS=$ap_ids"
  echo "AP_ONLINE=$online"
  echo "PARALLEL_RETURN=$parallel"
  echo "CPU0_TASKS=$cpu0_tasks"
  echo "CPU1_TASKS=$cpu1_tasks"
  echo "CPU0_WORK=$cpu0_work"
  echo "CPU1_WORK=$cpu1_work"
  echo "OVERLAP_SAMPLES=$overlap"
  echo "TSC_OVERLAP=$tsc_overlap"
} | tee "$RESULT"

echo "PASS: measured AP/SMP evidence written to $RESULT"
