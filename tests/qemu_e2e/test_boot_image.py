import shutil, subprocess, time
from pathlib import Path
import pytest

ROOT=Path(__file__).parents[2]

def test_iso_artifact_exists_after_build():
    iso=ROOT/'boot/iso/dist/chimera2os-bootstrap.iso'
    if not iso.exists(): pytest.skip('ISO has not been built in this checkout')
    assert iso.stat().st_size > 0

@pytest.mark.integration
def test_qemu_boot_token():
    iso=ROOT/'boot/iso/dist/chimera2os-bootstrap.iso'
    if not iso.exists() or not shutil.which('qemu-system-x86_64'):
        pytest.skip('QEMU integration environment unavailable')
    p=subprocess.Popen(['qemu-system-x86_64','-drive',f'file={iso},format=raw','-serial','stdio','-display','none','-m','512'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    deadline=time.time()+15; output=''
    try:
        while time.time()<deadline:
            line=p.stdout.readline()
            if not line: break
            output += line
            if 'Chimera II OS bootstrap' in output: return
    finally:
        p.kill()
    assert 'Chimera II OS bootstrap' in output
