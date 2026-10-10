#!/usr/bin/env bash
set -Eeuo pipefail

# Fail-closed Koronos ELF/SMP acceptance test.
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
ISO="${CHIMERA_ISO:-${1:-}}"
OUT="${CHIMERA_QEMU_LOG:-$ROOT/build/koronos-elf-smp-qemu.log}"
QEMU="${QEMU_SYSTEM_X86_64:-qemu-system-x86_64}"
TIMEOUT_SECS="${CHIMERA_QEMU_TIMEOUT:-90}"
CPUS="${CHIMERA_QEMU_CPUS:-4}"
MEMORY="${CHIMERA_QEMU_MEMORY:-2048}"

fail() { printf '[FAIL] %s\n' "$*" >&2; exit 1; }
command -v "$QEMU" >/dev/null 2>&1 || fail "qemu executable not found: $QEMU"
command -v timeout >/dev/null 2>&1 || fail "timeout command is required"
[[ -n "$ISO" && -f "$ISO" ]] || fail "set CHIMERA_ISO to a rebuilt ISO file"
[[ "$CPUS" =~ ^[2-9][0-9]*$|^[2-9]$ ]] || fail "CHIMERA_QEMU_CPUS must be an integer >= 2"
mkdir -p "$(dirname -- "$OUT")"
rm -f -- "$OUT"

printf '[INFO] Booting %s with %s vCPUs for up to %ss\n' "$ISO" "$CPUS" "$TIMEOUT_SECS"
set +e
timeout --signal=TERM --kill-after=5 "$TIMEOUT_SECS" \
  "$QEMU" -machine q35,accel=tcg -cpu max -smp "$CPUS" -m "$MEMORY" \
  -cdrom "$ISO" -boot d -display none -serial "file:$OUT" \
  -monitor none -no-reboot -no-shutdown
qemu_rc=$?
set -e
printf '[INFO] QEMU exit=%s; serial log=%s\n' "$qemu_rc" "$OUT"

grep -Fq 'ELF_USERSPACE: entry reached' "$OUT" || fail "no proof of actual userspace entry (ring-3 marker missing)"
grep -Fq 'ELF_TEST: bss=zero stack=valid permissions=valid' "$OUT" || fail "ELF runtime validation marker missing"

mapfile -t online_cpus < <(sed -nE 's/.*SMP: cpu online id=([0-9]+).*/\1/p' "$OUT" | sort -nu)
(("${#online_cpus[@]}" >= 2)) || fail "fewer than two distinct CPU-online markers observed"
nonzero_online="$(printf '%s\n' "${online_cpus[@]}" | awk '$1 != 0 {n++} END {print n+0}')"
(( nonzero_online >= 1 )) || fail "no non-BSP CPU was observed online"

mapfile -t progress_cpus < <(sed -nE 's/.*SCHED: task progress cpu=([0-9]+).*/\1/p' "$OUT" | sort -nu)
(("${#progress_cpus[@]}" >= 2)) || fail "scheduled task progress was not observed on at least two CPUs"

printf '[PASS] userspace entry, ELF mapping checks, and task progress on CPUs: %s\n' "${progress_cpus[*]}"
