#!/usr/bin/env bash
set -Eeuo pipefail

script="build-chimera-iso.sh"
test -s "$script"

# The supported target must fail closed before any architecture-specific ISO is
# produced when the current boot pipeline cannot serve that target.
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
set +e
CHIMERA_TARGET_ARCH=aarch64 CHIMERA_BUILD_DIR="$tmp/build" CHIMERA_ISO_OUTPUT_DIR="$tmp/out" bash "$script" --no-push >"$tmp/arm.log" 2>&1
arm_rc=$?
set -e
[[ "$arm_rc" -eq 2 ]] || { cat "$tmp/arm.log"; echo "Expected aarch64 target to fail with status 2; got $arm_rc" >&2; exit 1; }
grep -q 'current ISO boot pipeline supports x86_64 only' "$tmp/arm.log"
[[ ! -e "$tmp/out/ChimeraIIOS-comprehensive-1.0.0-aarch64.iso" ]]

# Both the build and verify stages must use the same architecture-suffixed path.
python3 - <<'PY'
from pathlib import Path
s = Path("build-chimera-iso.sh").read_text()
expected = '"$ISO_OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}-${TARGET_ARCH}.iso"'
assert s.count(expected) >= 2, "build_iso and verify_iso must use architecture-suffixed ISO paths"
assert 'CHIMERA_MEDIA_FS_PROFILE' in s and 'iso9660+squashfs' in s
assert 'CHIMERA_BUILD_VERBOSE="${CHIMERA_BUILD_VERBOSE:-1}"' in s, "verbose diagnostics must be enabled by default"
assert '--verbose)' in s and '--quiet)' in s, "verbose and quiet CLI controls must exist"
assert 'log_stage_diagnostics' in s and "completed successfully in" in s, "stage diagnostics and elapsed timing are required"
assert 'date -u +%Y-%m-%dT%H:%M:%SZ' in s, "diagnostics must use UTC timestamps"
assert 'process-snapshots.log' in s and 'chimera-build.log' in s, "diagnostic log destinations must be reported"
print("CPU-aware ISO selection contract: PASS")
PY
