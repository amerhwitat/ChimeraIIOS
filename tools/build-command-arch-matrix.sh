#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${CHIMERA_CMD_SOURCE:-$ROOT/src/chimera-command-compat/chimera-cmd.c}"
OUT="${CHIMERA_CMD_OUT:-$ROOT/build/command-arch-matrix}"
CC_BIN="${CC:-cc}"
ARCH="${TARGET_ARCH:-$(uname -m)}"
COMMANDS=(pwd echo ls cp mv touch mkdir rm cat clear whoami hostname date true false)
test -s "$SOURCE" || { echo "missing command source: $SOURCE" >&2; exit 2; }
command -v "$CC_BIN" >/dev/null 2>&1 || { echo "missing compiler: $CC_BIN" >&2; exit 127; }
command -v readelf >/dev/null 2>&1 || { echo "readelf is required to verify target ELF metadata" >&2; exit 127; }
STAGE="$OUT/$ARCH"
BIN="$STAGE/usr/lib/chimera/chimera-cmd.native"
ENTRY="$STAGE/usr/lib/chimera/native-bin"
mkdir -p "$(dirname "$BIN")" "$ENTRY"
"$CC_BIN" -std=c11 -O2 -Wall -Wextra -Werror "$SOURCE" -o "$BIN"
chmod 0755 "$BIN"
for name in "${COMMANDS[@]}"; do
  ln -sfn ../chimera-cmd.native "$ENTRY/$name"
done
readelf -h "$BIN" > "$STAGE/elf-header.txt"
python3 - "$BIN" "$ENTRY" "$ARCH" "${COMMANDS[@]}" <<'PY'
import hashlib,json,pathlib,subprocess,sys
binary=pathlib.Path(sys.argv[1]); entries=pathlib.Path(sys.argv[2]); arch=sys.argv[3]
commands=sys.argv[4:]
header=subprocess.run(["readelf","-h",str(binary)],check=True,text=True,stdout=subprocess.PIPE).stdout
machine=next((line.split(":",1)[1].strip() for line in header.splitlines() if line.strip().startswith("Machine:")),None)
if not machine: raise SystemExit("ELF machine metadata missing")
expected={"x86_64":"Advanced Micro Devices X86-64","i686":"Intel 80386",
          "aarch64":"AArch64","armv7":"ARM","riscv64":"RISC-V",
          "ppc64le":"PowerPC64","s390x":"IBM S/390"}.get(arch)
if expected is None: raise SystemExit(f"unsupported target architecture: {arch}")
if expected not in machine and machine not in expected:
    raise SystemExit(f"wrong-architecture ELF: target={arch} expected={expected!r} actual={machine!r}")
digest=hashlib.sha256(binary.read_bytes()).hexdigest()
rows=[]
for name in commands:
    link=entries/name
    if not link.is_symlink() or link.resolve()!=binary.resolve():
        raise SystemExit(f"invalid native multicall entrypoint: {name}")
    rows.append({"name":name,"entrypoint":"/usr/lib/chimera/native-bin/"+name,
                 "provider":"/usr/lib/chimera/chimera-cmd.native","sha256":digest,
                 "elf_machine":machine,"status":"native-elf-entrypoint-built"})
report={"schema":"CHIMERA-NATIVE-MULTICALL-ARCH-1","target_architecture":arch,
        "binary":"/usr/lib/chimera/chimera-cmd.native","binary_sha256":digest,
        "elf_machine":machine,"implemented_command_count":len(rows),
        "commands":rows,
        "limitations":"Compilation and ELF inspection only; cross-architecture runtime semantics and Koronos syscall/ABI compatibility require separate tests."}
path=binary.parent/"native-command-coverage.json"
path.write_text(json.dumps(report,indent=2)+"\\n",encoding="utf-8")
print(f"Built one genuine native multicall ELF for {arch}: {len(rows)} command entrypoints; machine={machine}; sha256={digest}")
PY
