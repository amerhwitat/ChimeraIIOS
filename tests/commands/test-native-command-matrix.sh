#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/build/native-command-isa}"
declare -A EMULATORS=(
  [x86_64]=""
  [i686]="qemu-i386-static"
  [aarch64]="qemu-aarch64-static"
  [armv7]="qemu-arm-static"
  [riscv64]="qemu-riscv64-static"
  [ppc64le]="qemu-ppc64le-static"
  [s390x]="qemu-s390x-static"
)
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for arch in x86_64 i686 aarch64 armv7 riscv64 ppc64le s390x; do
  bin="$OUT/$arch/chimera-cmd"
  [[ -s "$bin" ]] || { echo "missing binary for $arch" >&2; exit 2; }
  emulator="${EMULATORS[$arch]}"
  if [[ -n "$emulator" ]]; then command -v "$emulator" >/dev/null || { echo "missing $emulator" >&2; exit 2; }; fi
  run() { if [[ -n "$emulator" ]]; then "$emulator" "$@"; else "$@"; fi; }
  alias="$tmp/$arch-echo"
  ln -sf "$bin" "$alias"
  output="$(run "$alias" "chimera-$arch")"
  [[ "$output" == "chimera-$arch" ]] || { echo "$arch echo mismatch: $output" >&2; exit 1; }
  alias="$tmp/$arch-pwd"
  ln -sf "$bin" "$alias"
  output="$(run "$alias")"
  [[ -n "$output" && "$output" == /* ]] || { echo "$arch pwd failed: $output" >&2; exit 1; }
  alias="$tmp/$arch-true"; ln -sf "$bin" "$alias"; run "$alias"
  alias="$tmp/$arch-false"; ln -sf "$bin" "$alias"
  if run "$alias"; then echo "$arch false returned success" >&2; exit 1; fi
  printf 'PASS %s Linux userspace command ABI smoke tests\n' "$arch"
done
python3 - "$OUT/manifest.json" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); data=json.loads(p.read_text())
for row in data["targets"]:
    row["runtime_status"]="qemu-user-linux-abi-smoke-tested" if row["target"]!="x86_64" else "native-linux-abi-smoke-tested"
data["runtime_scope"]="Linux userspace under native execution/QEMU user mode; this does not validate Koronos syscalls or kernel boot."
p.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
print("Updated manifest with Linux ABI smoke-test evidence; Koronos remains untested.")
PY
