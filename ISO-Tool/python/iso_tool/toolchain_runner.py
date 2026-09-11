from __future__ import annotations
from pathlib import Path
import json,shutil,subprocess
from .toolchain_bootstrap import build_nasm,scan_windows
from .gcc_bootstrap import build_gcc,GCC_SOURCE
NASM_SOURCE='https://github.com/netwide-assembler/nasm.git'
def bootstrap_missing(cache:Path,log=print)->dict:
    cache=Path(cache).resolve();cache.mkdir(parents=True,exist_ok=True);git=shutil.which('git')
    if not git:raise RuntimeError('Git is required for explicit source toolchain bootstrap.')
    result={'actions':[]};tools=scan_windows(cache/'windows-toolchains.json')['toolchains'];names={Path(t['path']).name.lower() for t in tools}
    if not any(x in names for x in ('nasm.exe','nasm')):
        src=cache/'sources'/'nasm';src.parent.mkdir(parents=True,exist_ok=True)
        if not src.exists():subprocess.run([git,'clone','--depth','1',NASM_SOURCE,str(src)],check=True,timeout=3600)
        exe=build_nasm(src,cache/'build'/'nasm',cache/'toolchains'/'nasm',log);result['actions'].append({'tool':'NASM','status':'built','path':str(exe)})
    else:result['actions'].append({'tool':'NASM','status':'already-available'})
    if not any(x in names for x in ('g++.exe','g++','clang++.exe','cl.exe')):
        src=cache/'sources'/'gcc';src.parent.mkdir(parents=True,exist_ok=True)
        if not src.exists():subprocess.run([git,'clone','--depth','1',GCC_SOURCE,str(src)],check=True,timeout=7200)
        exe=build_gcc(src,cache/'build'/'gcc',cache/'toolchains'/'gcc',log);result['actions'].append({'tool':'G++','status':'built','path':str(exe)})
    else:result['actions'].append({'tool':'G++','status':'already-available'})
    (cache/'toolchain-bootstrap-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result
