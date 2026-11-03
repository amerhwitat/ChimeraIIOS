#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="${CHIMERA_SDK_BUILD_DIR:-$ROOT/build/sdk-bundle}"
DEST="${1:-${CHIMERA_SDK_STAGE_DIR:-$ROOT/build/sdk-stage}}"
mkdir -p "$BUILD" "$DEST"
status="$DEST/sdk-build-status.json"
tmp="$status.tmp"
cmake -S "$ROOT/sdk" -B "$BUILD/cmake" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/chimera-sdk
cmake --build "$BUILD/cmake" --parallel "${JOBS:-2}"
ctest --test-dir "$BUILD/cmake" --output-on-failure
DESTDIR="$DEST/rootfs" cmake --install "$BUILD/cmake"
mkdir -p "$DEST/rootfs/opt/chimera-sdk/source"
cp -a "$ROOT/sdk/." "$DEST/rootfs/opt/chimera-sdk/source/"
python3 - "$tmp" "$ROOT" <<'PY'
import json, pathlib, shutil, subprocess, sys
out, root = map(pathlib.Path, sys.argv[1:])
tools = ["cc","c++","clang","clang++","javac","jar","dotnet","rustc","cargo","go","gfortran","node","npm","python3","gnustep-config"]
status = {"schema":"CHIMERA-SDK-BUILD-STATUS-1","native_c_cpp":"built-and-ctested","optional_toolchains":{},"optional_builds":{}}
for tool in tools:
    status["optional_toolchains"][tool] = shutil.which(tool) or "unavailable"
jobs = [
    ("sdk/java/build.sh", ["bash", str(root/"sdk/java/build.sh")], "javac"),
    ("sdk/csharp/Chimera.Sdk.csproj", ["dotnet","build",str(root/"sdk/csharp/Chimera.Sdk.csproj"),"-c","Release"], "dotnet"),
    ("sdk/rust/chimera-runtime/Cargo.toml", ["cargo","build","--manifest-path",str(root/"sdk/rust/chimera-runtime/Cargo.toml"),"--release"], "cargo")
]
for rel, cmd, tool in jobs:
    if shutil.which(tool):
        subprocess.run(cmd, cwd=root, check=True)
        status["optional_builds"][rel] = "passed"
    else:
        status["optional_builds"][rel] = "skipped-toolchain-unavailable"
subprocess.run([sys.executable,"-m","compileall","-q",str(root/"sdk/python")],check=True)
status["optional_builds"]["sdk/python"] = "passed"
if shutil.which("gnustep-config") and shutil.which("clang"):
    flags = subprocess.check_output(["gnustep-config","--objc-flags"],text=True).split()
    obj = root/"build/sdk-bundle/chimera-sdk-objc.o"
    subprocess.run(["clang","-c",*flags,str(root/"sdk/objective-c/ChimeraSDK.m"),"-o",str(obj)],check=True)
    status["optional_builds"]["sdk/objective-c"] = "passed"
else:
    status["optional_builds"]["sdk/objective-c"] = "skipped-gnustep-unavailable"
(out).write_text(json.dumps(status,indent=2)+"\n")
PY
mv "$tmp" "$status"
mkdir -p "$DEST/rootfs/opt/chimera-sdk"
cp "$status" "$DEST/rootfs/opt/chimera-sdk/"
if [[ -s "$ROOT/sdk/java/chimera-sdk.jar" ]]; then
  install -D -m 0644 "$ROOT/sdk/java/chimera-sdk.jar" "$DEST/rootfs/opt/chimera-sdk/lib/chimera-sdk.jar"
fi
if [[ -d "$ROOT/sdk/rust/chimera-runtime/target/release" ]]; then
  mkdir -p "$DEST/rootfs/opt/chimera-sdk/lib/rust"
  find "$ROOT/sdk/rust/chimera-runtime/target/release" -maxdepth 1 -type f \( -name 'libchimera_runtime*.so' -o -name 'libchimera_runtime*.a' \) -exec cp -f {} "$DEST/rootfs/opt/chimera-sdk/lib/rust/" \;
fi
if [[ -d "$ROOT/sdk/csharp/bin/Release" ]]; then
  mkdir -p "$DEST/rootfs/opt/chimera-sdk/lib/dotnet"
  find "$ROOT/sdk/csharp/bin/Release" -type f \( -name '*.dll' -o -name '*.xml' \) -exec cp -f {} "$DEST/rootfs/opt/chimera-sdk/lib/dotnet/" \;
fi
printf 'SDK bundle staged at %s/rootfs/opt/chimera-sdk\n' "$DEST"
