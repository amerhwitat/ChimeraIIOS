#!/usr/bin/env python3
"""Guard the production target-init build -> staging -> ISO handoff contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class TargetInitStagingContract(unittest.TestCase):
    def test_kernel_build_produces_all_production_target_elves(self):
        script = (ROOT / "kernel" / "build-koronos.sh").read_text(encoding="utf-8")
        self.assertIn('for target in live installer recovery; do', script)
        self.assertIn('kernel/targets/${target}_init.c', script)
        self.assertIn('target-init-${target}.elf', script)

    def test_live_boot_builder_stages_each_elf_as_multiboot_payload(self):
        script = (ROOT / "tools" / "build-live-boot-binaries.sh").read_text(encoding="utf-8")
        self.assertIn('TARGETS_OUT="$OUT/boot/targets"', script)
        self.assertIn('target_elf="$BUILD_DIR/koronos/x86_64/target-init-$target.elf"', script)
        self.assertIn('chimera_copy_if_distinct "$target_elf" "$TARGETS_OUT/target-init-$target.elf"', script)
        # The builder writes the checksum from inside TARGETS_OUT so that the
        # manifest is relocatable; validate that command and its later check
        # rather than requiring a host-absolute checksum filename.
        self.assertIn(
            '(cd "$TARGETS_OUT" && sha256sum "target-init-$target.elf" > "target-init-$target.elf.sha256")',
            script,
        )
        self.assertIn(
            '(cd "$TARGETS_OUT" && sha256sum --check "target-init-$target.elf.sha256")',
            script,
        )
        self.assertIn('for target in live installer recovery; do', script)
        self.assertIn('target-init-$target.elf', script)


if __name__ == "__main__":
    unittest.main()
