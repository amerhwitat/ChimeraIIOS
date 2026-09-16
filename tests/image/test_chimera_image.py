from pathlib import Path
import hashlib
from tools.image.chimera_image import inspect_file, create_manifest, validate_manifest


def test_inspect_raw(tmp_path: Path):
    p = tmp_path / "guest.bin"
    p.write_bytes(b"chimera")
    info = inspect_file(p)
    assert info["format"] == "raw"
    assert info["size"] == 7


def test_manifest_checksum(tmp_path: Path):
    p = tmp_path / "guest.bin"
    p.write_bytes(b"chimera")
    manifest = create_manifest(p, "x86_64")
    assert manifest["sha256"] == hashlib.sha256(b"chimera").hexdigest()
    assert validate_manifest(manifest)
