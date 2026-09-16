import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'installer/chimera_installer.py'
def test_planner_emits_schema(tmp_path):
    out=tmp_path/'plan.json'
    subprocess.run([sys.executable,str(SCRIPT),'--edition','desktop','--output',str(out)],check=True)
    data=json.loads(out.read_text())
    assert data['schema']=='CHIMERA-INSTALL-PLAN-1'
    assert data['selection']['edition']=='desktop'
    assert data['selection']['disk_policy'].startswith('never')
