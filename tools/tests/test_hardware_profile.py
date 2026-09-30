#!/usr/bin/env python3
from pathlib import Path
import json
p=Path(__file__).resolve().parents[2]/'config/services/hardware-requirements.json'
d=json.loads(p.read_text())
assert d['schema']=='chimera-service-hardware-v1'
assert d['fallbacks']['display']=='generic-framebuffer'
assert d['fallbacks']['gpu']=='software-renderer'
assert d['fallbacks']['network']=='offline-mode'
print('PASS: hardware capability fallback contract is valid')
