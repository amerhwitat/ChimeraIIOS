from __future__ import annotations
from pathlib import Path
import shutil,subprocess
from .image_profiles import get_profile
def find_backend():
    for n in ('xorriso','xorrisofs','oscdimg'):
        p=shutil.which(n)
        if p:return p
    return None
def create_iso(staging:Path,output:Path,label='ISO_TOOL',profile='data'):
    backend=find_backend()
    if not backend:raise RuntimeError('No supported ISO backend found (xorriso/xorrisofs/oscdimg).')
    cfg=get_profile(profile);Path(output).parent.mkdir(parents=True,exist_ok=True);name=Path(backend).name.lower();bios=Path(staging)/cfg.bios_boot if cfg.bios_boot else None;efi=Path(staging)/cfg.uefi_boot if cfg.uefi_boot else None
    if cfg.bios_boot and (not bios or not bios.is_file()):raise RuntimeError(f'BIOS boot image missing: {cfg.bios_boot}')
    if cfg.uefi_boot and (not efi or not efi.is_file()):raise RuntimeError(f'UEFI boot image missing: {cfg.uefi_boot}')
    if name in ('xorriso','xorrisofs'):
        cmd=[backend,'-as','mkisofs','-iso-level','3','-V',label,'-J','-R','-c','boot.catalog']
        if cfg.udf_version:cmd+=['-udf']
        if bios:cmd+=['-b',cfg.bios_boot,'-no-emul-boot','-boot-load-size','4','-boot-info-table']
        if efi:cmd+=['-eltorito-alt-boot','-e',cfg.uefi_boot,'-no-emul-boot']
        cmd+=['-o',str(output),str(staging)]
    else:
        cmd=[backend,'-l','-m','*','-o',str(output),str(staging)]
        if bios and efi:cmd[1:1]=['-bootdata:2#p0,e,b'+str(bios)+'#pEF,e,b'+str(efi)]
        elif bios:cmd[1:1]=['-b'+str(bios),'-p0']
        elif efi:cmd[1:1]=['-b'+str(efi),'-pEF']
    return subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=3600)
