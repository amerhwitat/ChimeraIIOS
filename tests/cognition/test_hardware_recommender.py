import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOOL=ROOT/"tools/cognition/chimera_hardware_recommender.py"

def test_recommender_produces_provenance_and_no_auto_install(tmp_path):
    inv={"schema":"test","host":{"os":"Linux","machine":"x86_64"},"devices":[{"class":"pci","raw":"Intel Corporation Ethernet Controller; driver in use: igc"}],"storage":[]}
    p=tmp_path/"inventory.json"; p.write_text(json.dumps(inv))
    out=tmp_path/"recommendations.json"
    subprocess.run([sys.executable,str(TOOL),"--inventory",str(p),"--output",str(out)],check=True)
    data=json.loads(out.read_text())
    assert data["policy"]=="recommend_only_until_explicit_install_policy"
    assert data["recommendations"]
    assert all(x["automatic_install"] is False for x in data["recommendations"])
