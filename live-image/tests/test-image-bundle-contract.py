#!/usr/bin/env python3
"""Static acceptance for the shared Aurora/Spit Fire live-image contracts."""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
builder = (root / "live-image/build.sh").read_text()
grub = (root / "boot/iso/grub.cfg").read_text()
spitfire = (root / "boot/spitfire/spitfire-menu.cfg").read_text()

required_builder = [
    'AURORA_SOURCE="$REPO_DIR/desktop/aurora"',
    'vendor/chimera-ii-os/source/desktop/aurora',
    "optional_ide_packages=(qtcreator codeblocks eclipse-platform eric spyder gambas3-ide arduino fp-ide)",
    'apt-cache show "$package"',
    'ide-packages-installed.tsv',
    'install -m 0644 "$PAY/wallpapers/wp01.jpg" "$WORK/usr/share/backgrounds/aurora-default.jpg"',
    'CHIMERA_SPLASH_MAX_SECONDS=12',
    'CHIMERA_INIT_VIDEO=/usr/share/chimera/aurora/assets/Init.mp4',
]
for token in required_builder:
    if token not in builder:
        raise SystemExit(f"FAIL: live-image builder missing contract: {token}")

session_start = builder.find('cat > "$WORK/usr/local/bin/aurora-session"')
session_end = builder.find("\nEOF", session_start)
if session_start < 0 or session_end < 0:
    raise SystemExit("FAIL: generated Aurora session script is missing")
session = builder[session_start:session_end]
splash = session.find("/usr/local/bin/aurora-init-splash.sh")
kiosk = session.find("exec /usr/bin/python3 /usr/local/bin/aurora-kiosk.py")
if splash < 0 or kiosk < 0 or splash > kiosk:
    raise SystemExit("FAIL: Init.mp4 splash must run before the Aurora kiosk")

if "AURORA_DESKTOP_URI=" not in builder or 'test -s "$PAY/$ENTRY"' not in builder:
    raise SystemExit("FAIL: edition-specific desktop URI/page validation is missing")
if "background_image --mode stretch" not in grub:
    raise SystemExit("FAIL: Jasper/GRUB background selection is missing")
if "Native Installer" not in spitfire or "Native Recovery" not in spitfire:
    raise SystemExit("FAIL: Spit Fire menu is missing native handoff choices")
if "installer-initrd.img" not in spitfire or "chimera-recovery-initramfs.img" not in spitfire:
    raise SystemExit("FAIL: Spit Fire native handoffs must check their runtime images")
if "Init.mp4" not in grub or "userspace playback" not in grub:
    raise SystemExit("FAIL: GRUB must document post-selection userspace splash playback")
print("PASS: Aurora launcher, embedded wallpaper, IDE bundle, Spit Fire menu and splash contracts")
