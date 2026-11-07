#!/usr/bin/env bash
# Discover and compile every SDK/toolchain project in the repository.
#
# Compiles what the host can actually compile and records an honest report: a
# missing toolchain is reported as "skipped", never as success. It is used by
# live-image/build.sh and by build-chimera-iso.sh so the ISO can ship a machine
# readable build report.
#
#   tools/build-sdks.sh [--out reports/sdk-build-report.json] [--timeout 300]
#                       [--max 40] [--only cmake,rust] [--list]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/build/sdk-build-report.json"
TIMEOUT=300
MAX=40
ONLY=""
LIST_ONLY=0
STRICT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --max) MAX="$2"; shift 2 ;;
    --only) ONLY="$2"; shift 2 ;;
    --strict) STRICT=1; shift ;;
    --list) LIST_ONLY=1; shift ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

WORK="$ROOT/build/sdk"
mkdir -p "$WORK" "$(dirname "$OUT")"
REPORT_ITEMS="$WORK/items.jsonl"
: > "$REPORT_ITEMS"

have() { command -v "$1" >/dev/null 2>&1; }

toolchains_json() {
  python3 - <<'PY'
import json, shutil, subprocess
tools = ["gcc", "g++", "clang", "clang++", "cmake", "make", "ninja", "java", "javac", "mvn",
         "gradle", "kotlinc", "cargo", "rustc", "swiftc", "dart", "flutter", "dotnet",
         "npm", "node", "python3", "go"]
out = {}
for tool in tools:
    path = shutil.which(tool)
    version = ""
    if path:
        for flag in ("--version", "-version", "version"):
            try:
                result = subprocess.run([path, flag], capture_output=True, text=True, timeout=15)
                text = (result.stdout or result.stderr).strip().splitlines()
                if text:
                    version = text[0][:120]
                    break
            except Exception:
                continue
    out[tool] = {"present": bool(path), "path": path or "", "version": version}
print(json.dumps(out, indent=1))
PY
}

record() { # kind path status seconds detail
  python3 - "$REPORT_ITEMS" "$1" "$2" "$3" "$4" "$5" <<'PY'
import json, sys
path, kind, rel, status, seconds, detail = sys.argv[1:7]
with open(path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps({"kind": kind, "path": rel, "status": status,
                             "seconds": float(seconds or 0), "detail": detail[:600]}) + "\n")
PY
}

run_step() { # kind rel workdir cmd...
  local kind="$1" rel="$2" dir="$3"; shift 3
  if [ -n "$ONLY" ] && ! printf '%s' ",$ONLY," | grep -q ",$kind,"; then
    record "$kind" "$rel" "skipped" 0 "not requested by --only"
    return 0
  fi
  local log="$WORK/$(printf '%s' "$rel" | tr '/ ' '__').log"
  local start end status=0
  start=$(date +%s)
  ( cd "$dir" && timeout "$TIMEOUT" "$@" > "$log" 2>&1 ) || status=$?
  end=$(date +%s)
  local verdict="ok"
  [ "$status" -ne 0 ] && verdict="failed"
  [ "$status" -eq 124 ] && verdict="timeout"
  local tail_text
  tail_text="$(tail -n 6 "$log" 2>/dev/null | tr '\n' ' ')"
  record "$kind" "$rel" "$verdict" "$((end - start))" "$tail_text"
  printf '  %-8s %-52s %s (%ss)\n' "$kind" "$rel" "$verdict" "$((end - start))"
}

discover() { # prints "kind<TAB>relpath"
  cd "$ROOT" || return
  find . \
    \( -path ./.git -o -path ./build -o -path ./live-image/.build -o -path ./vendor \
       -o -path ./.chimera-fix-backups -o -name node_modules -o -name .pytest_cache \) -prune -o \
    -type f \( -name CMakeLists.txt -o -name Cargo.toml -o -name Package.swift \
       -o -name pubspec.yaml -o -name pom.xml -o -name build.gradle -o -name build.gradle.kts \
       -o -name '*.csproj' -o -name '*.sln' -o -name setup.py -o -name pyproject.toml \
       -o -name package.json -o -name go.mod \) -print 2>/dev/null |
  sed 's|^\./||' |
  awk '
    /(^|\/)CMakeLists\.txt$/      { print "cmake\t" $0; next }
    /(^|\/)Cargo\.toml$/          { print "rust\t" $0; next }
    /(^|\/)Package\.swift$/       { print "swift\t" $0; next }
    /(^|\/)pubspec\.yaml$/        { print "dart\t" $0; next }
    /(^|\/)pom\.xml$/             { print "maven\t" $0; next }
    /(^|\/)build\.gradle(\.kts)?$/ { print "gradle\t" $0; next }
    /\.(csproj|sln)$/             { print "dotnet\t" $0; next }
    /(^|\/)package\.json$/        { print "node\t" $0; next }
    /(^|\/)go\.mod$/              { print "go\t" $0; next }
    /(^|\/)(setup\.py|pyproject\.toml)$/ { print "python\t" $0; next }
  '
}

echo "== SDK build discovery ($ROOT)"
mapfile -t FOUND < <(discover)
printf '   %d build definitions discovered\n' "${#FOUND[@]}"

if [ "$LIST_ONLY" -eq 1 ]; then
  printf '%s\n' "${FOUND[@]}"
  exit 0
fi

count=0
for entry in "${FOUND[@]}"; do
  [ -z "$entry" ] && continue
  [ "$count" -ge "$MAX" ] && { echo "   reached --max $MAX, stopping"; break; }
  kind="${entry%%$'\t'*}"; rel="${entry#*$'\t'}"
  dir="$ROOT/$(dirname "$rel")"
  slug="$(printf '%s' "$rel" | tr '/ ' '__')"
  case "$kind" in
    cmake)
      have cmake || { record cmake "$rel" "skipped" 0 "cmake not installed"; continue; }
      run_step cmake "$rel" "$dir" cmake -S . -B "$WORK/cmake-$slug" -DCMAKE_BUILD_TYPE=Release
      run_step cmake "$rel" "$dir" cmake --build "$WORK/cmake-$slug" -j "${JOBS:-2}"
      ;;
    rust)
      if ! have cargo; then record rust "$rel" "skipped" 0 "cargo not installed"; continue; fi
      run_step rust "$rel" "$dir" env CARGO_TARGET_DIR="$WORK/cargo-target" cargo build --release
      ;;
    swift)
      have swiftc || { record swift "$rel" "skipped" 0 "swift toolchain not installed"; continue; }
      run_step swift "$rel" "$dir" swift build -c release
      ;;
    dart)
      have dart || { record dart "$rel" "skipped" 0 "dart not installed"; continue; }
      run_step dart "$rel" "$dir" dart pub get
      ;;
    maven)
      have mvn || { record maven "$rel" "skipped" 0 "maven not installed"; continue; }
      run_step maven "$rel" "$dir" mvn -q -B -DskipTests package
      ;;
    gradle)
      have gradle || { record gradle "$rel" "skipped" 0 "gradle not installed"; continue; }
      run_step gradle "$rel" "$dir" gradle --no-daemon -q build -x test
      ;;
    dotnet)
      have dotnet || { record dotnet "$rel" "skipped" 0 "dotnet SDK not installed"; continue; }
      run_step dotnet "$rel" "$dir" dotnet build -c Release --nologo
      ;;
    node)
      if ! have npm; then record node "$rel" "skipped" 0 "npm not installed"; continue; fi
      run_step node "$rel" "$dir" npm install --no-audit --no-fund --loglevel=error
      ;;
    go)
      have go || { record go "$rel" "skipped" 0 "go not installed"; continue; }
      run_step go "$rel" "$dir" go build ./...
      ;;
    python)
      run_step python "$rel" "$dir" python3 -m compileall -q .
      ;;
  esac
  count=$((count + 1))
done

# Plain-language sources that need no build system but must still parse.
if have javac; then
  mapfile -t JAVA < <(cd "$ROOT" && find . -path ./.git -prune -o -name '*.java' -print 2>/dev/null | grep -v '/build/' | head -20)
  if [ "${#JAVA[@]}" -gt 0 ]; then
    mkdir -p "$WORK/javac-out"
    run_step java "java-sources" "$ROOT" javac -d "$WORK/javac-out" "${JAVA[@]}"
  fi
fi

python3 - "$REPORT_ITEMS" "$OUT" "$ROOT" <<'PY'
import json, os, platform, subprocess, sys
items_path, out_path, root = sys.argv[1:4]
items = [json.loads(line) for line in open(items_path, encoding="utf-8") if line.strip()]
summary = {"ok": 0, "failed": 0, "skipped": 0, "timeout": 0}
for item in items:
    summary[item["status"]] = summary.get(item["status"], 0) + 1
try:
    commit = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True, timeout=10).stdout.strip()
except Exception:
    commit = ""
payload = {
    "schema": "chimera-sdk-build-report-1",
    "generated": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip(),
    "commit": commit,
    "host": {"platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version()},
    "summary": summary,
    "projects": items,
}
json.dump(payload, open(out_path, "w", encoding="utf-8"), indent=1)
print("report: %s (%s)" % (out_path, summary))
PY

if [ "$STRICT" -eq 1 ]; then
  python3 - "$OUT" <<'PY'
import json, sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
summary = report.get("summary", {})
projects = report.get("projects", [])
problems = {key: int(summary.get(key, 0)) for key in ("failed", "timeout", "skipped")
            if int(summary.get(key, 0)) != 0}
if not projects:
    raise SystemExit("strict SDK build found no build definitions; refusing an empty success")
if problems:
    raise SystemExit(f"strict SDK build did not pass: {problems}")
print(f"STRICT SDK PASS: {len(projects)} build/test records; no failures, timeouts or skipped toolchains")
PY
fi
exit 0
