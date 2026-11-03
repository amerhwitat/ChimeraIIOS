#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="${CHIMERA_SDK_BUILD_DIR:-$ROOT/build}"
DESTDIR="${CHIMERA_SDK_DESTDIR:-}"
PREFIX="${CHIMERA_SDK_PREFIX:-/opt/chimera-sdk}"
JOBS="${CHIMERA_SDK_JOBS:-2}"
mkdir -p "$BUILD"

cmake -S "$ROOT" -B "$BUILD/cmake-sdk" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX"
cmake --build "$BUILD/cmake-sdk" --target chimera_sdk chimera-sdk-config \
  --parallel "$JOBS"
ctest --test-dir "$BUILD/cmake-sdk" --output-on-failure

if command -v javac >/dev/null 2>&1 && command -v jar >/dev/null 2>&1; then
  CHIMERA_SDK_JAVA_BUILD_DIR="$BUILD/java/classes" CHIMERA_SDK_JAVA_JAR="$BUILD/chimera-sdk.jar" "$ROOT/java/build.sh"
else
  echo "[SDK] OpenJDK unavailable; Java source retained but JAR build skipped." >&2
fi
if command -v dotnet >/dev/null 2>&1; then
  dotnet build "$ROOT/csharp/Chimera.Sdk.csproj" -c Release -p:BaseOutputPath="$BUILD/dotnet/bin/" -p:BaseIntermediateOutputPath="$BUILD/dotnet/obj/"
else
  echo "[SDK] .NET SDK unavailable; C# source retained but managed build skipped." >&2
fi
if command -v cargo >/dev/null 2>&1; then
  CARGO_TARGET_DIR="$BUILD/rust-target" cargo test --manifest-path "$ROOT/rust/chimera-runtime/Cargo.toml" --locked
  CARGO_TARGET_DIR="$BUILD/rust-target" cargo build --release --manifest-path "$ROOT/rust/chimera-runtime/Cargo.toml" --locked
else
  echo "[SDK] Cargo unavailable; Rust source retained but crate build skipped." >&2
fi
PYTHONPYCACHEPREFIX="$BUILD/python-pycache" python3 -m compileall -q "$ROOT/python/chimera_sdk"

if [[ -n "$DESTDIR" ]]; then
  mkdir -p "$DESTDIR"
  DESTDIR="$DESTDIR" cmake --install "$BUILD/cmake-sdk" --prefix "$PREFIX"
  test -s "$DESTDIR$PREFIX/lib/libchimera_sdk.a" -o -s "$DESTDIR$PREFIX/lib64/libchimera_sdk.a"
  test -s "$DESTDIR$PREFIX/include/chimera/sdk.h"
  if [[ -s "$BUILD/chimera-sdk.jar" ]]; then
    install -D -m 0644 "$BUILD/chimera-sdk.jar" "$DESTDIR$PREFIX/share/java/chimera-sdk.jar"
  fi
  if [[ -d "$BUILD/dotnet/bin" ]]; then
    while IFS= read -r -d '' artifact; do
      install -D -m 0644 "$artifact" "$DESTDIR$PREFIX/lib/dotnet/Chimera.Sdk.dll"
    done < <(find "$BUILD/dotnet/bin" -type f -name 'Chimera.Sdk.dll' -print0)
  fi
  if [[ -s "$BUILD/rust-target/release/libchimera_runtime.a" ]]; then
    install -D -m 0644 "$BUILD/rust-target/release/libchimera_runtime.a" "$DESTDIR$PREFIX/lib/libchimera_runtime.a"
  fi
  if [[ -s "$BUILD/rust-target/release/libchimera_runtime.so" ]]; then
    install -D -m 0644 "$BUILD/rust-target/release/libchimera_runtime.so" "$DESTDIR$PREFIX/lib/libchimera_runtime.so"
  fi
fi

echo "[SDK] Build and CTest completed: $BUILD/cmake-sdk"
