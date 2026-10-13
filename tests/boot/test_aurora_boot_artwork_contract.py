from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MENU_FILES = [
    "boot/iso/grub.cfg",
    "boot/jasper/jasper.cfg",
    "boot/jasper/live.cfg",
    "boot/jasper/install.cfg",
    "boot/jasper/recovery.cfg",
    "boot/jasper/diagnostics.cfg",
    "boot/jasper/retro.cfg",
    "boot/spitfire/spitfire-menu.cfg",
]

def test_shared_theme_asset_is_staged_for_all_menu_layers():
    theme = (ROOT / "boot/grub/aurora-theme.txt").read_text(encoding="utf-8")
    assert 'desktop-image: "/boot/visual/aurora-menu.png"' in theme
    builder = (ROOT / "boot/iso/build-iso.sh").read_text(encoding="utf-8")
    assert 'cp -f "$MEDIA/menus/default.png" "$VISUAL_OUT/aurora-menu.png"' in builder
    assert 'cp -f "$ROOT/boot/grub/aurora-theme.txt" "$DIST/boot/grub/aurora-theme.txt"' in (ROOT / "boot/iso/prepare-layout.sh").read_text(encoding="utf-8")

def test_all_menu_layers_preserve_graphics_and_load_shared_theme_or_fallback():
    for relative in MENU_FILES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "set gfxpayload=keep" in text, f"{relative} does not preserve the graphics payload"
        assert "terminal_output gfxterm" in text, f"{relative} does not use the graphical terminal"
        assert "/boot/grub/aurora-theme.txt" in text or "/boot/visual/aurora-menu.png" in text, f"{relative} has no shared Aurora theme/fallback"

def test_ring3_probe_is_not_attached_to_normal_boot_entries():
    grub = (ROOT / "boot/iso/grub.cfg").read_text(encoding="utf-8")
    probe = 'menuentry "Chimera II OS — Native ELF Ring-3 Acceptance Probe" --id ring3-acceptance {'
    assert probe in grub
    assert grub.count("module2 /boot/koronos/chimera-user-init.elf chimera-user-init-elf") == 1
    probe_start = grub.index(probe)
    probe_end = grub.index("\n}", probe_start)
    assert "module2 /boot/koronos/chimera-user-init.elf chimera-user-init-elf" in grub[probe_start:probe_end]
