import os, tempfile, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOOL=ROOT/"filesystems/qfs/qfs_mkfs.py"

def test_qfs_default_4k_and_inspect():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"test.qfs"
        subprocess.run([sys.executable,str(TOOL),str(p),"--size",str(8*1024*1024),"--force"],check=True)
        raw=p.read_bytes()[:16]
        assert raw[8:12] == (4096).to_bytes(4,"little")
        out=subprocess.check_output([sys.executable,str(TOOL),str(p),"--inspect"],text=True)
        assert "4096" in out

def test_qfs_rejects_unsupported_size():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"bad.qfs"
        r=subprocess.run([sys.executable,str(TOOL),str(p),"--size",str(8*1024*1024),"--block-size","12288"],capture_output=True,text=True)
        assert r.returncode != 0
