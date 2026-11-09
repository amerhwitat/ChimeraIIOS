#!/usr/bin/env bash
set -euo pipefail
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
    rom="${CHIMERA_KICKSTART_ROM:-}"; [[ -n "$rom" && -f "$rom" ]] || { echo "Set CHIMERA_KICKSTART_ROM to a legally obtained Kickstart ROM." >&2; exit 78; }
    model=A500; [[ "$machine" == amiga-a2000 ]] && model=A2000
    if command -v fs-uae >/dev/null 2>&1; then
      cfg="$(mktemp --suffix=.fs-uae)"; trap 'rm -f "$cfg"' EXIT
      printf 'amiga_model = %s\nkickstart_file = %s\nfloppy_drive_0 = %s\n' "$model" "$rom" "$disk" > "$cfg"
      exec fs-uae "$cfg"
    fi
    core="${CHIMERA_PUAE_CORE:-}"
    [[ -n "$core" && -f "$core" ]] || core="$(find "$HOME/.local/share/retroarch/cores" /usr/lib/libretro /usr/lib64/libretro -name puae_libretro.so -print -quit 2>/dev/null || true)"
    if command -v retroarch >/dev/null 2>&1 && [[ -n "$core" && -f "$core" ]]; then exec retroarch -L "$core" "$disk"; fi
    echo "Install FS-UAE or RetroArch with PUAE." >&2; exit 127 ;;
  commodore-c64)
    if command -v x64sc >/dev/null 2>&1; then exec x64sc -autostart "$disk"; fi
    if command -v x64 >/dev/null 2>&1; then exec x64 -autostart "$disk"; fi
    if command -v mame >/dev/null 2>&1; then exec mame c64 -flop1 "$disk"; fi
    echo "Install VICE or MAME." >&2; exit 127 ;;
  *) echo "Unknown machine: $machine" >&2; exit 64 ;;
esac
