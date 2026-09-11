from __future__ import annotations
import json,os,shutil,subprocess
from pathlib import Path
def discover_backends():return {'llama_cpp':bool(shutil.which('llama-cli') or shutil.which('llama')),'rnn_model':bool(os.environ.get('ISO_TOOL_RNN_MODEL'))}
def propose_refinement(plan,prompt_context='',model=None):
 r={'schema':1,'backend':'none','approved_steps':plan.get('steps',[]),'recommendations':[],'confidence':0.0};cli=shutil.which('llama-cli') or shutil.which('llama')
 if not cli or not model or not Path(model).exists():r['recommendations'].append('No local model configured; deterministic plan remains authoritative.');return r
 prompt='Return JSON recommendations only. Never invent commands or reorder mandatory dependencies.\n'+json.dumps(plan)+'\n'+prompt_context
 try:
  p=subprocess.run([cli,'-m',str(model),'--temp','0','-n','512','-p',prompt],capture_output=True,text=True,timeout=600)
  if p.returncode==0:r.update(backend='llama.cpp',raw=p.stdout[-20000:],confidence=.5)
 except (OSError,subprocess.SubprocessError):r['recommendations'].append('LLM invocation failed; deterministic plan retained.')
 return r
