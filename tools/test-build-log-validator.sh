#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATOR="$ROOT/tools/validate_build_log.py"
TEST_DIR="$ROOT/tests/architecture"

if [[ ! -f "$VALIDATOR" || ! -f "$TEST_DIR/test_build_validation_log.py" ]]; then
  echo "ERROR: this checkout does not contain the build-log validator and its tests." >&2
  echo "Fetch and switch to the remediation branch, then retry:" >&2
  echo "  git fetch origin" >&2
  echo "  git switch fix/uefi-native-syscall-ack-20261024" >&2
  echo "  git pull --ff-only origin fix/uefi-native-syscall-ack-20261024" >&2
  exit 2
fi

python3 -m unittest discover -s "$TEST_DIR" -p 'test_build_validation_log.py' -v
python3 "$VALIDATOR" --help >/dev/null
printf 'PASS: build-log validator unit tests and CLI entry point are available.\n'

if [[ $# -gt 0 ]]; then
  LOG="$1"
  shift
  python3 "$VALIDATOR" "$LOG" "$@"
fi
