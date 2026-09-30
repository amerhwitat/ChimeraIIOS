#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
registry = json.loads((ROOT/'config/services/service-registry.json').read_text())
profiles = json.loads((ROOT/'config/services/service-profiles.json').read_text())
services = {s['id']: s for s in registry['services']}
profile = next(p for p in profiles['profiles'] if p['id']=='enterprise-server')
selected=set(profile['services'])
changed=True
while changed:
    changed=False
    for sid in list(selected):
        for dep in services[sid].get('dependencies',[]):
            if dep not in selected: selected.add(dep); changed=True
assert 'chimera.network' in selected
assert 'chimera.storage' in selected
assert 'chimera.security' in selected
assert 'enterprise.web' in selected
assert 'enterprise.fileserver' in selected
assert services['enterprise.web']['critical'] is False
print('PASS: enterprise-server expands dependencies without promoting optional services to critical')
