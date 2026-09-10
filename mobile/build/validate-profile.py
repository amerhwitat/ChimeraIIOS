#!/usr/bin/env python3
import json, sys
from pathlib import Path

REQUIRED = {'id', 'architecture', 'soc', 'boot', 'partitions', 'security'}

def main(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    missing = REQUIRED - set(data)
    if missing:
        raise SystemExit('missing profile fields: ' + ', '.join(sorted(missing)))
    if data['architecture'] not in {'aarch64', 'armv7'}:
        raise SystemExit('unsupported architecture')
    if not isinstance(data['partitions'], list) or not data['partitions']:
        raise SystemExit('partitions must be a non-empty list')
    if data['security'].get('avb') and not data['security'].get('unlockRequired'):
        raise SystemExit('AVB profile must declare unlock/signing policy')
    print(f"VALID {data['id']} ({data['architecture']})")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: validate-profile.py PROFILE.json')
    main(sys.argv[1])
