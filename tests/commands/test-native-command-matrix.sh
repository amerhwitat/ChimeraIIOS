#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$(realpath -m "${1:-$ROOT/build/linux-abi-command-matrix}")"
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
export LOGNAME="${LOGNAME:-chimera-test}"
for arch in x86_64 i686 armel aarch64 armv7 riscv64 ppc64le s390x; do
  bin="$OUT/$arch/chimera-cmd"
  [[ -s "$bin" ]] || { echo "missing binary for $arch" >&2; exit 2; }
  emulator="${EMULATORS[$arch]}"
  if [[ -n "$emulator" ]]; then
    command -v "$emulator" >/dev/null || { echo "missing $emulator" >&2; exit 2; }
  fi
  run() {
    if [[ -n "$emulator" ]]; then "$emulator" "$@"; else "$@"; fi
  }
  invoke() {
    local name="$1"; shift
    local alias="$tmp/$name"
    ln -sf "$bin" "$alias"
    run "$alias" "$@"
  }

  output="$(invoke echo "chimera-$arch")"
  [[ "$output" == "chimera-$arch" ]] || { echo "$arch echo mismatch: $output" >&2; exit 1; }

  output="$(invoke ls "$tmp")"
  [[ -n "$output" ]] || { echo "$arch ls failed to enumerate the test directory" >&2; exit 1; }

  output="$(invoke pwd)"
  [[ "$output" == /* ]] || { echo "$arch pwd failed: $output" >&2; exit 1; }

  invoke true
  if invoke false; then echo "$arch false returned success" >&2; exit 1; fi

  invoke touch "$tmp/touched-$arch"
  [[ -f "$tmp/touched-$arch" ]] || { echo "$arch touch failed" >&2; exit 1; }

  printf 'copy-source\n' > "$tmp/copy-source-$arch"
  invoke cp "$tmp/copy-source-$arch" "$tmp/copy-target-$arch"
  cmp -s "$tmp/copy-source-$arch" "$tmp/copy-target-$arch" || { echo "$arch cp failed" >&2; exit 1; }

  output="$(invoke cat "$tmp/copy-target-$arch")"
  [[ "$output" == "copy-source" ]] || { echo "$arch cat failed: $output" >&2; exit 1; }

  invoke mv "$tmp/copy-target-$arch" "$tmp/moved-$arch"
  [[ -f "$tmp/moved-$arch" && ! -e "$tmp/copy-target-$arch" ]] || { echo "$arch mv failed" >&2; exit 1; }

  invoke mkdir "$tmp/made-dir-$arch"
  [[ -d "$tmp/made-dir-$arch" ]] || { echo "$arch mkdir failed" >&2; exit 1; }

  invoke rm "$tmp/moved-$arch"
  [[ ! -e "$tmp/moved-$arch" ]] || { echo "$arch rm failed" >&2; exit 1; }

  output="$(invoke whoami)"
  [[ -n "$output" ]] || { echo "$arch whoami failed" >&2; exit 1; }
  output="$(invoke hostname)"
  [[ -n "$output" ]] || { echo "$arch hostname failed" >&2; exit 1; }
  output="$(invoke date)"
  [[ -n "$output" ]] || { echo "$arch date failed" >&2; exit 1; }
  invoke clear >/dev/null

  printf 'line-one\nline-two\nline-three\n' > "$tmp/input-$arch"
  output="$(invoke head -n 1 "$tmp/input-$arch")"
  [[ "$output" == "line-one" ]] || { echo "$arch head failed: $output" >&2; exit 1; }
  output="$(invoke tail -n 1 "$tmp/input-$arch")"
  [[ "$output" == "line-three" ]] || { echo "$arch tail failed: $output" >&2; exit 1; }
  output="$(invoke wc -l "$tmp/input-$arch")"
  [[ "$output" == *"3"* ]] || { echo "$arch wc failed: $output" >&2; exit 1; }

  output="$(invoke basename /var/tmp/sample.txt)"
  [[ "$output" == "sample.txt" ]] || { echo "$arch basename failed: $output" >&2; exit 1; }
  output="$(invoke dirname /var/tmp/sample.txt)"
  [[ "$output" == "/var/tmp" ]] || { echo "$arch dirname failed: $output" >&2; exit 1; }
  output="$(invoke uname -s)"
  [[ -n "$output" ]] || { echo "$arch uname failed" >&2; exit 1; }

  invoke ln -s "$tmp/input-$arch" "$tmp/link-$arch"
  output="$(invoke readlink "$tmp/link-$arch")"
  [[ "$output" == "$tmp/input-$arch" ]] || { echo "$arch readlink failed: $output" >&2; exit 1; }
  invoke rmdir "$tmp/made-dir-$arch"
  [[ ! -e "$tmp/made-dir-$arch" ]] || { echo "$arch rmdir failed" >&2; exit 1; }

  invoke sleep 0.001
  output="$(invoke env)"
  [[ "$output" == *"PATH="* ]] || { echo "$arch env failed" >&2; exit 1; }
  output="$(invoke printenv PATH)"
  [[ -n "$output" ]] || { echo "$arch printenv failed" >&2; exit 1; }
  output="$(invoke id -u)"
  [[ "$output" =~ ^[0-9]+$ ]] || { echo "$arch id failed: $output" >&2; exit 1; }
  output="$(invoke seq 1 3)"
  expected="$(printf '1\n2\n3')"
  [[ "$output" == "$expected" ]] || { echo "$arch seq failed: $output" >&2; exit 1; }

  set +o pipefail
  output="$(invoke yes yes | head -n 1)"
  set -o pipefail
  [[ "$output" == "yes" ]] || { echo "$arch yes failed: $output" >&2; exit 1; }

  temp_file="$(invoke mktemp)"
  [[ -f "$temp_file" ]] || { echo "$arch mktemp failed: $temp_file" >&2; exit 1; }
  temp_dir="$(invoke mktemp -d "$tmp/dir.XXXXXX")"
  [[ -d "$temp_dir" ]] || { echo "$arch mktemp -d failed: $temp_dir" >&2; exit 1; }
  rm -f "$temp_file"

  invoke chmod 600 "$tmp/input-$arch"
  output="$(invoke stat "$tmp/input-$arch")"
  [[ "$output" == *"Mode: 0600"* ]] || { echo "$arch stat failed: $output" >&2; exit 1; }

  invoke sync
  output="$(invoke tty || true)"
  [[ "$output" == "not a tty" || "$output" == /dev/* ]] || { echo "$arch tty failed: $output" >&2; exit 1; }
  output="$(invoke logname)"
  [[ -n "$output" ]] || { echo "$arch logname failed" >&2; exit 1; }
  invoke kill -0 "$$"
  output="$(invoke uptime)"
  [[ "$output" == up* ]] || { echo "$arch uptime failed: $output" >&2; exit 1; }

  # Verify env assignment and PATH-based dispatch to another multicall alias.
  ln -sf "$bin" "$tmp/env"
  ln -sf "$bin" "$tmp/printenv"
  output="$(PATH="$tmp:$PATH" run "$tmp/env" CHIMERA_TEST_VALUE=verified printenv CHIMERA_TEST_VALUE)"
  [[ "$output" == "verified" ]] || { echo "$arch env assignment/dispatch failed: $output" >&2; exit 1; }

  printf 'PASS %s Linux userspace command ABI smoke tests (38 aliases)\n' "$arch"
done

python3 - "$OUT/manifest.json" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
data=json.loads(p.read_text(encoding="utf-8"))
expected={"x86_64","i686","armel","aarch64","armv7","riscv64","ppc64le","s390x"}
rows=data.get("targets",[])
if {row.get("target") for row in rows} != expected:
    raise SystemExit("ABI matrix target set is incomplete")
for row in rows:
    if row.get("binary_status") != "cross-compiled-and-elf-machine-validated":
        raise SystemExit(f"{row.get('target')} binary was not ELF-validated")
    row["runtime_status"] = "native-linux-abi-smoke-tested" if row["target"] == "x86_64" else "qemu-user-linux-abi-smoke-tested"
data["runtime_scope"]="Linux userspace under native execution/QEMU user mode; this does not validate Koronos syscalls or kernel boot."
data["smoke_test_aliases"]=["pwd","echo","ls","cp","mv","touch","mkdir","rm","cat","clear","whoami","hostname","date","true","false","rmdir","ln","readlink","basename","dirname","uname","wc","head","tail","sleep","chmod","env","id","kill","logname","mktemp","printenv","seq","stat","sync","tty","uptime","yes"]
p.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print("Updated manifest with 38 Linux ABI alias smoke tests per target; Koronos remains untested.")
PY
