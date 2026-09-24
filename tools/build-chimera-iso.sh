#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
LOG_DIR="$ROOT/build/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/chimera-iso-build.log"
exec > >(tee -a "$LOG") 2>&1
JOBS="$(printenv CHIMERA_JOBS || echo 2)"
AUTO_DEPS="$(printenv CHIMERA_AUTO_INSTALL_DEPS || echo 1)"
SKIP_TESTS="$(printenv CHIMERA_SKIP_TESTS || echo 0)"
say(){ printf '\n[%s] %s\n' "$1" "$2"; }
die(){ echo "[ERROR] $*" >&2; exit 2; }
require_cmd(){ command -v "$1" >/dev/null 2>&1 || MISSING+=("$1"); }
repair_literal_newlines(){
  local file="$1"; [ -f "$file" ] || return 0
  python3 - "$file" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding="utf-8")
out=[]; changed=False
for line in s.splitlines(keepends=True):
    if "\\n" in line and '"' not in line.split("\\n",1)[0]:
        parts=line.split("\\n"); rebuilt=parts[0]
        for part in parts[1:]: rebuilt+="\n"+part
        if rebuilt != line: line=rebuilt; changed=True
    out.append(line)
if changed: p.write_text("".join(out),encoding="utf-8"); print("[FIX] repaired",p)
PY
}
MISSING=()
say CHECK "Checking host dependencies and ISO generators"
for c in bash python3 cmake gcc g++ ld as make pkg-config git curl file cpio gzip xorriso grub-mkrescue grub-file busybox awk sed grep sha256sum; do require_cmd "$c"; done
MISSING_COUNT="$(printf '%s\n' "${MISSING[@]}" | sed '/^$/d' | wc -l)"
if [ "$MISSING_COUNT" -gt 0 ] && [ "$AUTO_DEPS" = "1" ] && [ "$(id -u)" -eq 0 ] && [ -f /etc/debian_version ] && command -v apt-get >/dev/null 2>&1; then
  say DEPS "Installing missing Debian/Ubuntu build dependencies"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends build-essential gcc g++ binutils make cmake ninja-build pkg-config python3 python3-dev python3-venv python3-pip python3-setuptools python3-wheel git curl wget ca-certificates file rsync cpio gzip xz-utils bzip2 tar busybox xorriso grub-pc-bin grub-efi-amd64-bin grub-common grub2-common openssl libssl-dev zlib1g-dev libffi-dev libreadline-dev libsqlite3-dev libncurses-dev libboost-dev gawk sed grep coreutils util-linux
  MISSING=()
  for c in bash python3 cmake gcc g++ ld as make pkg-config git curl file cpio gzip xorriso grub-mkrescue grub-file busybox awk sed grep sha256sum; do require_cmd "$c"; done
fi
MISSING_COUNT="$(printf '%s\n' "${MISSING[@]}" | sed '/^$/d' | wc -l)"
[ "$MISSING_COUNT" -eq 0 ] || die "Missing required dependencies: ${MISSING[*]}"
say CHECK "Checking compiler/toolchain versions"
cmake --version | head -n1
gcc --version | head -n1
g++ --version | head -n1
python3 --version
say CHECK "Validating application catalog"
python3 - "$ROOT/applications/catalog.json" "$ROOT" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); root=Path(sys.argv[2]); apps=json.loads(p.read_text())["applications"]
counts={}
for a in apps: counts[a.get("integration","unknown")]=counts.get(a.get("integration","unknown"),0)+1
print("[APP] catalog entries:",len(apps)); print("[APP] integration:",counts)
for a in apps:
    if a.get("integration") in ("native","fetched") and a.get("source"):
        p1=root/"applications"/a["source"]; p2=root/a["source"]
        if not p1.exists() and not p2.exists(): print("[APP] not vendored; registry-only:",a.get("id"))
PY
say CHECK "Checking optional application toolchains"
for c in javac java rustc cargo node npm perl dotnet; do
  if command -v "$c" >/dev/null 2>&1; then "$c" --version 2>/dev/null | head -n1 || true; else echo "[INFO] optional toolchain unavailable: $c"; fi
done
say CHECK "Repairing known generated sources"
repair_literal_newlines "$ROOT/arch/registern/ChimeraCorePool.cpp"
say BUILD "Configuring CMake"
BUILD="$ROOT/build/full"
CMAKE_BUILD="$BUILD/cmake"
mkdir -p "$BUILD"
cmake -S "$ROOT" -B "$CMAKE_BUILD" -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
say BUILD "Compiling all configured Chimera II targets"
cmake --build "$CMAKE_BUILD" --target all koronos-x86_64 --parallel "$JOBS"
if [ "$SKIP_TESTS" != "1" ]; then
  say TEST "Running CTest"
  if ! ctest --test-dir "$CMAKE_BUILD" --output-on-failure --parallel "$JOBS"; then
    [ "$(printenv CHIMERA_ALLOW_TEST_FAILURES || echo 0)" = "1" ] || die "CTest failed"
  fi
fi
say BUILD "Building network, toolchain, drivers, compatibility, mobile, desktop and live artifacts"
for tool in build-network-toolkit.sh build-toolchain-bundle.sh fetch-driver-payloads.sh build-koronos-targets.sh fetch-foreign-runtimes.sh build-compatibility-binaries.sh build-mobile-edition.sh build-desktop-binaries.sh build-live-boot-binaries.sh; do
  chmod +x "$ROOT/tools/$tool"
done
"$ROOT/tools/build-network-toolkit.sh"
"$ROOT/tools/build-toolchain-bundle.sh"
"$ROOT/tools/fetch-driver-payloads.sh"
"$ROOT/tools/build-koronos-targets.sh"
"$ROOT/tools/fetch-foreign-runtimes.sh"
"$ROOT/tools/build-compatibility-binaries.sh"
"$ROOT/tools/build-mobile-edition.sh"
"$ROOT/tools/build-desktop-binaries.sh"
"$ROOT/tools/build-live-boot-binaries.sh"
say ISO "Generating BIOS/UEFI ISO"
"$ROOT/boot/iso/build-iso.sh"
FINAL="$ROOT/boot/iso/dist/output.iso"
TARGET="$ROOT/build/iso/chimera-ii-os.iso"
[ -s "$FINAL" ] || die "ISO not produced: $FINAL"
mkdir -p "$(dirname "$TARGET")"
cp -f "$FINAL" "$TARGET"
sha256sum "$TARGET" | tee "$TARGET.sha256"
cp -f "$TARGET" "$ROOT/chimera-ii-os.iso"
cp -f "$TARGET.sha256" "$ROOT/chimera-ii-os.iso.sha256"
if command -v xorriso >/dev/null 2>&1; then xorriso -indev "$TARGET" -report_el_torito plain -report_system_area plain > "$ROOT/build/iso/ISO-BOOT-REPORT.txt" || true; fi
say VERIFY "Validating final ISO"
python3 "$ROOT/boot/iso/validate-iso.py" --tree "$ROOT/boot/iso/dist/iso" --write-manifest "$ROOT/build/iso/SHA256SUMS" || true
[ -s "$ROOT/chimera-ii-os.iso" ] || die "Final ISO copy missing"
echo "ISO: $ROOT/chimera-ii-os.iso"
echo "SHA256: $ROOT/chimera-ii-os.iso.sha256"
echo "LOG: $LOG"
