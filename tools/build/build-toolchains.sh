#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="${ROOT}/build/toolchains"
mkdir -p "$BUILD"
command -v cmake >/dev/null || { echo 'cmake required'; exit 1; }
command -v ninja >/dev/null || echo 'ninja not found: CMake generator may use Makefiles'
cmake -S "$ROOT" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD" --parallel
printf '%s\n' 'Toolchain host build complete.'
printf '%s\n' 'Install language/compiler packages according to toolchains/tool_registry.json.'
