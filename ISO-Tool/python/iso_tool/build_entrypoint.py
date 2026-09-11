"""Recursive deterministic build entry point for ISO-Tool."""
from __future__ import annotations
import argparse,json,shutil,subprocess
from pathlib import Path
from .output_paths import prepare_output_layout
from .build_planner import make_plan
from .ai_engine import propose_refinement
from .build_adapters import detect_build_systems,command_for
from .application_discovery import discover_applications
from .tree_scanner import scan_tree
BUILD_MARKERS={'CMakeLists.txt','Makefile','makefile','meson.build','Cargo.toml','package.json','pom.xml','build.gradle','build.gradle.kts','go.mod','configure','configure.ac'}
SKIP_DIRS={'.git','.hg','.svn','node_modules','.venv','venv','__pycache__','.tox','dist','build','out','target'}
def _run(cmd,cwd,log):
    log('[exec] '+' '.join(str(x) for x in cmd));p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=7200)
    if p.stdout:log(p.stdout.rstrip())
    if p.stderr:log(p.stderr.rstrip())
    if p.returncode:raise RuntimeError(f'command failed ({p.returncode}): {cmd[0]}')
    return p
def _project_roots(source:Path):
    roots={source}
    for p in source.rglob('*'):
        if any(part in SKIP_DIRS for part in p.parts):continue
        if p.is_file() and p.name in BUILD_MARKERS:roots.add(p.parent)
    return sorted(roots,key=lambda p:(len(p.relative_to(source).parts),str(p).lower()))
def _stage_tree(tree:Path,layout:dict,log):
    staged=[]
    for p in tree.rglob('*'):
        if not p.is_file():continue
        s=p.suffix.lower()
        if s in {'.exe','.com'}:target=layout['executables']/p.name
        elif s in {'.dll','.so','.dylib','.lib','.a'}:target=layout['libraries']/p.name
        elif s in {'.bin','.img','.efi'}:target=layout['boot_images']/p.name
        else:continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.resolve()!=p.resolve():shutil.copy2(p,target);staged.append(str(target));log(f'[artifact] {target}')
    return staged
def _compile_project(root:Path,output:Path,compiler:str,log):
    systems=detect_build_systems(root);reports=[];build_root=output/'build'/'projects'/root.name
    for index,system in enumerate(systems):
        bd=build_root/f'{index:02d}-{system}';bd.mkdir(parents=True,exist_ok=True);command=command_for(system,root,bd,compiler)
        if command is None:reports.append({'project':str(root),'system':system,'status':'unavailable','command':None});continue
        try:
            _run(command,root,log)
            if system=='cmake':_run(['cmake','--build',str(bd),'--config','Release','--parallel'],root,log)
            elif system=='meson':_run(['meson','compile','-C',str(bd)],root,log)
            elif system=='npm':_run(['npm','run','build','--if-present'],root,log)
            elif system=='autotools' and shutil.which('make'):_run(['make','-j'],root,log)
            reports.append({'project':str(root),'system':system,'status':'built','command':command})
        except Exception as exc:reports.append({'project':str(root),'system':system,'status':'failed','command':command,'error':str(exc)});log(f'[build] {root.name}/{system}: {exc}')
    return build_root,reports
def build(source:Path,output:Path,compiler:str='auto',log=print)->dict:
    source=source.resolve();output=output.resolve();layout=prepare_output_layout(output);knowledge=output/'knowledge';knowledge.mkdir(parents=True,exist_ok=True);tree=scan_tree(source,knowledge/'repository-tree.json');plan=make_plan(source,knowledge);log(f'[scan] recursively indexed {tree["summary"]["files"]} files; languages={tree["summary"]["languages"]}');log(f'[intelligence] ordered {len(plan["steps"])} build stages');ai=propose_refinement(plan,prompt_context='Keep deterministic dependency/build precedence authoritative.');(knowledge/'ai-plan.json').write_text(json.dumps(ai,indent=2),encoding='utf-8');applications=discover_applications(source);(knowledge/'applications.json').write_text(json.dumps(applications,indent=2),encoding='utf-8');all_reports=[];all_artifacts=[]
    for project in _project_roots(source):
        log(f'[project] {project.relative_to(source) if project!=source else "."}');build_root,reports=_compile_project(project,output,compiler,log);all_reports.extend(reports);all_artifacts.extend(_stage_tree(project,layout,log));all_artifacts.extend(_stage_tree(build_root,layout,log))
    if not all_reports:raise RuntimeError('No registered build system found anywhere in the recursive source tree.')
    manifest=layout['manifests']/f'build-result-{compiler}.json';manifest.write_text(json.dumps({'source':str(source),'output':str(output),'compiler':compiler,'projects':_project_roots(source),'build_systems':all_reports,'artifacts':sorted(set(all_artifacts)),'repository_tree':str(knowledge/'repository-tree.json'),'plan':str(knowledge/'build-plan.json'),'ai_plan':str(knowledge/'ai-plan.json'),'applications':str(knowledge/'applications.json')},indent=2,default=str),encoding='utf-8');return {'layout':layout,'manifests':manifest,'artifacts':sorted(set(all_artifacts)),'build_systems':all_reports}
def main(argv=None):
    ap=argparse.ArgumentParser(description='ISO-Tool recursive document-aware compile/link entry point');ap.add_argument('source');ap.add_argument('--output',required=True);ap.add_argument('--compiler',choices=['auto','gnu','msvc'],default='auto');a=ap.parse_args(argv);r=build(Path(a.source),Path(a.output),a.compiler);print(json.dumps({k:str(v) for k,v in r.items() if k!='layout'},indent=2,default=str));return 0
if __name__=='__main__':raise SystemExit(main())
