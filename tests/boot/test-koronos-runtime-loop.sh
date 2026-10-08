#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
K="$ROOT/kernel/core/koronos.cpp"
R="$ROOT/kernel/core/runtime.cpp"
B="$ROOT/kernel/build-koronos.sh"

grep -q 'koronos_idle_loop' "$R"
grep -q 'chimera_sched_run_parallel(0, 1)' "$R"
grep -q 'chimera_timer_tick(1)' "$R"
grep -q 'chimera_watchdog_heartbeat(CHIMERA_WATCHDOG_KORONOS' "$R"
grep -q 'chimera_watchdog_heartbeat(CHIMERA_WATCHDOG_MICROKERNEL' "$R"
grep -q 'chimera_sched_block();' "$K"
grep -q 'chimera_watchdog_register(CHIMERA_WATCHDOG_KORONOS' "$K"
grep -q 'chimera_watchdog_register(CHIMERA_WATCHDOG_MICROKERNEL' "$K"
grep -q 'chimera_watchdog_register(CHIMERA_WATCHDOG_KORE' "$K"
grep -q 'koronos_idle_loop' "$B"

if grep -nF '\\n    if' "$K"; then
  echo "ERROR: literal newline escape leaked into Koronos C++ source" >&2
  exit 1
fi

echo "Koronos runtime-loop regression: PASS"
