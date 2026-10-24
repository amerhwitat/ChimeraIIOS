#!/usr/bin/env python3
"""Unit tests for the native ELF target matrix; these do not claim CPU execution."""
import json, struct, tempfile, unittest
from pathlib import Path
import verify_elf_matrix as verifier

class ElfMatrixTests(unittest.TestCase):
    def test_manifest_has_unique_targets_and_bounded_claims(self):
        data = verifier.load_manifest()
        self.assertGreaterEqual(len(data["architecture_targets"]), 10)
        self.assertIn("x86_64", {t["id"] for t in data["architecture_targets"]})
        self.assertEqual(data["policy"]["release_mode"], "fail-closed")

    def test_rejects_non_elf(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.elf"
            p.write_bytes(b"not an ELF file")
            with self.assertRaises(verifier.MatrixError):
                verifier.read_elf_identity(p)

    def test_accepts_matching_elf_header_identity_only(self):
        # Header fixture validates parser/ABI selection only; it is NOT executable code.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "fixture.elf"
            ident = bytearray(20)
            ident[:4] = b"\x7fELF"
            ident[4], ident[5], ident[6] = 2, 1, 1
            ident[18:20] = struct.pack("<H", 62)
            p.write_bytes(ident)
            self.assertEqual(verifier.read_elf_identity(p), (64, "little", 62))
            verifier.verify_artifact(next(t for t in verifier.load_manifest()["architecture_targets"] if t["id"] == "x86_64"), p)

    def test_rejects_cross_architecture_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "fixture.elf"
            ident = bytearray(20)
            ident[:4] = b"\x7fELF"
            ident[4], ident[5], ident[6] = 2, 1, 1
            ident[18:20] = struct.pack("<H", 183) # AArch64, not x86-64
            p.write_bytes(ident)
            target = next(t for t in verifier.load_manifest()["architecture_targets"] if t["id"] == "x86_64")
            with self.assertRaisesRegex(verifier.MatrixError, "identity mismatch"):
                verifier.verify_artifact(target, p)

if __name__ == "__main__":
    unittest.main(verbosity=2)
