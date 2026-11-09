#!/usr/bin/env python3
"""Create lawful, testable Amiga ADF and Commodore D64 starter media."""
from __future__ import annotations
import argparse, hashlib, json, shutil, struct, subprocess, tempfile
from pathlib import Path

def run(args: list[str]) -> str:
    proc = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout

def write_c64_prg(path: Path) -> None:
    """Emit a small tokenized BASIC V2 PRG at $0801."""
    lines = [
        (10, b'\x99"CHIMERA II COMMODORE LAB"'),
        (20, b'\x99"READY - TYPE LIST OR RUN"'),
        (30, b'\x80'),  # BASIC END token
    ]
    address = 0x0801
    body = bytearray()
    for number, tokens in lines:
        line = struct.pack("<H", number) + tokens + b"\0"
        next_address = address + 2 + len(line)
        body += struct.pack("<H", next_address) + line
        address = next_address
    body += b"\0\0"
    path.write_bytes(struct.pack("<H", 0x0801) + body)

def create_adf(xdftool: str, out: Path, volume: str, fs_type: str, model: str, temp: Path) -> dict:
    image = out / f"Chimera-Amiga-{model}.adf"
    startup, readme = temp / f"Startup-Sequence-{model}", temp / f"README-Amiga-{model}.txt"
    startup.write_text(
        f"; Chimera Retro Lab - Amiga {model}\n"
        "; Data disk for a legally licensed Kickstart/Workbench installation.\n"
        f'Echo "CHIMERA RETRO LAB - AMIGA {model}"\n'
        'Echo "Disk mounted successfully."\n', encoding="ascii")
    readme.write_text(
        f"CHIMERA RETRO LAB - AMIGA {model}\nFilesystem: {fs_type.upper()}\n"
        "Formatted 880 KiB Amiga floppy data disk.\n"
        "No Kickstart ROM, Workbench, commercial software or proprietary firmware is included.\n"
        "Use with a legally licensed ROM/OS. S/Startup-Sequence is a sample script, not a full OS.\n",
        encoding="ascii")
    run([xdftool, str(image), "create"])
    run([xdftool, str(image), "format", volume, fs_type])
    run([xdftool, str(image), "makedir", "S"])
    run([xdftool, str(image), "write", str(startup), "S/Startup-Sequence"])
    run([xdftool, str(image), "write", str(readme), "README.TXT"])
    listing = run([xdftool, str(image), "list", "all", "info"])
    data = image.read_bytes()
    expected = b"DOS" + (b"\0" if fs_type == "ofs" else b"\1")
    if len(data) != 901120 or data[:4] != expected:
        raise RuntimeError(f"Invalid Amiga {model} ADF geometry/filesystem signature")
    if "README.TXT" not in listing or "Startup-Sequence" not in listing:
        raise RuntimeError(f"Amiga {model} ADF is missing expected files")
    return {"file": image.name, "format": "ADF", "model": model, "filesystem": fs_type.upper(),
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "validation": "xdftool filesystem list/info + DOS signature"}

def create_d64(c1541: str, out: Path, temp: Path) -> dict:
    image, prg, readme = out / "Chimera-Commodore-C64-Starter.d64", temp / "HELLO.PRG", temp / "README-C64.txt"
    write_c64_prg(prg)
    readme.write_text("CHIMERA RETRO LAB - COMMODORE 64\nStandard 35-track D64 with original HELLO.PRG.\nNo ROMs or commercial software included.\n", encoding="ascii")
    run([c1541, "-format", "CHIMERA,01", "d64", str(image),
         "-write", str(prg), "HELLO.PRG", "-write", str(readme), "README.TXT"])
    listing = run([c1541, str(image), "-list"])
    data = image.read_bytes()
    if len(data) != 174848:
        raise RuntimeError(f"Unexpected D64 size: {len(data)}")
    if "HELLO.PRG" not in listing or "README.TXT" not in listing:
        raise RuntimeError("C64 D64 directory validation failed")
    roundtrip = temp / "HELLO-ROUNDTRIP.PRG"
    run([c1541, str(image), "-read", "HELLO.PRG", str(roundtrip)])
    if roundtrip.read_bytes() != prg.read_bytes():
        raise RuntimeError("C64 PRG round-trip through c1541 did not match")
    return {"file": image.name, "format": "D64", "model": "Commodore 64", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "validation": "VICE c1541 directory listing + PRG round-trip"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/retro-media"))
    args = parser.parse_args()
    xdftool, c1541 = shutil.which("xdftool"), shutil.which("c1541")
    if not xdftool: parser.error("xdftool is required (install the amitools Python package)")
    if not c1541: parser.error("c1541 is required (install VICE disk utilities)")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chimera-retro-media-") as tmpdir:
        temp = Path(tmpdir)
        artifacts = [
            create_adf(xdftool, out, "CHIMERA_A500", "ofs", "A500", temp),
            create_adf(xdftool, out, "CHIMERA_A2000", "ffs", "A2000", temp),
            create_d64(c1541, out, temp),
        ]
    manifest = {"schema": "chimera-retro-media/v1",
                "policy": "open-source-emulator; no proprietary ROM/OS/game payloads",
                "artifacts": artifacts}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
