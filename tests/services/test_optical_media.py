import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location(
    "mount_image", ROOT / "services/storage/mount-image.py"
)
mount_image = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mount_image)


class OpticalMediaTests(unittest.TestCase):
    def image(self, descriptor, sequence=None):
        # UDF recognition descriptors begin at sector 17. Allocate through
        # sector 32 so the fixture contains complete sectors, not a short
        # slice appended at EOF.
        data = bytearray(33 * 2048)
        data[16 * 2048] = 1
        data[16 * 2048 + 1:16 * 2048 + 6] = descriptor
        if sequence:
            data[17 * 2048 + 1:17 * 2048 + 6] = sequence
        handle = tempfile.NamedTemporaryFile(delete=False)
        handle.write(data)
        handle.close()
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        return handle.name

    def test_iso9660_descriptor(self):
        self.assertTrue(mount_image.validate_image(self.image(b"CD001")).is_file())

    def test_udf_recognition_sequence(self):
        self.assertTrue(
            mount_image.validate_image(self.image(b"BEA01", b"NSR02")).is_file()
        )

    def test_rejects_incomplete_udf_and_non_optical_devices(self):
        with self.assertRaises(ValueError):
            mount_image.validate_image(self.image(b"BEA01"))
        self.assertTrue(mount_image.valid_optical_device("/dev/sr0"))
        self.assertFalse(mount_image.valid_optical_device("/dev/sda"))


if __name__ == "__main__":
    unittest.main()
