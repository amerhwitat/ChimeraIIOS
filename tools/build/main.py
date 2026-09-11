"""Chimera II OS build entry point: configure, compile, link, and report artifacts."""
from __future__ import annotations
import argparse, json, shutil, subprocess
from pathlib import Path

def run(cmd, root, log=print):
    log('[exec] ' + ' '.join(map(str, cmd)))
    p=subprocess.run(cmd,cwd=root,text=True,capture_output=True,timeout=7200)
    if p.stdout: log(p.stdout.rstrip())
    if p.stderr: log(p.stderr.rstrip())
    if p.returncode: raise SystemExit(p.returncode)

def main(argv=None):
    ap=argparse.ArgumentParser(description='Chimera II OS single build entry point')
    ap.add_argument('--root',default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument('--build-dir',default=None)
    ap.add_argument('--generator',default=None)
    ap.add_argument('--clean',action='store_true')
    args=ap.parse_args(argv)
    root=Path(args.root).resolve(); build=Path(args.build_dir).resolve() if args.build_dir else root/'build'
    if args.clean and build.exists(): shutil.rmtree(build)
    build.mkdir(parents=True,exist_ok=True)
    cmake=shutil.which('cmake')
    if not cmake: raise SystemExit('CMake not found')
    configure=[cmake,'-S',str(root),'-B',str(build)]
    if args.generator: configure += ['-G',args.generator]
    run(configure,root)
    run([cmake,'--build',str(build),'--config','Release','--parallel'],root)
    artifacts=[]
    for p in build.rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.exe','.dll','.lib','.a','.so','.bin','.img','.efi'}:
            artifacts.append(str(p.relative_to(build)))
    report=build/'chimera-build-artifacts.json'
    report.write_text(json.dumps({'source':str(root),'build':str(build),'artifacts':artifacts},indent=2),encoding='utf-8')
    print(json.dumps({'build':str(build),'artifact_report':str(report),'artifacts':artifacts},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
