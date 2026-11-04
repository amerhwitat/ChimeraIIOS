#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "\${BASH_SOURCE[0]}")/.." && pwd)"
OUT="\${1:-$ROOT/build/macos-sdk-report.json}"
SDK_ROOT="\${MACOS_SDKROOT:-$ROOT/third_party/macos-extracted}"
mkdir -p "$(dirname "$OUT")" "$ROOT/build/macos-cross"
python3 - "$SDK_ROOT" "$OUT" <<'PY'
import json, pathlib, shutil, sys
sdk, out = map(pathlib.Path, sys.argv[1:])
names=("clang","clang++","clangd","cmake","ninja","xcrun","o64-clang","o64-clang++","oa64-clang","swiftc")
tools={n:shutil.which(n) for n in names}
licenses=[]
if sdk.is_dir():
    licenses=[str(p.relative_to(sdk)) for p in sdk.rglob("*") if p.is_file() and any(k in p.name.lower() for k in ("license","eula","agreement"))]
settings=list(sdk.rglob("SDKSettings.plist")) if sdk.is_dir() else []
status="blocked"
reason="macOS SDK directory is absent; provide a licensed SDK using MACOS_SDKROOT or third_party/macos-extracted."
if sdk.is_dir():
    status="review-required"
    reason="SDK files detected; verify the exact license and permitted use before enabling builds or redistribution."
report={"schema":"macos-cross-development-report-v1","status":status,
 "sdk":{"path":str(sdk),"present":sdk.is_dir(),"settings_plist_count":len(settings),"license_files":licenses[:50],"redistribution":"prohibited-unless-license-explicitly-permits"},
 "toolchains":{k:{"present":bool(v),"path":v or ""} for k,v in tools.items()},
 "darwin_cross_compiler_available":bool(tools["o64-clang"] or tools["oa64-clang"]),
 "reason":reason,"iso_policy":"Ship report, templates and first-party wrappers only; never copy proprietary SDK frameworks, headers, runtimes or Xcode binaries."}
out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":status,"sdk_present":sdk.is_dir(),"darwin_cross_compiler":report["darwin_cross_compiler_available"]}))
PY
mkdir -p "$ROOT/sdk/macos/templates" "$ROOT/sdk/macos/examples/hello-macos"
cat > "$ROOT/sdk/macos/templates/DarwinCross.cmake" <<'EOF'
set(CMAKE_SYSTEM_NAME Darwin)
set(CMAKE_OSX_SYSROOT "$ENV{MACOS_SDKROOT}" CACHE PATH "Externally supplied licensed macOS SDK")
find_program(OSXCROSS_CLANG NAMES o64-clang oa64-clang)
find_program(OSXCROSS_CLANGXX NAMES o64-clang++ oa64-clang++)
if(NOT OSXCROSS_CLANG OR NOT OSXCROSS_CLANGXX)
  message(FATAL_ERROR "Install osxcross and configure Darwin compiler wrappers.")
endif()
set(CMAKE_C_COMPILER "\${OSXCROSS_CLANG}")
set(CMAKE_CXX_COMPILER "\${OSXCROSS_CLANGXX}")
EOF
