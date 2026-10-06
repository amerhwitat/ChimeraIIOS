#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${CHIMERA_ROOT:-/mnt/c/tmp/ChimeraIIOS}"
KERNEL="$ROOT/kernel"
SCHED="$KERNEL/core/scheduler.cpp"
BUILD="$ROOT/build/koronos/x86_64"
BACKUP="$ROOT/.chimera-step3-fix-backups/$(date +%Y%m%d-%H%M%S)"
log(){ printf '[CHIMERA-STEP3] %s\n' "$*"; }
die(){ printf '[CHIMERA-STEP3][ERROR] %s\n' "$*" >&2; exit 1; }
[[ -d "$ROOT" ]] || die "ChimeraIIOS root not found: $ROOT"
[[ -f "$SCHED" ]] || die "scheduler.cpp not found: $SCHED"
[[ -f "$KERNEL/build-koronos.sh" ]] || die "Missing $KERNEL/build-koronos.sh"
mkdir -p "$BACKUP"
cp -a -- "$SCHED" "$BACKUP/scheduler.cpp"
log "Backup: $BACKUP/scheduler.cpp"
python3 - "$SCHED" "$KERNEL" <<'PY'
from pathlib import Path
import re, sys
sched=Path(sys.argv[1]); kernel=Path(sys.argv[2]); s=sched.read_text(encoding='utf-8')
block=re.compile(r'\n?// ---------------------------------------------------------------------------\n// Koronos process bootstrap ABI\n// ---------------------------------------------------------------------------\n// koronos\\.cpp calls this C-ABI hook during early boot\\. scheduler\\.cpp is already\n// //?a linked Koronos translation unit, so defining the hook here guarantees the\n// //?symbol is emitted without relying on an additional CMake source entry\\.\nextern "C" void chimera_process_init\\(\\)\n\\{\n    // Process bootstrap is intentionally idempotent\\. Scheduler task state is\n    // initialized by the scheduler subsystem itself\\.\n\\}\n', re.M)
# More tolerant cleanup of every generated hook block.
block2=re.compile(r'\n?// ---------------------------------------------------------------------------\n// Koronos process bootstrap ABI\n// ---------------------------------------------------------------------------\n// koronos\.cpp calls this C-ABI hook during early boot\. scheduler\.cpp is already\n// a linked Koronos translation unit, so defining the hook here guarantees the\n// symbol is emitted without relying on an additional CMake source entry\.\nextern "C" void chimera_process_init\(\)\n\{\n    // Process bootstrap is intentionally idempotent\. Scheduler task state is\n    // initialized by the scheduler subsystem itself\.\n\}\n', re.M)
s=block2.sub('',s)
if not re.search(r'extern\s+"C"\s+void\s+chimera_process_init\s*\(\s*\)\s*\{',s):
    s=s.rstrip()+'''\n\n// ---------------------------------------------------------------------------\n// Koronos process bootstrap ABI\n// ---------------------------------------------------------------------------\n// koronos.cpp calls this C-ABI hook during early boot. scheduler.cpp is already\n// a linked Koronos translation unit, so defining the hook here guarantees the\n// symbol is emitted without relying on an additional CMake source entry.\nextern "C" void chimera_process_init()\n{\n    // Process bootstrap is intentionally idempotent. Scheduler task state is\n    // initialized by the scheduler subsystem itself.\n}\n'''
sched.write_text(s,encoding='utf-8')
defs=[]
for p in kernel.rglob('*.cpp'):
    t=p.read_text(encoding='utf-8',errors='ignore')
    if re.search(r'extern\s+"C"\s+void\s+chimera_process_init\s*\(\s*\)\s*\{',t): defs.append(str(p))
print('[CHIMERA-STEP3] process_init definitions:')
for d in defs: print('  '+d)
if len(defs)!=1: raise SystemExit(f'[CHIMERA-STEP3][ERROR] Expected exactly 1 C-ABI definition, found {len(defs)}')
PY
python3 - "$SCHED" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8')
fixes=[
('if(i>=0) tasks[(uint32_t)i].info.state=CHIMERA_TASK_EXITED; unlock(); }','if (i >= 0) {\n            tasks[(uint32_t)i].info.state = CHIMERA_TASK_EXITED;\n        }\n        unlock();\n    }'),
('if(!out) return 0; lock(); uint32_t n=count<cap?count:cap;','if (!out) return 0;\n    lock();\n    uint32_t n = count < cap ? count : cap;'),
('for(uint32_t i=0;i<n;i++) out[i]=tasks[i].info; unlock(); return n;','for (uint32_t i = 0; i < n; i++) {\n        out[i] = tasks[i].info;\n    }\n    unlock();\n    return n;')]
changed=0
for a,b in fixes:
    if a in s: s=s.replace(a,b,1); changed+=1
p.write_text(s,encoding='utf-8')
print(f'[CHIMERA-STEP3] scheduler warning fixes applied: {changed}/3')
PY
chmod +x "$KERNEL/build-koronos.sh"
log "Removing stale Koronos objects..."
find "$ROOT/build" -type f \( -name 'scheduler.o' -o -name 'scheduler.cpp.o' -o -name 'scheduler.cc.o' \) -print -delete 2>/dev/null || true
rm -f "$BUILD/koronos.elf" "$BUILD/koronos.o" 2>/dev/null || true
log "Rebuilding Koronos with the project's real include paths and flags..."
(cd "$KERNEL" && ./build-koronos.sh) || die "Koronos rebuild failed"
ELF="$BUILD/koronos.elf"
[[ -f "$ELF" ]] || die "Koronos ELF was not produced: $ELF"
OBJ="$(find "$ROOT/build" -type f \( -name 'scheduler.o' -o -name 'scheduler.cpp.o' -o -name 'scheduler.cc.o' \) -print -quit 2>/dev/null || true)"
[[ -n "$OBJ" && -f "$OBJ" ]] || die "Could not locate rebuilt scheduler object"
command -v nm >/dev/null 2>&1 || die "nm is required but was not found"
log "Checking scheduler object symbol..."
nm -C "$OBJ" | grep -Eq '[[:space:]]T[[:space:]]chimera_process_init$' || die "chimera_process_init is missing from $OBJ"
log "Checking final Koronos ELF symbol..."
nm -C "$ELF" | grep -Eq '[[:space:]]T[[:space:]]chimera_process_init$' || die "chimera_process_init is missing from $ELF"
log "============================================================"
log " STEP 3 LINKER REPAIR: PASS"
log "============================================================"
log "Source : $SCHED"
log "Object : $OBJ"
log "ELF    : $ELF"
log "Symbol : chimera_process_init [PRESENT]"
log "============================================================"
log "Now run:"
log "  cd $ROOT"
log "  ./build-chimera-iso.sh"
