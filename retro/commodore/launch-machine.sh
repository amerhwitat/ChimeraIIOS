#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
usage(){ cat <<'EOF'
Usage: launch-machine.sh amiga-a500|amiga-a2000 DISK.adf
       launch-machine.sh commodore-c64 DISK.d64
Set CHIMERA_KICKSTART_ROM to a legally obtained Amiga Kickstart ROM.
EOF
}
if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then usage; exit 0; fi
[[ $# -ge 2 ]] || { usage >&2; exit 64; }
machine="$1"; disk="$(realpath "$2")"; [[ -f "$disk" ]] || { echo "Disk not found: $disk" >&2; exit 66; }
case "$machine" in
  amiga-a500|amiga-a2000)
    rom="${CHIMERA_KICKSTART_ROM:-}"
    if [[ -n "$rom" && ! -f "$rom" ]]; then echo "CHIMERA_KICKSTART_ROM does not point to a file." >&2; exit 66; fi
    model=A500; [[ "$machine" == amiga-a2000 ]] && model=A2000
    if [[ -n "$rom" ]] && command -v fs-uae >/dev/null 2>&1; then
      cfg="$(mktemp --suffix=.fs-uae)"; trap 'rm -f "$cfg"' EXIT
      printf 'amiga_model = %s\nkickstart_file = %s\nfloppy_drive_0 = %s\n' "$model" "$rom" "$disk" > "$cfg"
      exec fs-uae "$cfg"
    fi
    core="${CHIMERA_PUAE_CORE:-}"
    if [[ -z "$core" ]]; then
      for candidate in "$ROOT/build/retro-emulators/puae_libretro.so" /usr/lib/chimera/retro/emulators/puae_libretro.so /usr/lib/octavian/retro/emulators/puae_libretro.so /usr/lib/libretro/puae_libretro.so /usr/lib64/libretro/puae_libretro.so; do
        [[ -f "$candidate" ]] && { core="$candidate"; break; }
      done
    fi
    [[ -f "$core" ]] || core="$(find "$HOME/.local/share/retroarch/cores" -name puae_libretro.so -print -quit 2>/dev/null || true)"
    if command -v retroarch >/dev/null 2>&1 && [[ -n "$core" && -f "$core" ]]; then
      cfg="$(mktemp)"
      trap 'rm -f "$cfg"' EXIT
      if [[ -n "$rom" ]]; then
        printf 'system_directory = "%s"\npuae_model = "%s"\npuae_kickstart = "auto"\n' "$(dirname "$rom")" "$model" > "$cfg"
      else
        printf 'puae_model = "%s"\npuae_kickstart = "aros"\n' "$model" > "$cfg"
      fi
      retroarch --appendconfig "$cfg" -L "$core" "$disk"
      exit $?
    fi
    echo "Install FS-UAE or RetroArch with PUAE (PUAE can use its built-in AROS replacement if no Kickstart ROM is supplied)." >&2; exit 127 ;;
  commodore-c64)
    for candidate in "$ROOT/build/retro-emulators/x64sc" /usr/lib/chimera/retro/emulators/x64sc /usr/lib/octavian/retro/emulators/x64sc; do
      [[ -x "$candidate" ]] && exec "$candidate" -autostart "$disk"
    done
    if command -v x64sc >/dev/null 2>&1; then exec x64sc -autostart "$disk"; fi
    if command -v x64 >/dev/null 2>&1; then exec x64 -autostart "$disk"; fi
    if command -v mame >/dev/null 2>&1; then exec mame c64 -flop1 "$disk"; fi
    echo "Install VICE or MAME." >&2; exit 127 ;;
  *) echo "Unknown machine: $machine" >&2; exit 64 ;;
esac
