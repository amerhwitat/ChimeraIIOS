import hashlib, json, os
from pathlib import Path
import unittest

class RetroMediaArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ["CHIMERA_RETRO_MEDIA_DIR"])
        cls.manifest = json.loads((cls.root / "manifest.json").read_text(encoding="utf-8"))

    def test_expected_media_and_hashes(self):
        files = {item["file"]: item for item in self.manifest["artifacts"]}
        self.assertEqual(set(files), {"Chimera-Amiga-A500.adf", "Chimera-Amiga-A2000.adf",
                                     "Chimera-Commodore-C64-Starter.d64"})
        for name, item in files.items():
            data = (self.root / name).read_bytes()
            self.assertEqual(len(data), item["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])

    def test_amiga_adf_geometry_and_dos_types(self):
        a500 = (self.root / "Chimera-Amiga-A500.adf").read_bytes()
        a2000 = (self.root / "Chimera-Amiga-A2000.adf").read_bytes()
        self.assertEqual(len(a500), 901120)
        self.assertEqual(len(a2000), 901120)
        self.assertEqual(a500[:4], b"DOS\0")
        self.assertEqual(a2000[:4], b"DOS\1")

    def test_c64_d64_geometry(self):
        self.assertEqual((self.root / "Chimera-Commodore-C64-Starter.d64").stat().st_size, 174848)

if __name__ == "__main__":
    unittest.main()
