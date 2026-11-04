#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 -m unittest discover -s "$ROOT/tests/system" -p 'test_*.py' -v
python3 -m unittest discover -s "$ROOT/tests/services" -p 'test_*.py' -v
