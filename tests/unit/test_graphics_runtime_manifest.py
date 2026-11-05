#!/usr/bin/env python3
"""Validate the target graphics runtime package plan without claiming installation."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "graphics" / "graphics-runtime.json"


class GraphicsRuntimeManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_scope_is_target_rootfs_and_not_certified(self):
        self.assertEqual(self.data["scope"], "target-rootfs-package-plan")
        self.assertEqual(self.data["status"], "requested_not_runtime_certified")

    def test_native_opengl_runtime_dependencies_are_present(self):
        gl = self.data["native_opengl"]
        self.assertIn("libGL", gl["required_runtime_capabilities"])
        self.assertIn("libEGL", gl["required_runtime_capabilities"])
        packages = set(gl["debian_ubuntu_packages"])
        self.assertTrue({"libgl1", "libegl1", "libgles2", "libgbm1"} <= packages)

    def test_webgl_requires_real_webgl2_acceptance(self):
        web = self.data["webgl"]
        self.assertTrue(web["requires_browser_or_embedded_web_runtime"])
        self.assertIn("browser_reports_webgl2_available", web["acceptance"])
        self.assertIn("context_loss_and_restoration_test_passes", web["acceptance"])
        self.assertEqual(web["browser_selection"], "install_one_available_signed_candidate; do_not_require_both")

    def test_target_installation_never_uses_host_root(self):
        policy = self.data["policy"]
        self.assertTrue(policy["never_copy_host_libraries_into_target"])
        self.assertTrue(policy["verify_repository_signatures"])
        self.assertTrue(self.data["distribution_adapters"]["debian_ubuntu"]["must_not_use_host_root"])

    def test_architecture_listing_is_not_support_claim(self):
        arch = self.data["architecture_policy"]
        self.assertIn("x86_64", arch["architectures"])
        self.assertIn("aarch64", arch["architectures"])
        self.assertIn("not support certification", arch["rule"])


if __name__ == "__main__":
    unittest.main()
