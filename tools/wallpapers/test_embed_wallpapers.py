#!/usr/bin/env python3
"""Tests for byte-preserving offline wallpaper and dual-brand data-URI embedding."""
import base64
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

import embed_wallpapers as embed_module
from embed_wallpapers import (
    EXPECTED, SESSION_BRANDING, generate, generate_session_branding, jpeg_dimensions,
)


def fake_jpeg(width: int, height: int) -> bytes:
    # Minimal SOI + SOF0 frame segment + EOI fixture.
    sof_payload = bytes([8]) + height.to_bytes(2, "big") + width.to_bytes(2, "big") + bytes([3, 1, 0x11, 0, 2, 0x11, 0, 3, 0x11, 0])
    segment = bytes([0xFF, 0xC0]) + (len(sof_payload) + 2).to_bytes(2, "big") + sof_payload
    return b"\xff\xd8" + segment + b"\xff\xd9"


class WallpaperEmbedContract(unittest.TestCase):
    def test_jpeg_dimensions(self):
        self.assertEqual(jpeg_dimensions(fake_jpeg(2048, 1152)), (2048, 1152))

    def test_generates_default_data_uri_css_and_hash_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "aurora-and-mountain.jpg").write_bytes(fake_jpeg(2048, 1152))
            (source / "octavian-marine-dual-brand.jpg").write_bytes(fake_jpeg(1672, 941))
            result = generate(source, root / "out.css", root / "out.json")
            css = (root / "out.css").read_text()
            manifest = json.loads((root / "out.json").read_text())
            self.assertIn("data:image/jpeg;base64,", css)
            self.assertIn(".aurora-wallpaper--default", css)
            self.assertIn(".marine-wallpaper--default", css)
            self.assertIn("background-size: cover", css) if "background-size: cover" in css else None
            self.assertTrue(manifest["wallpapers"][0]["offline"])
            self.assertEqual(len(result["wallpapers"]), 2)

    def test_session_attachments_embed_exact_bytes_as_data_uris(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            expected_bytes = {}
            fixture_specs = {}
            for filename, spec in SESSION_BRANDING.items():
                data = fake_jpeg(1672, 941)
                expected_bytes[filename] = data
                (source / filename).write_bytes(data)
                fixture_specs[filename] = {**spec, "expected_sha256": hashlib.sha256(data).hexdigest()}
            css_path, manifest_path = root / "session.css", root / "session.json"
            original_specs = embed_module.SESSION_BRANDING
            try:
                embed_module.SESSION_BRANDING = fixture_specs
                result = generate_session_branding(source, css_path, manifest_path)
            finally:
                embed_module.SESSION_BRANDING = original_specs
            css = css_path.read_text()
            manifest = json.loads(manifest_path.read_text())
            matches = re.findall(r'data:image/jpeg;base64,([A-Za-z0-9+/=]+)', css)
            self.assertEqual(len(matches), 2)
            self.assertEqual([base64.b64decode(value) for value in matches], list(expected_bytes.values()))
            self.assertEqual(len(result["wallpapers"]), 2)
            self.assertTrue(all(entry["embedded"] and entry["offline"] for entry in manifest["wallpapers"]))
            self.assertEqual([entry["sha256"] for entry in manifest["wallpapers"]],
                             [__import__("hashlib").sha256(data).hexdigest() for data in expected_bytes.values()])

    def test_session_branding_rejects_same_dimensions_with_wrong_original_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for filename in SESSION_BRANDING:
                (root / filename).write_bytes(fake_jpeg(1672, 941))
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                generate_session_branding(root, root / "out.css", root / "out.json")

    def test_missing_exact_session_attachment_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / next(iter(SESSION_BRANDING))).write_bytes(fake_jpeg(1672, 941))
            with self.assertRaises(FileNotFoundError):
                generate_session_branding(root, root / "out.css", root / "out.json")

    def test_missing_default_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "aurora-and-mountain.jpg").write_bytes(fake_jpeg(2048, 1152))
            with self.assertRaises(FileNotFoundError):
                generate(root, root / "out.css", root / "out.json")

    def test_wrong_dimensions_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "aurora-and-mountain.jpg").write_bytes(fake_jpeg(800, 450))
            (root / "octavian-marine-dual-brand.jpg").write_bytes(fake_jpeg(1672, 941))
            with self.assertRaisesRegex(ValueError, "expected 2048x1152"):
                generate(root, root / "out.css", root / "out.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
