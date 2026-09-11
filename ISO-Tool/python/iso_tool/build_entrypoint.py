from __future__ import annotations
import argparse,json,shutil,subprocess
from pathlib import Path
from .output_paths import prepare_output_layout
from .build_planner import make_plan
from .ai_engine import propose_refinement
def run(cmd,cwd,log):
 log('[exec] '+' '.join(map(str,cmd)));p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=7200)
 if p.stdout:log(p.stdout.rstrip())
 if p.stderr:log(p.stderr.rstrip())
 if p.returncode:raise RuntimeError(f'command failed ({p.returncode}): {cmd[0]}')
def build(source:Path,output:Path,compiler='auto',log=print):
 source=source.resolve();output=output.resolve();layout=prepare_output_layout(output);knowledge=output/'knowledge';plan=make_plan(source,knowledge);(knowledge/'ai-plan.json').write_text(json.dumps(propose_refinement(plan,prompt_context='Do not invent commands or reorder mandatory dependencies.'),indent=2),encoding='utf-8');build_root=output/'build'/compiler;build_root.mkdir(parents=True,exist_ok=True);cmake=shutil.which('cmake')
 if not cmake:raise RuntimeError('CMake was not found.')
 if not (source/'CMakeLists.txt').exists():raise RuntimeError(f'No CMakeLists.txt found at {source}')
 if compiler=='gnu':gen='Ninja' if shutil.which('ninja') else 'MinGW Makefiles';run([cmake,'-S',str(source),'-B',str(build_root),'-G',gen,'-DCMAKE_BUILD_TYPE=Release'],source,log)
 elif compiler=='msvc':run([cmake,'-S',str(source),'-B',str(build_root),'-G','Visual Studio 17 2022','-A','x64'],source,log)
 else:run([cmake,'-S',str(source),'-B',str(build_root)],source,log)
 run([cmake,'--build',str(build_root),'--config','Release','--parallel'],source,log);artifacts=[]
 for p in build_root.rglob('*'):
  if not p.is_file():continue
  d=layout['executables'] if p.suffix.lower() in {'.exe','.com'} else layout['libraries'] if p.suffix.lower() in {'.dll','.so','.dylib','.lib','.a'} else layout['boot_images'] if p.suffix.lower() in {'.bin','.img','.efi'} else None
  if d:t=d/p.name;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t);artifacts.append(str(t));log(f'[artifact] {t}')
 m=layout['manifests']/f'build-result-{compiler}.json';m.write_text(json.dumps({'source':str(source),'compiler':compiler,'build_tree':str(build_root),'artifacts':artifacts,'plan':str(knowledge/'build-plan.json')},indent=2),encoding='utf-8');return artifacts
def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('--output',required=True);ap.add_argument('--compiler',choices=['auto','gnu','msvc'],default='auto');a=ap.parse_args(argv);build(Path(a.source),Path(a.output),a.compiler);return 0
if __name__=='__main__':raise SystemExit(main())
