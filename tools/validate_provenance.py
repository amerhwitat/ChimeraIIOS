#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
ALLOWED_INTEGRATIONS={"adapter","reference","fetched","vendored"}

def load_registry(path:Path=ROOT/'opensource/sources.json'):
    data=json.loads(path.read_text(encoding='utf-8'))
    assert data['schema']=='CHM-OSS-SOURCES-1'
    ids=set()
    for item in data['sources']:
        assert item['id'] not in ids
        ids.add(item['id'])
        assert urlparse(item['upstream']).scheme=='https'
        assert item['spdx'] and item['languages'] and item['platforms']
        assert item['integration'] in ALLOWED_INTEGRATIONS
        assert item['security']['execute_on_fetch'] is False
    return data

if __name__=='__main__':
    data=load_registry(); print(f"validated {len(data['sources'])} open-source records")
