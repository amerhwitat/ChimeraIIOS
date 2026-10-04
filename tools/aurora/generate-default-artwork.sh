#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/aurora/generate-default-artwork.sh

Usage:
  tools/aurora/generate-default-artwork.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
OUT="${1:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/../../build/aurora-default-artwork}"
mkdir -p "$OUT"
write_svg() {
  local file="$1" title="$2" subtitle="$3" accent="$4"
  cat > "$OUT/$file.svg" <<EOF
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#030914"/><stop offset=".46" stop-color="#0b2038"/><stop offset="1" stop-color="#02050b"/></linearGradient>
    <radialGradient id="glow"><stop stop-color="${accent}" stop-opacity=".52"/><stop offset="1" stop-color="${accent}" stop-opacity="0"/></radialGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop stop-color="${accent}" stop-opacity="0"/><stop offset=".5" stop-color="${accent}" stop-opacity=".85"/><stop offset="1" stop-color="${accent}" stop-opacity="0"/></linearGradient>
  </defs>
  <rect width="1920" height="1080" fill="url(#bg)"/>
  <circle cx="380" cy="210" r="520" fill="url(#glow)"/><circle cx="1570" cy="850" r="650" fill="url(#glow)"/>
  <path d="M0 780 C360 570 650 1010 1040 760 S1570 590 1920 760" fill="none" stroke="${accent}" stroke-opacity=".22" stroke-width="2"/>
  <path d="M0 830 C390 640 680 1035 1070 800 S1590 650 1920 810" fill="none" stroke="#e8fbff" stroke-opacity=".09"/>
  <path d="M180 140 H1740 M180 940 H1740" stroke="url(#line)" stroke-width="2"/>
  <g fill="#bdefff" opacity=".22"><circle cx="220" cy="240" r="2"/><circle cx="320" cy="350" r="2"/><circle cx="1680" cy="300" r="2"/><circle cx="1530" cy="210" r="2"/><circle cx="1760" cy="690" r="2"/><circle cx="470" cy="850" r="2"/></g>
  <text x="960" y="470" text-anchor="middle" fill="#f4fdff" font-family="sans-serif" font-size="74" font-weight="700" letter-spacing="9">${title}</text>
  <text x="960" y="535" text-anchor="middle" fill="${accent}" font-family="sans-serif" font-size="27" letter-spacing="7">${subtitle}</text>
</svg>
EOF
}
write_svg aurora-boot "CHIMERA II OS" "AURORA BOOT" "#62e8ff"
write_svg aurora-splash "CHIMERA II OS" "AURORA INITIALIZING" "#76f3d0"
write_svg aurora-menu "CHIMERA II OS" "AURORA BOOT MENU" "#a6b8ff"
write_svg aurora-installer "CHIMERA II OS" "AURORA INSTALLER" "#ffcf70"
write_svg aurora-recovery "CHIMERA II OS" "AURORA RECOVERY" "#ff8fa3"
write_svg aurora-diagnostics "CHIMERA II OS" "AURORA DIAGNOSTICS" "#d3a7ff"
write_svg aurora-live "CHIMERA II OS" "AURORA LIVE ENVIRONMENT" "#70eaff"
write_svg aurora-mobile "CHIMERA II OS" "AURORA MOBILE EDITION" "#75e6a5"
write_svg aurora-desktop "CHIMERA II OS" "AURORA DESKTOP" "#68dfff"
cat > "$OUT/manifest.json" <<EOF
{"schema":"CHIMERA-AURORA-ARTWORK-1","generated":true,"resolution":"1920x1080","assets":["aurora-boot.svg","aurora-splash.svg","aurora-menu.svg","aurora-installer.svg","aurora-recovery.svg","aurora-diagnostics.svg","aurora-live.svg","aurora-mobile.svg","aurora-desktop.svg"]}
EOF
printf '[INFO] Generated deterministic Aurora fallback artwork in %s\n' "$OUT"
