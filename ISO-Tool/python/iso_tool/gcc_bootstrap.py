from __future__ import annotations
from pathlib import Path
import os,shutil,subprocess
GCC_SOURCE='https://gcc.gnu.org/git/gcc.git'
def find_gxx():return shutil.which('g++') or shutil.which('g++.exe')
def build_gcc(source:Path,build:Path,prefix:Path,log=print)->Path:
    source=Path(source).resolve();build=Path(build).resolve();prefix=Path(prefix).resolve();build.mkdir(parents=True,exist_ok=True);prefix.mkdir(parents=True,exist_ok=True);configure=source/'configure'
    if not configure.exists():raise RuntimeError('GCC source tree has no configure script; obtain a release tarball or generate the required bootstrap files first.')
    if not (shutil.which('make') or shutil.which('mingw32-make')):raise RuntimeError('GNU make is required to bootstrap GCC.')
    shell=shutil.which('sh')
    if not shell and os.name=='nt':raise RuntimeError('A POSIX shell such as MSYS2 sh.exe is required for the GCC Windows source build.')
    def run(cmd):log('$ '+' '.join(map(str,cmd)));return subprocess.run(cmd,cwd=build,check=True,text=True,timeout=14400)
    run([shell or 'sh',str(configure),f'--prefix={prefix}','--enable-languages=c,c++','--disable-multilib','--disable-bootstrap']);make=shutil.which('make') or shutil.which('mingw32-make');run([make,'-j2','all-gcc','all-target-libgcc','all-target-libstdc++-v3']);run([make,'install-gcc','install-target-libgcc','install-target-libstdc++-v3'])
    candidate=prefix/'bin'/'g++.exe' if os.name=='nt' else prefix/'bin'/'g++'
    if not candidate.is_file():raise RuntimeError('GCC bootstrap finished without producing the integrated g++ executable.')
    return candidate
