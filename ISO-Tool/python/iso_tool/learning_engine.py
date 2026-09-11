from pathlib import Path
import hashlib,json,time,re
EXT={'.md','.txt','.rst','.adoc','.json','.yaml','.yml','.toml','.xml','.cmake','.py','.c','.cpp','.h','.hpp','.cs','.java','.js','.ts','.sh','.asm'}
def ingest_repository(root,out):
 root=Path(root);out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);n=0
 with out.open('w',encoding='utf-8') as f:
  for p in root.rglob('*'):
   if p.is_file() and p.suffix.lower() in EXT and not any(x in p.parts for x in ('.git','node_modules','bin','obj')):
    raw=p.read_bytes();f.write(json.dumps({'source':str(p.relative_to(root)),'source_type':'repository','retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode('utf-8','replace')[:500000]})+'\n');n+=1
 return {'records':n,'output':str(out)}
def generate_build_plan(k):
 text=''.join(p.read_text(encoding='utf-8',errors='ignore') for p in Path(k).glob('*.jsonl'));steps=[x for x in ('cmake','make','mvn','dotnet build','msbuild','npm run build','cargo build') if re.search(r'\b'+re.escape(x.split()[0])+r'\b',text,re.I)] or ['detect build system','resolve dependencies','compile','link','stage binaries','build ISO','verify ISO'];return {'steps':steps,'evidence':str(k),'authorization_required':True}
