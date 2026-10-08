import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SEC=ROOT/'tools/security'
def test_python_modules_compile():
    for p in SEC.glob('*.py'):
        subprocess.run([sys.executable,'-m','py_compile',str(p)],check=True)
def test_eicar_detection():
    p=Path(tempfile.mktemp(suffix='.com'))
    try:
        p.write_bytes(b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
        out=subprocess.check_output([sys.executable,str(SEC/'chimera_securityd.py'),'scan',str(p),'--no-clamav','--no-yara'],text=True)
        data=json.loads(out)
        assert data['verdict']=='malicious'
        assert 'EICAR-test-signature' in data['detections']
    finally: p.unlink(missing_ok=True)
def test_firewall_render():
    import importlib.util
    spec=importlib.util.spec_from_file_location('cf',SEC/'chimera_firewall.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    pol=m.load(ROOT/'system/security/firewall-policy.json')
    for name in pol['profiles']:
        rules=m.render(name,pol)
        assert 'table inet chimera' in rules and 'chain input' in rules
