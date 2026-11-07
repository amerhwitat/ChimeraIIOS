#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$(realpath -m "${1:-$ROOT/build/native-command-isa}")"
declare -A EMULATORS=(
  [x86_64]=""
  [i686]="qemu-i386-static"
  [armel]="qemu-arm-static"
  [aarch64]="qemu-aarch64-static"
  [armv7]="qemu-arm-static"
  [riscv64]="qemu-riscv64-static"
  [ppc64le]="qemu-ppc64le-static"
  [s390x]="qemu-s390x-static"
)
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for arch in x86_64 i686 armel aarch64 armv7 riscv64 ppc64le s390x; do
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
  alias="$tmp/$arch-touch"; ln -sf "$bin" "$alias"
  run "$alias" "$tmp/touched-$arch"
  [[ -f "$tmp/touched-$arch" ]] || { echo "$arch touch failed" >&2; exit 1; }
  printf 'copy-source\n' > "$tmp/copy-source-$arch"
  alias="$tmp/$arch-cp"; ln -sf "$bin" "$alias"
  run "$alias" "$tmp/copy-source-$arch" "$tmp/copy-target-$arch"
  cmp -s "$tmp/copy-source-$arch" "$tmp/copy-target-$arch" || { echo "$arch cp failed" >&2; exit 1; }
  alias="$tmp/$arch-cat"; ln -sf "$bin" "$alias"
  output="$(run "$alias" "$tmp/copy-target-$arch")"
  [[ "$output" == "copy-source" ]] || { echo "$arch cat failed: $output" >&2; exit 1; }
  alias="$tmp/$arch-mv"; ln -sf "$bin" "$alias"
  run "$alias" "$tmp/copy-target-$arch" "$tmp/moved-$arch"
  [[ -f "$tmp/moved-$arch" && ! -e "$tmp/copy-target-$arch" ]] || { echo "$arch mv failed" >&2; exit 1; }
  alias="$tmp/$arch-mkdir"; ln -sf "$bin" "$alias"
  run "$alias" "$tmp/made-dir-$arch"
  [[ -d "$tmp/made-dir-$arch" ]] || { echo "$arch mkdir failed" >&2; exit 1; }
  alias="$tmp/$arch-rm"; ln -sf "$bin" "$alias"
  run "$alias" "$tmp/moved-$arch"
  [[ ! -e "$tmp/moved-$arch" ]] || { echo "$arch rm failed" >&2; exit 1; }
  alias="$tmp/$arch-whoami"; ln -sf "$bin" "$alias"
  output="$(run "$alias")"; [[ -n "$output" ]] || { echo "$arch whoami failed" >&2; exit 1; }
  alias="$tmp/$arch-hostname"; ln -sf "$bin" "$alias"
  output="$(run "$alias")"; [[ -n "$output" ]] || { echo "$arch hostname failed" >&2; exit 1; }
  alias="$tmp/$arch-date"; ln -sf "$bin" "$alias"
  output="$(run "$alias")"; [[ -n "$output" ]] || { echo "$arch date failed" >&2; exit 1; }
  alias="$tmp/$arch-clear"; ln -sf "$bin" "$alias"; run "$alias" >/dev/null
  printf 'line-one\nline-two\nline-three\n' > "$tmp/input-$arch"
  alias="$tmp/$arch-head"; ln -sf "$bin" "$alias"
  output="$(run "$alias" -n 1 "$tmp/input-$arch")"
  [[ "$output" == "line-one" ]] || { echo "$arch head failed: $output" >&2; exit 1; }
  alias="$tmp/$arch-tail"; ln -sf "$bin" "$alias"
  output="$(run "$alias" -n 1 "$tmp/input-$arch")"
  [[ "$output" == "line-three" ]] || { echo "$arch tail failed: $output" >&2; exit 1; }
  alias="$tmp/$arch-wc"; ln -sf "$bin" "$alias"
  output="$(run "$alias" -l "$tmp/input-$arch")"
  [[ "$output" == *"3"* ]] || { echo "$arch wc failed: $output" >&2; exit 1; }
  alias="$tmp/$arch-basename"; ln -sf "$bin" "$alias"
  output="$(run "$alias" /var/tmp/sample.txt)"
  [[ "$output" == "sample.txt" ]] || { echo "$arch basename failed: $output" >&2; exit 1; }
  alias="$tmp/$arch-dirname"; ln -sf "$bin" "$alias"
  output="$(run "$alias" /var/tmp/sample.txt)"
  [[ "$output" == "/var/tmp" ]] || { echo "$arch dirname failed: $output" >&2; exit 1; }
  alias="$tmp/$arch-uname"; ln -sf "$bin" "$alias"
  output="$(run "$alias" -s)"
  [[ -n "$output" ]] || { echo "$arch uname failed" >&2; exit 1; }
  alias="$tmp/$arch-ln"; ln -sf "$bin" "$alias"
  run "$alias" -s "$tmp/input-$arch" "$tmp/link-$arch"
  alias="$tmp/$arch-readlink"; ln -sf "$bin" "$alias"
  output="$(run "$alias" "$tmp/link-$arch")"
  [[ "$output" == "$tmp/input-$arch" ]] || { echo "$arch readlink failed: $output" >&2; exit 1; }
  mkdir "$tmp/rmdir-$arch"
  alias="$tmp/$arch-rmdir"; ln -sf "$bin" "$alias"
  run "$alias" "$tmp/rmdir-$arch"
  [[ ! -e "$tmp/rmdir-$arch" ]] || { echo "$arch rmdir failed" >&2; exit 1; }
  alias="$tmp/$arch-sleep"; ln -sf "$bin" "$alias"; run "$alias" 0.001
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
