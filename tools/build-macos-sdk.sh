#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/build/macos-sdk-report.json}"
SDK_ROOT="${MACOS_SDKROOT:-$ROOT/third_party/macos-extracted}"
mkdir -p "$(dirname "$OUT")"
python3 - "$SDK_ROOT" "$OUT" <<'PY'
import json, pathlib, shutil, sys
sdk, out = map(pathlib.Path, sys.argv[1:])
names=("clang","clang++","clangd","cmake","ninja","o64-clang","o64-clang++","oa64-clang","oa64-clang++","swiftc")
tools={n:shutil.which(n) for n in names}
licenses=[]
if sdk.is_dir():
    licenses=[str(p.relative_to(sdk)) for p in sdk.rglob("*") if p.is_file() and any(k in p.name.lower() for k in ("license","eula","agreement"))]
settings=list(sdk.rglob("SDKSettings.plist")) if sdk.is_dir() else []
report={"schema":"macos-cross-development-report-v1",
 "status":"review-required" if sdk.is_dir() else "blocked",
 "sdk":{"path":str(sdk),"present":sdk.is_dir(),"settings_plist_count":len(settings),
        "license_files":licenses[:50],"redistribution":"prohibited-unless-license-explicitly-permits"},
 "toolchains":{k:{"present":bool(v),"path":v or ""} for k,v in tools.items()},
 "darwin_cross_compiler_available":bool(tools["o64-clang"] or tools["oa64-clang"]),
 "application_build":{"status":"not-attempted","reason":"Set MACOS_SDK_LICENSE_REVIEWED=1 after reviewing the exact SDK license and provide an osxcross Darwin compiler."},
 "iso_policy":"Ship report, templates and first-party wrappers only; never copy proprietary SDK frameworks, headers, runtimes or Xcode binaries."}
if not sdk.is_dir():
    report["reason"]="SDK directory is absent; provide a licensed SDK using MACOS_SDKROOT or third_party/macos-extracted."
else:
    report["reason"]="SDK detected. License review and SDK platform metadata validation are required."
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],"sdk_present":sdk.is_dir(),"darwin_cross_compiler":report["darwin_cross_compiler_available"]}))
PY
if [[ "${MACOS_SDK_LICENSE_REVIEWED:-0}" == "1" && -d "$SDK_ROOT" ]]; then
  compiler=""
  for candidate in o64-clang oa64-clang; do
    if command -v "$candidate" >/dev/null 2>&1; then compiler="$candidate"; break; fi
  done
  if [[ -n "$compiler" ]] && command -v cmake >/dev/null 2>&1 && command -v ninja >/dev/null 2>&1; then
    build_dir="$(dirname "$OUT")/macos-objective-c-build"
    if MACOS_SDKROOT="$SDK_ROOT" cmake -S "$ROOT/sdk/macos/examples/hello-macos" -B "$build_dir" \
      -G Ninja -DCMAKE_TOOLCHAIN_FILE="$ROOT/sdk/macos/templates/DarwinCross.cmake" \
      -DCMAKE_OSX_SYSROOT="$SDK_ROOT" >/dev/null &&
      cmake --build "$build_dir" --parallel 2; then
      python3 - "$OUT" <<'PY'
import json, pathlib, sys
p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text())
d["application_build"]={"status":"built","artifact":"macos-objective-c-build/HelloMacOS.app","reason":"Objective-C sample compiled using externally supplied SDK and osxcross."}
p.write_text(json.dumps(d,indent=2)+"\n")
PY
    else
      python3 - "$OUT" <<'PY'
import json, pathlib, sys
p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text())
d["application_build"]={"status":"failed","reason":"CMake/osxcross compilation failed; inspect build diagnostics."}
p.write_text(json.dumps(d,indent=2)+"\n")
PY
      exit 1
    fi
  else
    echo "MACOS_SDK_LICENSE_REVIEWED=1 but osxcross, CMake or Ninja is unavailable." >&2
    exit 2
  fi
fi
