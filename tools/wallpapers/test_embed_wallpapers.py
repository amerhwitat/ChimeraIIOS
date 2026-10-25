#!/usr/bin/env python3
"""Tests for offline wallpaper embedding; fixtures test the parser, not artwork."""
import tempfile
import unittest
from pathlib import Path

from embed_wallpapers import EXPECTED, generate, jpeg_dimensions


def fake_jpeg(width: int, height: int) -> bytes:
    # Minimal SOI + SOF0 frame segment + EOI fixture. The generator verifies
    # markers, segment bounds, and the declared dimensions without re-encoding.
    sof_payload = bytes([8]) + height.to_bytes(2, "big") + width.to_bytes(2, "big") + bytes([3, 1, 0x11, 0, 2, 0x11, 0, 3, 0x11, 0])
    segment = bytes([0xFF, 0xC0]) + (len(sof_payload) + 2).to_bytes(2, "big") + sof_payload
    return b"\\xff\\xd8" + segment + b"\\xff\\xd9"


class WallpaperEmbedContract(unittest.TestCase):
    def test_jpeg_dimensions(self):
        self.assertEqual(jpeg_dimensions(fake_jpeg(2048, 1152)), (2048, 1152))

    def test_generates_data_uri_css_and_hash_manifest_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "aurora-and-mountain.jpg").write_bytes(fake_jpeg(2048, 1152))
            (source / "octavian-marine-dual-brand.jpg").write_bytes(fake_jpeg(1672, 941))
            result = generate(source, root / "out.css", root / "out.json")
            css = (root / "out.css").read_text()
            manifest = (root / "out.json").read_text()
            self.assertIn("data:image/jpeg;base64,", css)
            self.assertIn(".aurora-wallpaper--default", css)
            self.assertIn(".marine-wallpaper--default", css)
            self.assertIn("background-size: cover", css)
            self.assertIn('"offline": true', manifest)
            self.assertEqual(len(result["wallpapers"]), 2)

    def test_missing_exact_source_fails_closed(self):
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
    unittest.main()
