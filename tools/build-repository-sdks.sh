#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/build/sdk-build"
if [[ -n "$(printenv CHIMERA_SDK_BUILD_DIR 2>/dev/null)" ]]; then OUT="$(printenv CHIMERA_SDK_BUILD_DIR)"; fi
STRICT="$(printenv CHIMERA_SDK_BUILD_STRICT 2>/dev/null || echo 0)"
JOBS="$(printenv JOBS 2>/dev/null || echo 2)"
mkdir -p "$OUT"; LOG="$OUT/sdk-build.log"; MANIFEST="$OUT/sdk-build-results.tsv"
: >"$LOG"; printf 'status\tkind\tpath\tdetail\n' >"$MANIFEST"
declare -A SEEN=()
run(){ local kind="$1" dir="$2" cmd="$3"; [[ \${SEEN["$dir"]+x} ]] && return; SEEN["$dir"]=1; printf '[SDK] %s %s\n' "$kind" "$dir" | tee -a "$LOG"; if (cd "$dir" && eval "$cmd") >>"$LOG" 2>&1; then printf 'PASS\t%s\t%s\tbuilt\n' "$kind" "\${dir#$ROOT/}" >>"$MANIFEST"; else local rc=$?; printf 'FAIL\t%s\t%s\texit=%s\n' "$kind" "\${dir#$ROOT/}" "$rc" >>"$MANIFEST"; echo "[SDK] FAILED: $kind $dir ($rc)" | tee -a "$LOG"; fi; }
find_files(){ find "$ROOT" -type d \( -name .git -o -name node_modules -o -name vendor -o -name third_party -o -name build -o -name dist -o -name target -o -name .venv -o -name venv -o -name .tox \) -prune -o "$@" -type f -print0; }
while IFS= read -r -d '' f; do d="$(dirname "$f")"; run cmake "$d" "cmake -S . -B build/chimera-sdk -DCMAKE_BUILD_TYPE=Release && cmake --build build/chimera-sdk --parallel $JOBS"; done < <(find_files -name CMakeLists.txt)
while IFS= read -r -d '' f; do d="$(dirname "$f")"; if command -v cargo >/dev/null 2>&1; then run cargo "$d" 'cargo build --release --locked'; else printf 'SKIP\tcargo\t%s\tcargo-not-installed\n' "\${d#$ROOT/}" >>"$MANIFEST"; fi; done < <(find_files -name Cargo.toml)
while IFS= read -r -d '' f; do d="$(dirname "$f")"; if command -v go >/dev/null 2>&1; then run go "$d" 'go build ./...'; else printf 'SKIP\tgo\t%s\tgo-not-installed\n' "\${d#$ROOT/}" >>"$MANIFEST"; fi; done < <(find_files -name go.mod)
while IFS= read -r -d '' f; do d="$(dirname "$f")"; if command -v mvn >/dev/null 2>&1; then run maven "$d" 'mvn -B -DskipTests package'; else printf 'SKIP\tmaven\t%s\tmvn-not-installed\n' "\${d#$ROOT/}" >>"$MANIFEST"; fi; done < <(find_files -name pom.xml)
while IFS= read -r -d '' f; do d="$(dirname "$f")"; if command -v npm >/dev/null 2>&1 && node -e 'const p=require(process.argv[1]);process.exit(p.scripts&&p.scripts.build?0:1)' "$f" >/dev/null 2>&1; then run npm "$d" 'if [[ -f package-lock.json ]]; then npm ci; elif [[ -f pnpm-lock.yaml ]] && command -v pnpm >/dev/null 2>&1; then pnpm install --frozen-lockfile; elif [[ -f yarn.lock ]] && command -v yarn >/dev/null 2>&1; then yarn install --frozen-lockfile; fi; npm run build --if-present'; else printf 'SKIP\tnpm\t%s\tno-build-script-or-tool\n' "\${d#$ROOT/}" >>"$MANIFEST"; fi; done < <(find_files -name package.json)
while IFS= read -r -d '' f; do d="$(dirname "$f")"; if [[ -x "$f" ]]; then run gradle "$d" './gradlew --no-daemon build -x test'; elif command -v gradle >/dev/null 2>&1; then run gradle "$d" 'gradle --no-daemon build -x test'; else printf 'SKIP\tgradle\t%s\tgradle-not-installed\n' "\${d#$ROOT/}" >>"$MANIFEST"; fi; done < <(find_files -name gradlew)
while IFS= read -r -d '' f; do d="$(dirname "$f")"; if [[ ! -f "$d/gradlew" ]]; then if command -v gradle >/dev/null 2>&1; then run gradle "$d" 'gradle --no-daemon build -x test'; else printf 'SKIP\tgradle\t%s\tgradle-not-installed\n' "${d#$ROOT/}" >>"$MANIFEST"; fi; fi; done < <(find_files -name build.gradle -o -name build.gradle.kts)
printf '\nSDK build results: %s\n' "$MANIFEST"
if [[ "$STRICT" == 1 ]] && grep -q '^FAIL' "$MANIFEST"; then echo "SDK strict mode: one or more project builds failed." >&2; exit 1; fi
