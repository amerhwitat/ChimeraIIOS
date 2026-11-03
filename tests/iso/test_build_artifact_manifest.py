#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "iso" / "build_artifact_manifest.py"

class ArtifactManifestTests(unittest.TestCase):
    def test_inventory_hashes_images_and_binaries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "iso"
            (root / "boot/grub").mkdir(parents=True)
            (root / "boot/koronos").mkdir(parents=True)
            (root / "boot/live").mkdir(parents=True)
            (root / "boot/recovery").mkdir(parents=True)
            (root / "install/installer").mkdir(parents=True)
            (root / "EFI/BOOT").mkdir(parents=True)
            payloads = {
                "boot/grub/grub.cfg": b"menuentry {}",
                "boot/koronos/koronos.elf": b"ELF",
                "boot/live/chimera-live-initramfs.img": b"LIVE",
                "boot/recovery/chimera-recovery-initramfs.img": b"RECOVERY",
                "install/installer/installation.img": b"INSTALLER",
                "EFI/BOOT/BOOTX64.EFI": b"MZ",
                "boot/spitfire/stage2.bin": b"SF2",
            }
            for name, data in payloads.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            manifest = root / "boot/artifact-manifest.json"
            checksums = root / "checksums/SHA256SUMS"
            subprocess.run([
                sys.executable, str(SCRIPT), "--root", str(root),
                "--manifest", str(manifest), "--checksums", str(checksums),
            ], check=True, capture_output=True, text=True)
            doc = json.loads(manifest.read_text())
            by_path = {item["path"]: item for item in doc["artifacts"]}
            self.assertEqual(doc["schema"], "CHIMERA-ISO-ARTIFACTS-1")
            self.assertEqual(doc["artifact_count"], len(payloads))
            self.assertEqual(by_path["boot/live/chimera-live-initramfs.img"]["kind"], "ram-disk-image")
            self.assertEqual(by_path["boot/spitfire/stage2.bin"]["kind"], "boot-binary")
            self.assertEqual(by_path["boot/koronos/koronos.elf"]["sha256"], hashlib.sha256(b"ELF").hexdigest())
            self.assertNotIn("boot/artifact-manifest.json", by_path)
            self.assertTrue(checksums.is_file())

    def test_missing_required_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "manifest.json"
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--root", str(root),
                "--manifest", str(manifest),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("required ISO artifacts missing", result.stderr)
            self.assertFalse(manifest.exists())

if __name__ == "__main__":
    unittest.main()
