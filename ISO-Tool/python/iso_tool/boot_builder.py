from __future__ import annotations
from pathlib import Path
import shutil,subprocess
from .builtin_boot_assembler import assemble_spit_fire
def build_spit_fire(source:Path,output:Path,log=None)->Path:
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);nasm=shutil.which('nasm') or shutil.which('nasm.exe')
    if nasm:
        cmd=[nasm,'-f','bin',str(source),'-o',str(output)]
        if log:log('$ '+' '.join(cmd))
        subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=120)
    else:
        if log:log('[boot] NASM unavailable; using built-in Spit Fire bootstrap assembler')
        assemble_spit_fire(output)
    data=output.read_bytes()
    if len(data)!=512 or data[-2:]!=b'\x55\xAA':raise RuntimeError('Spit Fire BIOS boot sector failed 512-byte/0xAA55 validation')
    return output
