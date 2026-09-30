#!/usr/bin/env python3
import json
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'boot/chimera-measurement-policy.json'
d=json.loads(p.read_text())
assert d['schema']=='chimera-measurement-policy-v1'
ids=[x['id'] for x in d['stages']]
assert ids == ['spitfire','jasper','koronos','boot-modules','rootfs','critical-services']
assert all(x['required'] for x in d['stages'])
assert d['tpm']=='optional-if-present'
assert d['failure_action']=='jasper-recovery'
assert d['development_mode']['visible_warning'] is True
print('PASS: measured boot policy is valid')
