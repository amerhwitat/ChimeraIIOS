#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, platform, shlex, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DIST=ROOT/'build'/'artifacts'
def log(s,m): print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] [{s.upper():10}] {m}',flush=True)
def tool(n): return shutil.which(n)
def run(cmd,dry=False,cwd=ROOT):
 log('command',' '.join(shlex.quote(str(x)) for x in cmd))
 if dry:return 0
 t=time.monotonic(); p=subprocess.Popen([str(x) for x in cmd],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 assert p.stdout
 for line in p.stdout: print(line.rstrip(),flush=True)
 rc=p.wait(); log('result',f'exit={rc} elapsed={time.monotonic()-t:.2f}s'); return rc
def caps():
 return {'python':bool(list(ROOT.rglob('*.py'))),'java':bool(list(ROOT.rglob('*.java')) or (ROOT/'pom.xml').exists() or (ROOT/'build.gradle').exists()),'node':(ROOT/'package.json').exists(),'cmake':(ROOT/'CMakeLists.txt').exists(),'dotnet':bool(list(ROOT.rglob('*.sln'))+list(ROOT.rglob('*.csproj'))),'sql':bool(list(ROOT.rglob('*.sql')))}
def pybuild(a,dry):
 if not tool('python'): log('skip','Python not found'); return 0
 req=ROOT/'requirements.txt'
 if req.exists() and run([sys.executable,'-m','pip','install','-r',str(req)],dry): return 1
 src=[p for p in ROOT.rglob('*.py') if p.name not in {'__init__.py','setup.py'} and not any(x in p.parts for x in {'.git','build','dist','.venv','venv','__pycache__'})]
 if a.python: src=[ROOT/a.python]
 for p in src[:1] if not a.python else src:
  cmd=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--name',p.stem,'--distpath',str(DIST/'python'),'--workpath',str(ROOT/'build'/'pyinstaller')]
  if a.onefile: cmd.insert(4,'--onefile')
  if run(cmd+[str(p)],dry): return 1
 return 0
def javabuild(dry):
 if (ROOT/'pom.xml').exists() and tool('mvn'): return run(['mvn','-B','test','package'],dry)
 if (ROOT/'gradlew').exists(): return run([str(ROOT/'gradlew'),'build'],dry)
 if (ROOT/'build.gradle').exists() and tool('gradle'): return run(['gradle','build'],dry)
 src=[p for p in ROOT.rglob('*.java') if '.git' not in p.parts]
 if src and tool('javac'):
  out=ROOT/'build'/'java-classes'; out.mkdir(parents=True,exist_ok=True); return run(['javac','-d',str(out),*map(str,src)],dry)
 log('skip','No Java build target'); return 0
def nodebuild(dry):
 if not (ROOT/'package.json').exists(): log('skip','No package.json'); return 0
 pm='pnpm' if (ROOT/'pnpm-lock.yaml').exists() and tool('pnpm') else 'yarn' if (ROOT/'yarn.lock').exists() and tool('yarn') else 'npm'
 if not tool(pm): log('skip',f'{pm} not found'); return 0
 install=['npm','ci'] if pm=='npm' and (ROOT/'package-lock.json').exists() else [pm,'install']
 if run(install,dry): return 1
 return run([pm,'run','build'],dry)
def nativebuild(dry):
 if (ROOT/'CMakeLists.txt').exists() and tool('cmake'):
  b=ROOT/'build'/'cmake'; b.mkdir(parents=True,exist_ok=True)
  if run(['cmake','-S',str(ROOT),'-B',str(b),'-DCMAKE_BUILD_TYPE=Release'],dry): return 1
  return run(['cmake','--build',str(b),'--config','Release','--parallel'],dry)
 if (ROOT/'Makefile').exists() and tool('make'): return run(['make','-j'],dry)
 if list(ROOT.glob('*.sln')) and tool('dotnet'): return run(['dotnet','build','--configuration','Release'],dry)
 return 0
def sqlbuild(dry):
 ss=sorted(p for p in ROOT.rglob('*.sql') if '.git' not in p.parts and 'build' not in p.parts)
 log('database',f'discovered {len(ss)} SQL scripts; execution uses configured native clients/NLP_DB_* variables')
 for p in ss: log('database',str(p.relative_to(ROOT)))
 return 0
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--only',choices=['all','python','java','node','native','sql'],default='all'); ap.add_argument('--python'); ap.add_argument('--onefile',action='store_true'); a=ap.parse_args(); DIST.mkdir(parents=True,exist_ok=True)
 log('build',f'repo={ROOT.name} os={platform.system()} arch={platform.machine()}'); c=caps(); log('detect',json.dumps(c,sort_keys=True)); t=time.monotonic()
 fs={'python':lambda:pybuild(a,a.dry_run),'java':lambda:javabuild(a.dry_run),'node':lambda:nodebuild(a.dry_run),'native':lambda:nativebuild(a.dry_run),'sql':lambda:sqlbuild(a.dry_run)}
 for n in ([a.only] if a.only!='all' else ['python','java','node','native','sql']):
  if n!='all' and not c.get(n,True): log('skip',f'{n}: not detected'); continue
  log('stage',n)
  if fs[n](): log('build',f'FAILED stage={n}'); return 1
 log('build',f'DONE elapsed={time.monotonic()-t:.2f}s artifacts={DIST}'); return 0
if __name__=='__main__': raise SystemExit(main())
