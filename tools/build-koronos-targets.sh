#!/usr/bin/env bash
# Build real architecture-entry probes for port-layer targets.
# These ELFs prove cross-assembly/linking and an early UART entry only. They
# are not full Koronos kernels and are never staged as production OS kernels.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${KORONOS_PORT_OUT:-$ROOT/build/koronos/ports}"
REQUIRE_ALL=0
RUN_QEMU=1
for arg in "$@"; do
  case "$arg" in
    --require-all) REQUIRE_ALL=1 ;;
    --no-qemu) RUN_QEMU=0 ;;
    --help|-h)
      cat <<'HELP'
Usage: tools/build-koronos-targets.sh [--require-all] [--no-qemu]
Builds x86-32, AArch64 and RV64 architecture bring-up probes.
--require-all  Fail if any requested cross compiler or QEMU runner is absent.
--no-qemu      Build/link/ELF-check only; do not run QEMU probes.
These probes are not production Koronos kernel ports.
HELP
      exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done
mkdir -p "$OUT"
failures=()
built=()
probe() {
  local arch="$1" cc="$2" flags="$3" machine="$4" source="$5" entry="$6" linker="$7" qemu="$8" qemu_args="$9" marker="${10}"
  local dest="$OUT/$arch" log="$OUT/$arch.qemu.log" output rc
  if ! command -v "$cc" >/dev/null 2>&1; then
    echo "MISSING-COMPILER $arch: $cc"
    failures+=("$arch:missing-compiler:$cc")
    return 0
  fi
  mkdir -p "$dest"
  # shellcheck disable=SC2086
  "$cc" $flags -ffreestanding -fno-builtin -fno-stack-protector -fno-pic -fno-pie \
    -nostdlib -Wl,--build-id=none -Wl,-T,"$ROOT/$linker" \
    "$ROOT/$entry" "$ROOT/$source" -o "$dest/koronos-$arch-probe.elf"
  local hdr
  hdr="$(readelf -h "$dest/koronos-$arch-probe.elf")"
  grep -Fq "$machine" <<<"$hdr" || { echo "ELF machine mismatch for $arch"; failures+=("$arch:elf-machine-mismatch"); return 0; }
  nm "$dest/koronos-$arch-probe.elf" | grep -Eq '[[:space:]]_start$'
  nm "$dest/koronos-$arch-probe.elf" | grep -Eq '[[:space:]]koronos_boot$'
  sha256sum "$dest/koronos-$arch-probe.elf" > "$dest/SHA256SUMS"
  echo "ELF-VALIDATED $arch: $dest/koronos-$arch-probe.elf"
  built+=("$arch")
  if (( RUN_QEMU )); then
    if command -v "$qemu" >/dev/null 2>&1; then
      # QEMU is expected to run indefinitely in the probe's WFI loop. A timeout
      # is success only when the architecture-specific UART marker was printed.
      set +e
      timeout 5s "$qemu" $qemu_args -kernel "$dest/koronos-$arch-probe.elf" >"$log" 2>&1
      rc=$?
      set -e
      if grep -Fq "$marker" "$log"; then
        echo "QEMU-UART-PASS $arch"
      else
        echo "QEMU-UART-FAIL $arch (exit=$rc); see $log"
        failures+=("$arch:qemu-uart-marker-missing")
      fi
    else
      echo "MISSING-QEMU $arch: $qemu"
      failures+=("$arch:missing-qemu:$qemu")
    fi
  fi
}
probe aarch64 "${AARCH64_CC:-aarch64-linux-gnu-gcc}" "-march=armv8-a" "AArch64" \
  kernel/arch/aarch64/boot_probe.c kernel/arch/aarch64/entry.S kernel/arch/aarch64/koronos.ld \
  "${QEMU_AARCH64:-qemu-system-aarch64}" "-machine virt -cpu cortex-a57 -display none -monitor none -serial stdio" "KORONOS_AARCH64_ENTRY_OK"
probe riscv64 "${RISCV64_CC:-riscv64-linux-gnu-gcc}" "-march=rv64gc -mabi=lp64d -mcmodel=medany -msmall-data-limit=0" "RISC-V" \
  kernel/arch/riscv64/boot_probe.c kernel/arch/riscv64/entry.S kernel/arch/riscv64/koronos.ld \
  "${QEMU_RISCV64:-qemu-system-riscv64}" "-machine virt -bios default -display none -monitor none -serial stdio" "KORONOS_RISCV64_ENTRY_OK"
if command -v "${X86_32_MAKE:-make}" >/dev/null 2>&1 && command -v "${X86_32_CC:-gcc}" >/dev/null 2>&1; then
  make -C "$ROOT/kernel/arch/x86_32" BUILD="$OUT/x86_32" CC="${X86_32_CC:-gcc}" all check
  built+=("x86_32-probe")
else
  echo "MISSING-COMPILER x86_32: gcc -m32"
  failures+=("x86_32:missing-multilib-compiler")
fi
python3 - "$OUT/manifest.json" "$REQUIRE_ALL" "$RUN_QEMU" "${built[*]}" "${failures[*]}" <<'PY'
import json,sys
path,required,qemu,built,failures=sys.argv[1:]
result={
 "schema":"KORONOS-ARCH-PORT-PROBES-1",
 "purpose":"Architecture-entry/link/UART bring-up probes only; not complete Koronos kernel ports.",
 "built_probes":built.split(),
 "failures":failures.split(),
 "runtime_validation":"qemu-uart-marker-required" if qemu=="1" else "not-run",
 "production_status":{"x86_64":"implemented-kernel-target","aarch64":"port-layer-not-production-kernel","riscv64":"port-layer-not-production-kernel","x86_32":"serial-probe-only"},
 "acceptance":"pass" if not failures else "incomplete"
}
open(path,"w",encoding="utf-8").write(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
if required=="1" and failures: raise SystemExit(1)
PY
if (( REQUIRE_ALL )) && (( ${#failures[@]} )); then
  printf 'Architecture probe matrix incomplete: %s\n' "${failures[*]}" >&2
  exit 1
fi
