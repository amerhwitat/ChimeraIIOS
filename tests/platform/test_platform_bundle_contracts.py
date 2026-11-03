import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class PlatformBundleContracts(unittest.TestCase):
    def test_json_contracts_are_valid(self):
        for path in (
            "filesystems/runtime-capabilities.json",
            "network/runtime-stack-manifest.json",
            "kernel/arch/koronos-architecture-profiles.json",
            "sdk/third-party-sdk-manifest.json",
        ):
            with self.subTest(path=path):
                json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_native_koronos_vfs_is_not_overclaimed(self):
        data = json.loads((ROOT / "filesystems/runtime-capabilities.json").read_text())
        self.assertEqual(data["native_koronos"]["vfs"], "not-integrated")
        self.assertEqual(data["native_koronos"]["write_delete"], "not-available-until-VFS-backend-and-persistence-tests-pass")

    def test_media_and_sdk_scripts_parse(self):
        for path in ("tools/chimera-media-manager.sh", "tools/build-sdk-bundle.sh", "build-chimera-iso.sh"):
            subprocess.run(["bash", "-n", str(ROOT / path)], check=True)

    def test_iso_pipeline_has_sdk_and_media_stages(self):
        script = (ROOT / "build-chimera-iso.sh").read_text()
        self.assertIn("sdk) run_stage sdk stage_sdk_bundle", script)
        self.assertIn("media) run_stage media stage_storage_network_runtime", script)
        self.assertIn("tools/build-sdk-bundle.sh", script)
        self.assertIn("tools/build-desktop-binaries.sh", script)
        self.assertIn("chimera-desktop-shell.cpp", script)

    def test_architecture_boot_claims_are_bounded(self):
        data = json.loads((ROOT / "kernel/arch/koronos-architecture-profiles.json").read_text())
        by_id = {item["id"]: item for item in data["profiles"]}
        self.assertEqual(by_id["x86_64"]["status"], "current-boot-pipeline")
        self.assertEqual(by_id["aarch64"]["status"], "port-scaffold-only")
        self.assertEqual(by_id["riscv64"]["status"], "port-scaffold-only")

    def test_proprietary_apple_sdk_is_not_redistributed(self):
        data = json.loads((ROOT / "sdk/third-party-sdk-manifest.json").read_text())
        apple = next(item for item in data["sdks"] if item["id"] == "apple-macos-sdk")
        self.assertFalse(apple["redistribute"])
        self.assertEqual(apple["mode"], "external-local-only")


if __name__ == "__main__":
    unittest.main()
