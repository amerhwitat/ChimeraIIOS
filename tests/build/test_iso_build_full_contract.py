#!/usr/bin/env python3
"""Guard the full ISO builder's fail-closed and non-destructive contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
build = (ROOT / "build-chimera-iso.sh").read_text(encoding="utf-8")
sdk = (ROOT / "tools/build-sdks.sh").read_text(encoding="utf-8")

assert 'CHIMERA_PUSH="${CHIMERA_PUSH:-0}"' in build
assert '    --full) FULL_BUILD=1; CLEAN_STATE=1; RESUME_BUILD=0; shift;;' in build
assert '[[ "$FULL_BUILD" == 1 ]] && build_opts+=(--no-cache)' in build
assert 'docker container prune -f' not in build
assert 'bash "$SCRIPT_DIR/tools/build-sdks.sh" --strict --out "$report"' in build
assert 'if [[ "$FULL_BUILD" == 1 ]]; then' in build
assert '--strict) STRICT=1; shift ;;' in sdk
assert 'STRICT SDK PASS:' in sdk
assert 'problems = {key:' in sdk
print("PASS: full build is opt-in, no-cache, no implicit publish, no global container prune, and strict on SDK failures/skips.")
