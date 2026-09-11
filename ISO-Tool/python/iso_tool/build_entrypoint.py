"""Single build entry point: inspect documents, plan precedence, compile/link, stage artifacts."""
from __future__ import annotations
import argparse,json,shutil,subprocess
from pathlib import Path
from .output_paths import prepare_output_layout
from .build_planner import make_plan
from .ai_engine import propose_refinement
from .build_adapters import detect_build_systems, command_for
from .application_discovery import discover_applications

def _run(cmd:list[str],cwd:Path,log):
    log('[exec] '+' '.join(str(x) for x in cmd));p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=7200)
    if p.stdout:log(p.stdout.rstrip())
    if p.stderr:log(p.stderr.rstrip())
    if p.returncode:raise RuntimeError(f'command failed ({p.returncode}): {cmd[0]}')
    return p

def _stage_tree(build:Path,layout:dict,log):
    staged=[]
    for p in build.rglob('*'):
        if not p.is_file():continue
        s=p.suffix.lower()
        if s in {'.exe','.com'}:target=layout['executables']/p.name
        elif s in {'.dll','.so','.dylib','.lib','.a'}:target=layout['libraries']/p.name
        elif s in {'.bin','.img','.efi'}:target=layout['boot_images']/p.name
        else:continue
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);staged.append(str(target));log(f'[artifact] {target}')
    return staged

def _compile_systems(source:Path,output:Path,compiler:str,log):
    build_root=output/'build'/compiler.lower().replace('+','p').replace(' ','-');build_root.mkdir(parents=True,exist_ok=True);systems=detect_build_systems(source)
    if not systems:raise RuntimeError(f'No registered build system detected at {source}')
    reports=[]
    for system in systems:
        command=command_for(system,source,build_root/system,compiler)
        if command is None:reports.append({'system':system,'status':'unavailable','command':None});log(f'[build] {system}: toolchain unavailable; skipped');continue
        try:
            _run(command,source,log)
            if system=='cmake':_run(['cmake','--build',str(build_root/system),'--config','Release','--parallel'],source,log)
            elif system=='meson':_run(['meson','compile','-C',str(build_root/system)],source,log)
            elif system=='npm':_run(['npm','run','build','--if-present'],source,log)
            reports.append({'system':system,'status':'built','command':command})
        except Exception as exc:reports.append({'system':system,'status':'failed','command':command,'error':str(exc)});log(f'[build] {system}: {exc}')
    return build_root,reports

def build(source:Path,output:Path,compiler:str='auto',log=print)->dict:
    source=source.resolve();output=output.resolve();layout=prepare_output_layout(output);knowledge=output/'knowledge';plan=make_plan(source,knowledge);log(f'[intelligence] scanned {len(plan["steps"])} ordered build stages');ai=propose_refinement(plan,prompt_context='Keep the deterministic precedence unchanged unless a registered dependency proves otherwise.');(knowledge/'ai-plan.json').write_text(json.dumps(ai,indent=2),encoding='utf-8');applications=discover_applications(source);(knowledge/'applications.json').write_text(json.dumps(applications,indent=2),encoding='utf-8');build_root,reports=_compile_systems(source,output,compiler,log);artifacts=_stage_tree(build_root,layout,log);manifest=layout['manifests']/f'build-result-{compiler}.json';manifest.write_text(json.dumps({'source':str(source),'output':str(output),'compiler':compiler,'build_tree':str(build_root),'build_systems':reports,'artifacts':artifacts,'plan':str(knowledge/'build-plan.json'),'ai_plan':str(knowledge/'ai-plan.json'),'applications':str(knowledge/'applications.json')},indent=2),encoding='utf-8');log(f'[manifest] {manifest}');return {'layout':layout,'build_tree':build_root,'artifacts':artifacts,'manifest':manifest,'build_systems':reports}

def main(argv=None):
    ap=argparse.ArgumentParser(description='ISO-Tool document-aware compile/link entry point');ap.add_argument('source');ap.add_argument('--output',required=True);ap.add_argument('--compiler',choices=['auto','gnu','msvc'],default='auto');a=ap.parse_args(argv);r=build(Path(a.source),Path(a.output),a.compiler);print(json.dumps({k:str(v) for k,v in r.items() if k!='layout'},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
