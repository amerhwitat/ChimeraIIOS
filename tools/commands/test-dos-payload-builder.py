#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).with_name("dos-payload-builder.py")
spec = importlib.util.spec_from_file_location("dos_payload_builder", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class DosPayloadBuilderTests(unittest.TestCase):
    def test_cataloged_entries_never_qualify(self):
        self.assertFalse(mod.valid_payload({
            "id": "demo", "status": "cataloged", "license_reviewed": False,
            "redistributable": False, "smoke_tested": False, "license": "unknown",
            "sha256": "0" * 64, "package_url": "https://www.ibiblio.org/demo.zip", "format": "zip"
        }))

    def test_only_fully_reviewed_pinned_entries_qualify(self):
        item = {"id":"demo","status":"smoke-tested","license_reviewed":True,
                "redistributable":True,"smoke_tested":True,"license":"GPL-2.0-or-later",
                "sha256":"a"*64,"package_url":"https://www.ibiblio.org/demo.zip","format":"zip"}
        self.assertTrue(mod.valid_payload(item))
        item["package_url"] = "http://www.ibiblio.org/demo.zip"
        self.assertFalse(mod.valid_payload(item))

    def test_archive_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("../escape.exe", b"bad")
            with self.assertRaises(ValueError):
                mod.safe_extract(archive, Path(tmp) / "out")

    def test_stage_default_manifest_adds_catalog_without_binaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"bundled_titles": [], "cataloged_titles": [{
                "id":"old-game","status":"cataloged","binary_included":False
            }]}))
            self.assertEqual(mod.stage(manifest, root/"cache", root/"dest", False), 0)
            result = json.loads((root/"dest"/"CATALOG.json").read_text())
            self.assertEqual(result["included_payload_count"], 0)

if __name__ == "__main__":
    unittest.main()
