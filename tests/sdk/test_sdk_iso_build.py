import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class SDKIsoBuildContract(unittest.TestCase):
    def test_iso_pipeline_runs_sdk_after_rootfs(self):
        script = (ROOT / "build-chimera-iso.sh").read_text()
        self.assertIn("for stage in docker rootfs commands sdk docker-publish", script)
        self.assertIn("sdk) run_stage sdk build_sdk;;", script)
        self.assertIn('CHIMERA_SDK_DESTDIR="$ROOTFS_DIR"', script)

    def test_sdk_build_is_its_own_cmake_project_and_runs_tests(self):
        script = (ROOT / "sdk/tools/build-sdk.sh").read_text()
        self.assertIn('cmake -S "$ROOT"', script)
        self.assertIn("ctest --test-dir", script)
        self.assertIn("cmake --install", script)
        self.assertIn("cargo test", script)
        validator = (ROOT / "boot/iso/validate-iso.py").read_text()
        layout = (ROOT / "boot/iso/prepare-layout.sh").read_text()
        self.assertIn("SDK_ROOTFS", layout)
        self.assertIn("sdk/tools/build-sdk.sh", layout)
        self.assertIn("boot/gates/gates.cfg", validator)
        self.assertIn("boot/gates/gates.cfg", layout)
        self.assertIn("opt/chimera-sdk/include/chimera/sdk.h", validator)
        self.assertIn("python3 -m compileall", script)
        self.assertIn("CARGO_TARGET_DIR", script)
        self.assertIn("CHIMERA_SDK_JAVA_BUILD_DIR", script)

    def test_rust_sdk_lockfile_is_present(self):
        lock = ROOT / "sdk/rust/chimera-runtime/Cargo.lock"
        self.assertTrue(lock.is_file())
        self.assertIn('name = "chimera-runtime"', lock.read_text())

if __name__ == "__main__":
    unittest.main()
