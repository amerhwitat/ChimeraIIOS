"""Ensure every ISO builder stages the exact ring-3 init modules GRUB requests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class TargetInitStagingTests(unittest.TestCase):
    def test_all_iso_builders_stage_live_installer_and_recovery_inits(self):
        for relative in (
            "tools/build-full-iso.sh",
            "iso/chimera-live-iso.sh",
            "boot/iso/prepare-layout.sh",
        ):
            with self.subTest(builder=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("for target in live installer recovery", content)
                self.assertIn("target-init-$target.elf", content)
                self.assertIn("boot/targets", content)
                self.assertIn("Type:[[:space:]]+EXEC", content)
                self.assertIn("readelf -lW", content)

    def test_canonical_grub_menu_requests_matching_init_modules(self):
        grub = (ROOT / "boot/iso/grub.cfg").read_text(encoding="utf-8")
        for target in ("live", "installer", "recovery"):
            with self.subTest(target=target):
                self.assertIn(
                    f"module2 /boot/targets/target-init-{target}.elf chimera-user-init-elf target={target}",
                    grub,
                )

    def test_qemu_acceptance_extracts_and_loads_the_target_init_module(self):
        workflow = (ROOT / ".github/workflows/chimera-full-iso.yml").read_text(encoding="utf-8")
        self.assertIn('extract "/boot/targets/target-init-$target.elf"', workflow)
        self.assertIn('module2 /boot/targets/target-init-$target.elf chimera-user-init-elf target=$target', workflow)
        self.assertIn("readelf -lW", workflow)


if __name__ == "__main__":
    unittest.main()
