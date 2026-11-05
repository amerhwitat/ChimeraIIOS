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

    def test_target_rootfs_builder_installs_graphics_and_webgl_runtime(self):
        builder_path = ROOT / "live-image" / "build.sh"
        self.assertTrue(builder_path.is_file())
        builder = builder_path.read_text(encoding="utf-8")
        for package in (
            "libgl1", "libglx-mesa0", "libegl1", "libgles2", "libgbm1",
            "libgl1-mesa-dri", "libwayland-egl1", "libdrm2", "mesa-utils",
            "mesa-vulkan-drivers", "firefox-esr",
        ):
            self.assertIn(package, builder)
        self.assertIn(".packages-installed-graphics-v2", builder)
        self.assertIn("glxinfo -B", builder)
        self.assertIn("if ! compgen -G '/dev/dri/renderD*'", builder)

        # When this test runs in OctavianOS's vendored source tree, also
        # validate the outer Octavian live-image builder.
        octavian_builder_path = ROOT.parents[2] / "live-image" / "build.sh"
        if octavian_builder_path.is_file():
            octavian_builder = octavian_builder_path.read_text(encoding="utf-8")
            for package in (
                "libgl1", "libglx-mesa0", "libegl1", "libgles2", "libgbm1",
                "libgl1-mesa-dri", "libwayland-egl1", "libdrm2", "mesa-utils",
                "mesa-vulkan-drivers", "firefox-esr",
            ):
                self.assertIn(package, octavian_builder)
            self.assertIn(".packages-installed-graphics-v2", octavian_builder)

    def test_architecture_listing_is_not_support_claim(self):
        arch = self.data["architecture_policy"]
        self.assertIn("x86_64", arch["architectures"])
        self.assertIn("aarch64", arch["architectures"])
        self.assertIn("not support certification", arch["rule"])


if __name__ == "__main__":
    unittest.main()
