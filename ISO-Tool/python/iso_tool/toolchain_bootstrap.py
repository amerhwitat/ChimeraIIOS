from __future__ import annotations
from pathlib import Path
import json, os, shutil, subprocess
from .windows_toolchains import discover
NASM_GIT='https://github.com/netwide-assembler/nasm.git'
GCC_GIT='https://gcc.gnu.org/git/gcc.git'
def scan_windows(output:Path)->dict:
    tools=discover();report={'platform':os.name,'toolchains':[t.__dict__ for t in tools],'roles':{}}
    for t in tools: report['roles'].setdefault(t.role,[]).append(t.__dict__)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2),encoding='utf-8');return report
def _run(cmd,cwd=None,env=None,log=None):
    if log:log('$ '+' '.join(map(str,cmd)))
    return subprocess.run(cmd,cwd=cwd,env=env,check=True,text=True,capture_output=True,timeout=7200)
def build_nasm(source:Path,build:Path,install:Path,log=None)->Path:
    source=Path(source);build=Path(build);install=Path(install);build.mkdir(parents=True,exist_ok=True);install.mkdir(parents=True,exist_ok=True)
    if os.name=='nt' and shutil.which('nmake') and (source/'Mkfiles/msvc.mak').exists():_run(['nmake','/f','Mkfiles/msvc.mak'],cwd=source,log=log)
    elif (source/'configure').exists():
        _run(['sh','configure',f'--prefix={install}'],cwd=build,log=log);_run(['make','-j'],cwd=build,log=log);_run(['make','install'],cwd=build,log=log)
    else:raise RuntimeError('NASM source lacks a supported build entry point.')
    for p in (install/'nasm.exe',source/'nasm.exe',build/'nasm.exe'):
        if p.is_file():return p
    raise RuntimeError('NASM build completed without producing nasm.exe')
def bootstrap_plan(report:dict)->dict:
    names={Path(t['path']).name.lower() for t in report.get('toolchains',[])};assembler=any(x in names for x in ('nasm.exe','ml64.exe','ml.exe','clang.exe','as.exe','yasm.exe'));cxx=any(x in names for x in ('cl.exe','g++.exe','clang++.exe','clang-cl.exe'))
    return {'assembler_available':assembler,'cxx_available':cxx,'nasm_source':NASM_GIT,'gcc_source':GCC_GIT,'actions':(['use-detected-toolchain'] if assembler else ['use-built-in-boot-assembler','bootstrap-nasm']),'gcc_action':'use-detected-g++' if cxx else 'bootstrap-gcc-when-prerequisites-available'}
def write_plan(output:Path,report:dict)->dict:
    plan=bootstrap_plan(report);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(plan,indent=2),encoding='utf-8');return plan
