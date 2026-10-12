from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "build-chimera-iso.sh"


class BuildPipelineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = BUILDER.read_text(encoding="utf-8")

    def test_resume_order_matches_actual_stage_loop(self):
        order_match = re.search(r"local order='([^']+)'", self.script)
        loop_match = re.search(r"for stage in (docker rootfs commands docker-publish boot installer branding apache features package-managers games squashfs iso verify native-iso report); do", self.script)
        self.assertIsNotNone(order_match, "state resume order is missing")
        self.assertIsNotNone(loop_match, "build stage loop is missing")
        self.assertEqual(order_match.group(1).split(), loop_match.group(1).split())

    def test_docker_only_has_dedicated_early_path(self):
        self.assertIn('if [[ "$BUILD_ISO" == 0 ]]; then', self.script)
        self.assertIn('run_stage docker build_docker', self.script)
        self.assertIn('run_stage docker-publish push_docker_image', self.script)
        self.assertIn('Docker-only pipeline completed.', self.script)

    def test_iso_only_checks_image_and_skips_build_and_publish(self):
        self.assertIn('--iso-only requires an existing Docker image:', self.script)
        self.assertIn('Skipping Docker build for --iso-only', self.script)
        self.assertIn('Skipping Docker publish for --iso-only', self.script)

    def test_rootfs_is_exported_once_by_the_named_container_path(self):
        self.assertIn('docker export "$cname"', self.script)
        self.assertNotIn('chimera_export_docker_rootfs "$DOCKER_IMAGE:$DOCKER_TAG"', self.script)

    def test_optional_isa_research_uses_defined_logger(self):
        self.assertNotRegex(self.script, r"\blog_warn\s")
        self.assertIn('log_warning "Online ISA research failed;', self.script)

    def test_discovery_worker_is_staged_for_runtime(self):
        self.assertIn('tools/architecture_discovery/chimera_discovery.py', self.script)
        self.assertIn('packaging/systemd/user/chimera-architecture-discovery.timer', self.script)
        self.assertIn('Staged Aurora architecture/ISA discovery worker', self.script)

    def test_qemu_timeout_is_not_reported_as_boot_success(self):
        self.assertIn("no boot milestone was asserted", self.script)
        self.assertIn('qemu-firmware-probe.log', self.script)
        self.assertNotIn('qemu-system-x86_64 -accel tcg -m 512 -cdrom "$iso" -display none -serial none -monitor none -no-reboot -no-shutdown >/dev/null 2>&1 || true', self.script)

    def test_discovery_uses_final_selected_build_directory(self):
        storage_check = self.script.index('if ((rg<20 || og<20)); then')
        discovery_call = self.script.index('tools/architecture_discovery/chimera_discovery.py')
        self.assertGreater(discovery_call, storage_check)


if __name__ == "__main__":
    unittest.main()
