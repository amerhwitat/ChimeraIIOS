#!/usr/bin/env python3
"""Bounded source/documentation crawler for Chimera's Linux-architecture crosswalk.
It records a dependency map without copying Linux source into ChimeraIIOS.
Default depth is 10. Bootlin may block automated clients; a Git mirror can be supplied.
"""
import argparse, json, re
from collections import deque
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

def crawl(root, depth, limit):
    q=deque([(root,0)]); seen=set(); edges=[]
    while q and len(seen)<limit:
        url,d=q.popleft()
        if url in seen or d>depth: continue
        seen.add(url)
        try:
            req=Request(url,headers={'User-Agent':'ChimeraIIOS-architecture-crawler/1.0'})
            body=urlopen(req,timeout=15).read().decode('utf-8','ignore')
        except Exception as e:
            edges.append({'url':url,'depth':d,'error':str(e)}); continue
        links=re.findall(r'href=["\']([^"\']+)',body,re.I)
        for href in links:
            nxt=urljoin(url,href)
            if urlparse(nxt).netloc==urlparse(root).netloc and nxt not in seen:
                edges.append({'from':url,'to':nxt,'depth':d+1}); q.append((nxt,d+1))
    return {'root':root,'max_depth':depth,'visited':len(seen),'edges':edges}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',default='https://elixir.bootlin.com/linux/v7.2.2/source'); p.add_argument('--depth',type=int,default=10); p.add_argument('--limit',type=int,default=5000); p.add_argument('--out',default='build/linux-depth-map.json'); a=p.parse_args()
    result=crawl(a.root,a.depth,a.limit)
    import pathlib; pathlib.Path(a.out).parent.mkdir(parents=True,exist_ok=True); pathlib.Path(a.out).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f"visited={result['visited']} edges={len(result['edges'])}")
