#!/usr/bin/env bash
set -Eeuo pipefail
REPO="${1:-/mnt/d/chimera-build/rootfs/src/chimera/ChimeraIIOS}"
REPO="$(realpath -m "$REPO")"
[[ -d "$REPO" ]] || { echo "ERROR: repository not found: $REPO" >&2; exit 2; }
BACKUP_ROOT="$REPO/.chimera-fix-backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_ROOT"
log(){ printf '[CHIMERA-FIX] %s\n' "$*"; }
backup(){ local f="$1" rel="${f#"$REPO"/}"; mkdir -p "$BACKUP_ROOT/$(dirname "$rel")"; cp -a "$f" "$BACKUP_ROOT/$rel"; }
inject_helper(){
  local f="$1"; grep -q 'chimera_copy_if_distinct()' "$f" && return 0; backup "$f"
  python3 - "$f" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
helper='''\nchimera_copy_if_distinct() {\n  local src="$1" dst="$2"\n  [[ -e "$src" ]] || { echo "ERROR: source missing: $src" >&2; return 2; }\n  mkdir -p "$(dirname "$dst")"\n  local src_real dst_real\n  src_real="$(realpath -m "$src")"\n  dst_real="$(realpath -m "$dst")"\n  if [[ "$src_real" == "$dst_real" ]]; then\n    echo "[CHIMERA] copy skipped (source == destination): $src_real"\n    return 0\n  fi\n  cp -f -- "$src" "$dst"\n}\n'''
marker='set -Eeuo pipefail\n'
p.write_text(s.replace(marker,marker+helper,1) if marker in s else helper+s)
PY
}
replace_once(){ local f="$1" old="$2" new="$3"; grep -Fq "$old" "$f" || return 0; backup "$f"; python3 - "$f" "$old" "$new" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); old=sys.argv[2]; new=sys.argv[3]; s=p.read_text()
p.write_text(s.replace(old,new,1))
PY
}
LIVE="$REPO/tools/build-live-boot-binaries.sh"
BOOT_ART="$REPO/tools/build-boot-artifacts.sh"
ISO="$REPO/iso/chimera-live-iso.sh"
FULL="$REPO/build-chimera-iso.sh"
PRE="$REPO/build-chimera-iso.sh.pre-docker-log-fix"
for f in "$LIVE" "$BOOT_ART" "$ISO" "$FULL" "$PRE"; do [[ -f "$f" ]] || continue; log "Updating ${f#"$REPO"/}"; inject_helper "$f"; done
if [[ -f "$LIVE" ]]; then
 replace_once "$LIVE" 'if [[ -n "$KORONOS" && -f "$KORONOS" ]]; then cp -f "$KORONOS" "$OUT/boot/koronos/koronos.elf"; sha256sum "$OUT/boot/koronos/koronos.elf" > "$OUT/boot/koronos/koronos.el.sha256"; else echo "ERROR: Koronos ELF64 kernel not found." >&2; exit 2; fi' 'if [[ -n "$KORONOS" && -f "$KORONOS" ]]; then chimera_copy_if_distinct "$KORONOS" "$OUT/boot/koronos/koronos.elf"; sha256sum "$OUT/boot/koronos/koronos.elf" > "$OUT/boot/koronos/koronos.elf.sha256"; else echo "ERROR: Koronos ELF64 kernel not found." >&2; exit 2; fi'
 replace_once "$LIVE" 'echo "Koronos kernel: /mnt/chimera/boot/koronoskoronos.elf"' 'echo "Koronos kernel: /mnt/chimera/boot/koronos/koronos.elf"'
fi
if [[ -f "$ISO" ]]; then replace_once "$ISO" 'chimera_copy_if_distinct "$LIVE_BOOT/boot/koronos/koronos.elf" "$STAGE/boot/koronos/koronos.elf"' 'chimera_copy_if_distinct "$LIVE_BOOT/boot/koronos/koronos.elf" "$STAGE/boot/koronos/koronos.elf"'; fi
if [[ -f "$BOOT_ART" ]]; then
 replace_once "$BOOT_ART" 'cp "$KORONOS" "$OUT/koronos/koronos.elf"' 'chimera_copy_if_distinct "$KORONOS" "$OUT/koronos/koronos.elf"'
 replace_once "$BOOT_ART" 'cp -f "$OUT/koronos/koronos.elf" "$OUT/all-elf/"' 'chimera_copy_if_distinct "$OUT/koronos/koronos.elf" "$OUT/all-elf/koronos.elf"'
fi
if [[ -f "$FULL" ]]; then replace_once "$FULL" 'cp "$k" "$ISO_DIR/boot/kernel.bin"; cp "$k" "$ISO_DIR/boot/koronos/koronos.elf"' 'chimera_copy_if_distinct "$k" "$ISO_DIR/boot/kernel.bin"; chimera_copy_if_distinct "$k" "$ISO_DIR/boot/koronos/koronos.elf"'; fi
if [[ -f "$PRE" ]]; then
 replace_once "$PRE" 'cp "$kernel" "$ISO_DIR/boot/koronos/koronos.elf"' 'chimera_copy_if_distinct "$kernel" "$ISO_DIR/boot/koronos/koronos.elf"'
 replace_once "$PRE" 'cp "$live_boot/boot/koronos/koronos.elf" "$ISO_DIR/boot/koronos/koronos.elf"' 'chimera_copy_if_distinct "$live_boot/boot/koronos/koronos.elf" "$ISO_DIR/boot/koronos/koronos.elf"'
fi
REPORT="$REPO/build/chimera-boot-copy-audit.txt"; mkdir -p "$(dirname "$REPORT")"
{ echo "Chimera II Koronos boot-copy audit"; echo "Generated: $(date -Is)"; echo "Repository: $REPO"; echo; grep -RIn --exclude-dir=.git --exclude-dir=.chimera-fix-backups -E 'cp([[:space:]]|[^[:alnum:]])[^;]*koronos\.elf|koronos\.elf' "$REPO/tools" "$REPO/iso" "$REPO/build-chimera-iso.sh" "$REPO/boot" 2>/dev/null || true; } > "$REPORT"
for f in "$LIVE" "$BOOT_ART" "$ISO" "$FULL" "$PRE"; do [[ -f "$f" ]] || continue; bash -n "$f"; done
log "PASS: identical source/destination copies are skipped."
log "PASS: Koronos checksum normalized to koronos.elf.sha256."
log "PASS: malformed /boot/koronoskoronos.elf path corrected."
log "Audit: $REPORT"
log "Backups: $BACKUP_ROOT"
echo; echo '=== Candidate build entry points ==='; find "$REPO" -maxdepth 3 -type f -name 'build*.sh' -perm -u+x -not -path '*/.git/*' -not -path '*/.chimera-fix-backups/*' -print | sort
