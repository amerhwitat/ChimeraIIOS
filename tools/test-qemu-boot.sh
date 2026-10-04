#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ISO="${1:-$ROOT/ChimeraIIOS-comprehensive-1.0.0.iso}"
RAM="${CHIMERA_QEMU_RAM:-4096}"
SMP="${CHIMERA_QEMU_SMP:-1}"
ACCEL="${CHIMERA_QEMU_ACCEL:-tcg}"

[[ -r "$ISO" ]] || { echo "[ERROR] ISO not found: $ISO" >&2; exit 2; }
command -v qemu-system-x86_64 >/dev/null || { echo "[ERROR] qemu-system-x86_64 is required" >&2; exit 2; }

# WHPX exit code 4 is a known Windows Hypervisor Platform/APIC failure mode.
# Use TCG by default for a deterministic Chimera kernel smoke test.
if [[ "${OS:-}" == "Windows_NT" || "$(uname -a 2>/dev/null)" == *Microsoft* ]]; then
  if [[ "${CHIMERA_QEMU_ACCEL+x}" != x ]]; then ACCEL=tcg; fi
fi

case "$ACCEL" in
  tcg)
    ACCEL_ARGS=(-accel tcg,thread=multi)
    ;;
  whpx)
    ACCEL_ARGS=(-accel whpx)
    ;;
  none)
    ACCEL_ARGS=()
    ;;
  *)
    echo "[ERROR] Unsupported CHIMERA_QEMU_ACCEL=$ACCEL (use tcg, whpx, or none)" >&2
    exit 2
    ;;
esac

echo "[INFO] QEMU smoke test: RAM=$RAM MiB SMP=$SMP accelerator=$ACCEL"
echo "[INFO] SMP defaults to 1 because WHPX/APIC exit-code-4 failures are host-side accelerator failures."

set +e
qemu-system-x86_64 \
  -machine pc \
  -m "$RAM" \
  -smp "$SMP" \
  "${ACCEL_ARGS[@]}" \
  -cpu qemu64 \
  -nodefaults \
  -display gtk,show-cursor=on \
  -device VGA \
  -serial stdio \
  -no-reboot \
  -no-shutdown \
  -cdrom "$ISO"
rc=$?
set -e

if [[ "$rc" -eq 4 && "$ACCEL" == whpx ]]; then
  echo "[ERROR] QEMU WHPX returned exit code 4." >&2
  echo "[ERROR] This is a WHPX/Hyper-V accelerator failure, not proof that Koronos crashed." >&2
  echo "[HINT] Re-run with: CHIMERA_QEMU_ACCEL=tcg CHIMERA_QEMU_SMP=1 $0 \"$ISO\"" >&2
fi

exit "$rc"
