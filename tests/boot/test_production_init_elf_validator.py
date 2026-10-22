#!/usr/bin/env python3
"""Regression tests for the production init ELF packaging validator."""
from __future__ import annotations
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "boot" / "verify-production-init-elfs.py"
HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PHDR = struct.Struct("<IIQQQQQQ")
TARGET_PATHS = (
    "boot/live/user-init-live.elf",
    "boot/installer/user-init-installer.elf",
    "boot/recovery/user-init-recovery.elf",
)

def make_elf(flags: int = 5, machine: int = 62) -> bytes:
    ident = b"\x7fELF" + bytes((2, 1, 1, 0, 0)) + bytes(7)
    header = HEADER.pack(ident, 2, machine, 1, 0x400000, HEADER.size, 0, 0,
                         HEADER.size, PHDR.size, 1, 0, 0, 0)
    phdr = PHDR.pack(1, flags, HEADER.size + PHDR.size, 0x400000, 0, 1, 1, 1)
    return header + phdr + b"\xC3"

class ProductionInitElfValidatorTests(unittest.TestCase):
    def run_validator(self, root: Path, manifest: Path | None = None) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(VALIDATOR), str(root)]
        if manifest:
            cmd += ["--write-manifest", str(manifest)]
        return subprocess.run(cmd, text=True, capture_output=True, check=False)

    def populate(self, root: Path, payload: bytes) -> None:
        for relative in TARGET_PATHS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

    def test_valid_target_elfs_generate_sha256_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "iso"
            self.populate(root, make_elf())
            manifest = Path(temp) / "manifest.json"
            result = self.run_validator(root, manifest)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "payloads-validated-not-runtime-accepted")
            self.assertEqual([p["target"] for p in data["payloads"]], ["live", "installer", "recovery"])
            self.assertTrue(all(len(p["sha256"]) == 64 for p in data["payloads"]))

    def test_missing_payload_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "iso"
            self.populate(root, make_elf())
            (root / TARGET_PATHS[0]).unlink()
            result = self.run_validator(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing", result.stderr.lower())

    def test_writable_executable_segment_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "iso"
            self.populate(root, make_elf(flags=7))
            result = self.run_validator(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("W^X", result.stderr)

    def test_wrong_architecture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "iso"
            self.populate(root, make_elf(machine=183))
            result = self.run_validator(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("x86-64", result.stderr)

if __name__ == "__main__":
    unittest.main()
