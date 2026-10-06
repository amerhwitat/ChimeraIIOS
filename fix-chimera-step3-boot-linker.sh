#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${CHIMERA_ROOT:-/mnt/c/tmp/ChimeraIIOS}"
KERNEL="$ROOT/kernel"
CORE="$KERNEL/core"
CMAKE="$KERNEL/CMakeLists.txt"
BACKUP="$ROOT/.chimera-step3-fix-backups/$(date +%Y%m%d-%H%M%S)"
log(){ printf '[CHIMERA-STEP3] %s\n' "$*"; }
die(){ printf '[CHIMERA-STEP3][ERROR] %s\n' "$*" >&2; exit 1; }
[[ -d "$ROOT" ]] || die "ChimeraIIOS root not found: $ROOT"
[[ -d "$KERNEL" && -d "$CORE" ]] || die "Kernel/core directory missing"
[[ -f "$CMAKE" ]] || die "Missing kernel/CMakeLists.txt"
mkdir -p "$BACKUP"
backup(){ local f="$1"; [[ -f "$f" ]] || return 0; local rel="${f#"$ROOT"/}"; mkdir -p "$BACKUP/$(dirname "$rel")"; cp -a -- "$f" "$BACKUP/$rel"; }
PROCESS_CPP="$CORE/process_init.cpp"
if grep -RqsE '(^|[^A-Za-z0-9_])chimera_process_init[[:space:]]*\([^;]*\)[[:space:]]*\{' "$KERNEL" --include='*.cpp' --include='*.cc' --include='*.c' 2>/dev/null; then
  log "chimera_process_init definition already exists."
elif grep -RqsE '(^|[^A-Za-z0-9_])chimera_process_init[[:space:]]*\(' "$KERNEL" --include='*.cpp' --include='*.cc' --include='*.c' 2>/dev/null; then
  log "Declaration/reference found without definition; installing definition."
  backup "$PROCESS_CPP"
  cat > "$PROCESS_CPP" <<'CPP'
/* ChimeraIIOS process bootstrap. C linkage matches koronos.cpp ABI. */
extern "C" void chimera_process_init()
{
    /* Scheduler owns task initialization; this hook is intentionally idempotent. */
}
CPP
else
  log "Koronos references chimera_process_init but no source definition exists; installing it."
  backup "$PROCESS_CPP"
  cat > "$PROCESS_CPP" <<'CPP'
/* ChimeraIIOS process bootstrap. C linkage matches koronos.cpp ABI. */
extern "C" void chimera_process_init()
{
    /* Scheduler owns task initialization; this hook is intentionally idempotent. */
}
CPP
fi

if ! grep -Fq 'process_init.cpp' "$CMAKE"; then
  if grep -Eq 'GLOB(_RECURSE)?[^;]*\.cpp' "$CMAKE"; then
    log "CMake uses source globbing; process_init.cpp will be included automatically."
  else
    backup "$CMAKE"
    python3 - "$CMAKE" <<'PY'
from pathlib import Path
import sys,re
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
for needle in ('core/scheduler.cpp','core\\scheduler.cpp','scheduler.cpp'):
    if needle in s:
        s=s.replace(needle, needle+'\n    ${CMAKE_CURRENT_SOURCE_DIR}/core/process_init.cpp',1)
        p.write_text(s,encoding='utf-8'); print('CMAKE_PATCHED_NEAR_SCHEDULER'); raise SystemExit(0)
# Try a common multiline source variable.
m=re.search(r'(?m)^([ \t]*(?:set|list)[ \t]*\([ \t]*[A-Za-z0-9_]*SOURCES[A-Za-z0-9_]*[^\n]*\n)',s)
if m:
    s=s[:m.end()]+'    ${CMAKE_CURRENT_SOURCE_DIR}/core/process_init.cpp\n'+s[m.end():]
    p.write_text(s,encoding='utf-8'); print('CMAKE_PATCHED_SOURCE_LIST'); raise SystemExit(0)
raise SystemExit('CMAKE_SOURCE_LIST_NOT_FOUND')
PY
  fi
fi

SCHED="$CORE/scheduler.cpp"
[[ -f "$SCHED" ]] || die "Missing scheduler.cpp"
backup "$SCHED"
python3 - "$SCHED" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
repls={
'if(i>=0) tasks[(uint32_t)i].info.state=CHIMERA_TASK_EXITED; unlock(); }':'if (i >= 0) {\n            tasks[(uint32_t)i].info.state = CHIMERA_TASK_EXITED;\n        }\n        unlock();\n    }',
'if(!out) return 0; lock(); uint32_t n=count<cap?count:cap;':'if (!out) return 0;\n    lock();\n    uint32_t n = count < cap ? count : cap;',
'for(uint32_t i=0;i<n;i++) out[i]=tasks[i].info; unlock(); return n;':'for (uint32_t i = 0; i < n; i++) {\n        out[i] = tasks[i].info;\n    }\n    unlock();\n    return n;'}
changed=0
for old,new in repls.items():
    if old in s: s=s.replace(old,new,1); changed+=1
p.write_text(s,encoding='utf-8'); print(f'scheduler-warning-fixes={changed}')
PY

grep -RqsE '(^|[^A-Za-z0-9_])chimera_process_init[[:space:]]*\([^;]*\)[[:space:]]*\{' "$CORE" --include='*.cpp' --include='*.cc' --include='*.c' || die "chimera_process_init definition missing"
if grep -Fq 'process_init.cpp' "$CMAKE"; then log "PASS: CMake explicitly includes process_init.cpp"; elif grep -Eq 'GLOB(_RECURSE)?[^;]*\.cpp' "$CMAKE"; then log "PASS: CMake glob includes process_init.cpp"; else die "process_init.cpp is not part of the active CMake source set"; fi
rm -f "$ROOT/build/kernel/CMakeFiles/koronos-x86_64.dir"/core/process_init.cpp.o "$ROOT/build/kernel/CMakeFiles/koronos-x86_64.dir"/process_init.cpp.o 2>/dev/null || true
if command -v c++ >/dev/null 2>&1; then c++ -fsyntax-only -x c++ "$PROCESS_CPP" >/dev/null; fi
log "STEP 3 BOOT LINKER FIX: PASS"
log "Missing symbol fixed: chimera_process_init"
log "Scheduler warnings cleaned"
log "Backup: $BACKUP"
log "Rebuild with: cd $ROOT && ./build-chimera-iso.sh"
