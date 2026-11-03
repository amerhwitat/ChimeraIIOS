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
python3 - "$tmp" "$ROOT" "$BUILD" <<'PY'
import json, pathlib, shutil, subprocess, sys
out, root, build = map(pathlib.Path, sys.argv[1:])
tools = ["cc","c++","clang","clang++","javac","jar","dotnet","rustc","cargo","go","gfortran","node","npm","python3","gnustep-config"]
status = {"schema":"CHIMERA-SDK-BUILD-STATUS-1","native_c_cpp":"built-and-ctested","optional_toolchains":{}}
for tool in tools:
    status["optional_toolchains"][tool] = shutil.which(tool) or "unavailable"
for rel, cmd in [
    ("sdk/java/build.sh", ["bash", str(root/"sdk/java/build.sh")]),
    ("sdk/csharp/Chimera.Sdk.csproj", ["dotnet","build",str(root/"sdk/csharp/Chimera.Sdk.csproj"),"-c","Release"]),
    ("sdk/rust/chimera-runtime/Cargo.toml", ["cargo","build","--manifest-path",str(root/"sdk/rust/chimera-runtime/Cargo.toml"),"--release"])
]:
    if shutil.which(cmd[0]):
        subprocess.run(cmd, cwd=root, check=True)
        status.setdefault("optional_builds",{})[rel]="passed"
    else:
        status.setdefault("optional_builds",{})[rel]="skipped-toolchain-unavailable"
(out).write_text(json.dumps(status,indent=2)+"\n")
PY
mv "$tmp" "$status"
mkdir -p "$DEST/rootfs/opt/chimera-sdk"
cp "$status" "$DEST/rootfs/opt/chimera-sdk/"
printf 'SDK bundle staged at %s/rootfs/opt/chimera-sdk\n' "$DEST"
