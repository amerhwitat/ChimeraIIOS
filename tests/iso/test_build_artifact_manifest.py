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

    def test_native_build_stages_use_the_selected_build_directory(self):
        root = Path(__file__).resolve().parents[2]
        expected = {
            "kernel/build-koronos.sh": 'BUILD="${CHIMERA_BUILD_DIR:-$ROOT/build}/koronos/x86_64"',
            "tools/build-boot-artifacts.sh": 'BUILD_DIR="${CHIMERA_BUILD_DIR:-$ROOT/build}"',
            "tools/build-live-boot-binaries.sh": 'BUILD_DIR="${CHIMERA_BUILD_DIR:-$ROOT/build}"',
            "boot/iso/prepare-layout.sh": 'BUILD_DIR="${CHIMERA_BUILD_DIR:-$ROOT/build}"',
            "boot/iso/build-iso.sh": 'BUILD_DIR="${CHIMERA_BUILD_DIR:-$ROOT/build}"',
            "build-chimera-iso.sh": 'export CHIMERA_BUILD_DIR="$BUILD_DIR"',
        }
        for relative, required in expected.items():
            source = (root / relative).read_text()
            self.assertIn(required, source, relative)
            self.assertNotIn('"$ROOT/build/', source, relative)
        prepare = (root / "boot/iso/prepare-layout.sh").read_text()
        build_iso = (root / "boot/iso/build-iso.sh").read_text()
        self.assertIn('NATIVE_ISO_ROOT="${CHIMERA_NATIVE_ISO_ROOT:-$ISO_ROOT}"', build_iso)
        self.assertIn('NATIVE_ISO_ROOT="${CHIMERA_NATIVE_ISO_ROOT:-$ROOT/boot/iso}"', prepare)
        main_builder = (root / "build-chimera-iso.sh").read_text()
        self.assertIn('local native_root="$BUILD_DIR/native-iso"', main_builder)
        self.assertIn('install -m 0644 "$UEFI_LOADER" "$DIST/EFI/BOOT/BOOTX64.EFI"', prepare)
        self.assertIn('BOOT_ART="${CHIMERA_BOOT_ARTIFACT_DIR:-$BUILD_DIR/boot-artifacts}"', prepare)
        self.assertIn('local generated_uefi_loader="${CHIMERA_BOOT_ARTIFACT_DIR:-$BUILD_DIR/boot-artifacts}/uefi/BOOTX64.EFI"', main_builder)

if __name__ == "__main__":
    unittest.main()
