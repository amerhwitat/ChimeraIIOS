#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE="$ROOT"
if [[ -d "$ROOT/vendor/chimera-ii-os/source" ]]; then
  SOURCE="$ROOT/vendor/chimera-ii-os/source"
fi
LOG_DIR="$SOURCE/build/logs/release-gate"
MATRIX_DIR="$SOURCE/build/qemu-smoke/production-matrix"
mkdir -p "$LOG_DIR"

fail() { echo "RELEASE BLOCKED: $*" >&2; exit 1; }
echo "[GATE] Production release acceptance (fail closed)"
echo "[GATE] Repository: $ROOT"
echo "[GATE] Kernel source: $SOURCE"

# Build through the repository's canonical ISO pipeline; never synthesize
# initramfs files or use kernel/tests smoke images as production payloads.
bash "$SOURCE/boot/iso/build-iso.sh" 2>&1 | tee "$LOG_DIR/iso-build.log"

for target in live installer recovery; do
  payload="$SOURCE/build/koronos/userspace/${target}-init.elf"
  [[ -s "$payload" ]] || fail "missing production init ELF: $payload"
done
python3 "$SOURCE/tools/boot/validate_production_init.py" 2>&1 | tee "$LOG_DIR/elf-validation.log"

# The matrix runs six fresh ISO boots and records independent serial/debugcon
# traces. A QEMU timeout/exit code is not acceptance evidence.
bash "$ROOT/tools/boot/run_six_case_production_matrix.sh" 2>&1 | tee "$LOG_DIR/matrix.log"

for target in live installer recovery; do
  for firmware in bios uefi; do
    trace="$MATRIX_DIR/${target}-${firmware}.log"
    [[ -s "$trace" ]] || fail "missing boot trace: $trace"
    grep -Fq '[KRN ] KORONOS READY' "$trace" || fail "$target/$firmware did not prove kernel readiness"
    grep -Fq 'USERSPACE SYSCALL RETURNED TO RING3' "$trace" || fail "$target/$firmware did not prove syscall return to ring 3"
    python3 - "$trace" "$target" <<'PY'
import pathlib, re, sys
path, target = pathlib.Path(sys.argv[1]), sys.argv[2]
text = path.read_text(errors="replace")
syscalls = re.findall(r"USER INIT SYSCALL: target=(live|installer|recovery) init_pid=([1-9][0-9]*)", text)
ready = re.findall(r"USERSPACE READY: target=(live|installer|recovery) init_pid=([1-9][0-9]*)", text)
if not any(t == target and pid for t, pid in syscalls):
    raise SystemExit(f"FAIL: {path}: no target-matched nonzero CPL3 syscall acknowledgement")
if not any(t == target and any(rt == t and rp == pid for rt, rp in ready) for t, pid in syscalls):
    raise SystemExit(f"FAIL: {path}: no readiness marker matching the syscall PID")
PY
  done
done

# Process startup is not equivalent to the user-facing OS being functional.
# These separately generated evidence files must come from real integration
# tests, not static manifests or hand-authored PASS values.
for evidence in \
  "$SOURCE/build/evidence/live-aurora-functional.json" \
  "$SOURCE/build/evidence/installer-reboot-functional.json" \
  "$SOURCE/build/evidence/recovery-operation-functional.json" \
  "$SOURCE/build/evidence/ap-backed-smp-functional.json"; do
  [[ -s "$evidence" ]] || fail "missing independent functional evidence: $evidence"
  python3 "$ROOT/tools/ci/validate_functional_evidence.py" "$evidence" || fail "invalid functional evidence: $evidence"
done

echo "[GATE] PASS: all production runtime and functional acceptance criteria verified"
