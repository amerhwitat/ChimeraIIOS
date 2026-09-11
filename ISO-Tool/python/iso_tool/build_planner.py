from __future__ import annotations
import json
from pathlib import Path
from .document_intelligence import scan_repository,infer_components
BASE_ORDER=['toolchain','generated_sources','libraries','drivers','kernel','bootloader','system_services','applications','filesystem_staging','boot_images','iso_mastering']
def make_plan(root,knowledge_dir):
 root=Path(root).resolve();idx=scan_repository(root);c=infer_components(idx);steps=[]
 for n in BASE_ORDER:
  if n=='libraries' and not c['libraries']:continue
  if n=='drivers' and not c['drivers']:continue
  if n=='kernel' and not c['kernel']:continue
  if n=='bootloader' and not c['boot']:continue
  if n=='applications' and not c['applications']:continue
  steps.append({'id':n,'precedence':len(steps)+1,'status':'planned','reason':'deterministic repository evidence/policy'})
 plan={'schema':1,'repository':str(root),'components':c,'steps':steps,'authority':'deterministic-policy','ai_refinement':'optional-and-constrained'};knowledge_dir=Path(knowledge_dir);knowledge_dir.mkdir(parents=True,exist_ok=True);(knowledge_dir/'repository-knowledge.json').write_text(json.dumps(idx,indent=2));(knowledge_dir/'build-plan.json').write_text(json.dumps(plan,indent=2));return plan
