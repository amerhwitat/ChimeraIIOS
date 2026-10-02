#!/usr/bin/env python3
"""Refresh a local manifest of publicly documented mobile OS/firmware sources.

This tool records source metadata; it does not bypass access controls or download
proprietary firmware automatically. Vendor authorization and device compatibility
remain separate gates in the Chimera Mobile deployment pipeline.
"""
import json, sys, urllib.request, urllib.error, datetime

catalog_path = sys.argv[1] if len(sys.argv) > 1 else 'mobile-os-catalog.json'
with open(catalog_path, encoding='utf-8') as f:
    catalog = json.load(f)

results=[]
for item in catalog.get('sources', []):
    url=item['url']
    status='unknown'
    detail=''
    try:
        req=urllib.request.Request(url, headers={'User-Agent':'ChimeraIIOS-Mobile-Discovery/1.0'})
        with urllib.request.urlopen(req, timeout=12) as r:
            status='reachable' if 200 <= r.status < 400 else f'http-{r.status}'
            detail=r.geturl()
    except urllib.error.HTTPError as e:
        status=f'http-{e.code}'
        detail=e.geturl() or url
    except Exception as e:
        status='unreachable'
        detail=str(e)
    results.append({**item, 'status':status, 'resolved_url':detail})

out={
    'schema':1,
    'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'policy':'metadata discovery only; no lock bypass or proprietary firmware redistribution',
    'sources':results,
}
json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
print()
