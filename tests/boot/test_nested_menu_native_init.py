#!/usr/bin/env python3
"""Static contract: every nested Koronos boot entry passes one production target-init ELF."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
MENU_FILES = (
    "boot/iso/grub.cfg",
    "boot/jasper/jasper.cfg",
    "boot/jasper/live.cfg",
    "boot/jasper/install.cfg",
    "boot/jasper/recovery.cfg",
    "boot/jasper/diagnostics.cfg",
    "boot/jasper/retro.cfg",
    "boot/installation/menu.cfg",
    "boot/spitfire/spitfire-menu.cfg",
)
INIT_MODULE = re.compile(
    r"(?m)^[ \t]*module2[ \t]+/boot/targets/target-init-(live|installer|recovery)\.elf"
    r"[ \t]+chimera-user-init-elf[ \t]+target=(live|installer|recovery)"
    r"[ \t]+firmware=\$grub_platform[ \t]*$"
)


class NestedMenuNativeInitContract(unittest.TestCase):
    def test_all_menus_remain_visible_and_require_selection(self):
        for relative in MENU_FILES:
            with self.subTest(menu=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertRegex(content, r"(?m)^set timeout=120$")
                self.assertRegex(content, r"(?m)^set timeout_style=menu$")

    def test_every_kernel_menu_entry_has_one_matching_native_init(self):
        checked = 0
        for relative in MENU_FILES:
            content = (ROOT / relative).read_text(encoding="utf-8")
            blocks = re.findall(
                r"(?ms)^menuentry\b[^{]*\{(.*?)(?=^menuentry\b|\Z)",
                content,
            )
            for index, block in enumerate(blocks, 1):
                if "multiboot2 /boot/koronos/koronos.elf" not in block:
                    continue
                checked += 1
                matches = INIT_MODULE.findall(block)
                self.assertEqual(
                    len(matches),
                    1,
                    f"{relative} menuentry {index} must pass exactly one native target-init ELF",
                )
                self.assertEqual(
                    matches[0][0],
                    matches[0][1],
                    f"{relative} menuentry {index} target name must match its ELF",
                )
        self.assertGreater(checked, 0, "no Koronos menu entries were checked")

    def test_iso_builder_stages_all_production_target_inits(self):
        builder = (ROOT / "boot/iso/build-iso.sh").read_text(encoding="utf-8")
        self.assertIn("for target in live installer recovery; do", builder)
        self.assertIn(
            'target_elf="$ROOT/build/koronos/x86_64/target-init-$target.elf"',
            builder,
        )
        self.assertIn('cp -f "$target_elf" "$TARGETS_OUT/"', builder)


if __name__ == "__main__":
    unittest.main()
