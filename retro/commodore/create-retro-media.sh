#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/retro-media"
while (($#)); do case "$1" in --out) OUT="$(mkdir -p "$2" && cd "$2" && pwd)"; shift 2;; -h|--help) echo "Usage: $0 [--out DIRECTORY]"; exit 0;; *) echo "Unknown option: $1" >&2; exit 64;; esac; done
command -v xdftool >/dev/null || { echo "Install amitools for xdftool." >&2; exit 127; }
command -v c1541 >/dev/null || { echo "Install VICE tools for c1541." >&2; exit 127; }
mkdir -p "$OUT"; TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/README" <<'TXT'
CHIMERA RETRO STARTER MEDIA
Original docs/configuration only. No Kickstart, Workbench, commercial firmware or games included.
Set CHIMERA_KICKSTART_ROM to a legally obtained Kickstart ROM to launch Amiga machines.
TXT
for model in 500 2000 4000; do
  if [[ "$model" == 500 ]]; then label=CHIMERA-A500; profile="$ROOT/retro/commodore/profiles/amiga-a500.fs-uae"; disk="$OUT/CHIMERA-Amiga-500.adf"
  elif [[ "$model" == 2000 ]]; then label=CHIMERA-A2000; profile="$ROOT/retro/commodore/profiles/amiga-a2000.fs-uae"; disk="$OUT/CHIMERA-Amiga-2000.adf"
  else label=CHIMERA-A4000; profile="$ROOT/retro/commodore/profiles/amiga-a4000.fs-uae"; disk="$OUT/CHIMERA-Amiga-4000.adf"; fi
  cp "$profile" "$TMP/MACHINE.cfg"; rm -f "$disk"
  xdftool "$disk" format "$label" ffs + write "$TMP/README" + write "$TMP/MACHINE.cfg"
  xdftool "$disk" list > "$TMP/list-$model.txt"
  grep -q README "$TMP/list-$model.txt"; grep -q MACHINE.cfg "$TMP/list-$model.txt"
  test "$(stat -c %s "$disk")" -eq 901120
done
python3 "$ROOT/retro/commodore/create-c64-demo.py" --output "$TMP/CHIMERA.PRG"
D64="$OUT/CHIMERA-Commodore-64.d64"; rm -f "$D64"
c1541 -format "CHIMERA,01" d64 "$D64"
c1541 -attach "$D64" -write "$TMP/CHIMERA.PRG" CHIMERA
c1541 -attach "$D64" -list > "$TMP/c64-list.txt"; grep -qi CHIMERA "$TMP/c64-list.txt"
(cd "$OUT" && sha256sum CHIMERA-Amiga-500.adf CHIMERA-Amiga-2000.adf CHIMERA-Amiga-4000.adf CHIMERA-Commodore-64.d64 > SHA256SUMS)
echo "Retro media created and inspected:"; ls -lh "$OUT"/CHIMERA-*
