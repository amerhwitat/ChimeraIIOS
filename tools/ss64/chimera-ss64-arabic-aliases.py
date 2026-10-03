#!/usr/bin/env python3
"""Extract command names/descriptions from SS64 indexes and generate Arabic aliases.

This stores command metadata and short Arabic labels, not copied SS64 articles.
Network access is optional; use --offline with a previously saved index.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from urllib.parse import urljoin

try:
    import urllib.request
except ImportError:
    urllib = None

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runtime" / "commands" / "ss64"
DEFAULT_INDEXES = {
    "bash": "https://ss64.com/bash/",
    "windows": "https://ss64.com/nt/",
    "powershell": "https://ss64.com/ps/",
}
AR = {
    "ls":"عرض", "cd":"دخول", "pwd":"مسار", "cp":"نسخ", "mv":"نقل", "rm":"حذف",
    "mkdir":"أنشئ", "rmdir":"احذف_مجلد", "cat":"اقرأ", "less":"تصفح", "more":"تصفح",
    "head":"بداية", "tail":"نهاية", "grep":"ابحث", "find":"اعثر", "locate":"حدد",
    "which":"أين", "whereis":"مكان", "type":"نوع", "command":"أمر", "alias":"اختصار",
    "unalias":"احذف_اختصار", "echo":"اطبع", "printf":"اطبع_منسق", "clear":"نظف",
    "history":"سجل", "help":"مساعدة", "man":"دليل", "apropos":"ابحث_دليل", "env":"بيئة",
    "export":"صدّر", "source":"مصدر", "exec":"نفذ", "chmod":"صلاحيات", "chown":"مالك",
    "ps":"عمليات", "top":"مراقب", "kill":"أوقف", "jobs":"مهام", "fg":"واجهة", "bg":"خلفية",
    "tar":"أرشفة", "gzip":"ضغط", "gunzip":"فك_ضغط", "zip":"ضغط_ملف", "unzip":"فك_ملف",
    "ssh":"اتصال_آمن", "scp":"نسخ_آمن", "sftp":"ملفات_آمنة", "ping":"اختبر_اتصال",
    "ip":"شبكة", "curl":"طلب_ويب", "wget":"تنزيل", "df":"مساحة", "du":"حجم",
    "mount":"اربط", "umount":"افصل", "fdisk":"أقسام", "dd":"نسخ_خام", "date":"تاريخ",
    "whoami":"من_أنا", "uname":"النظام", "sudo":"صلاحيات_عليا", "apt":"حزم", "apt-get":"حزم_متقدمة",
    "systemctl":"خدمات", "journalctl":"سجل_النظام", "bash":"باش", "python":"بايثون",
    "python3":"بايثون3", "git":"جت", "make":"بناء", "gcc":"مترجم_سي", "g++":"مترجم_سي_بلس",
    "javac":"مترجم_جافا", "java":"جافا", "cargo":"كارجو", "rustc":"مترجم_راست",
    "cmd":"موجه_الأوامر", "dir":"عرض_ويندوز", "copy":"نسخ_ويندوز", "move":"نقل_ويندوز",
    "del":"حذف_ويندوز", "mkdir":"أنشئ_ويندوز", "rmdir":"احذف_مجلد_ويندوز", "cls":"نظف_الشاشة",
    "ipconfig":"إعداد_الشبكة", "ping":"اختبر_الشبكة", "tasklist":"قائمة_المهام", "taskkill":"أوقف_مهمة",
    "powershell":"باورشيل", "start":"ابدأ", "where":"أين_ويندوز", "set":"اضبط", "help":"مساعدة",
}

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent":"ChimeraIIOS-SS64-Indexer/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def parse_index(html: str, base: str, shell: str):
    # SS64 indexes expose command names as link text. Avoid copying page bodies.
    from html.parser import HTMLParser
    class P(HTMLParser):
        def __init__(self): super().__init__(); self.a=False; self.href=''; self.buf=[]; self.rows=[]
        def handle_starttag(self,t,a):
            if t=='a': self.a=True; self.href=dict(a).get('href',''); self.buf=[]
        def handle_data(self,d):
            if self.a: self.buf.append(d)
        def handle_endtag(self,t):
            if t=='a' and self.a:
                name=' '.join(''.join(self.buf).split())
                if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+-]*', name) and len(name)<=32:
                    self.rows.append((name,urljoin(base,self.href)))
                self.a=False
    p=P(); p.feed(html)
    seen=set(); out=[]
    for name,url in p.rows:
        key=name.lower()
        if key in seen: continue
        seen.add(key)
        out.append({"command":name,"arabic":AR.get(key, f"أمر_{key.replace('-','_')}"),"shell":shell,"source":url})
    return out

def alias_line(item):
    a=item['arabic']; c=item['command']
    # Arabic identifiers are accepted by modern shells; quote the RHS.
    return f"alias {a}='{c}'"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--offline-dir',type=Path); ap.add_argument('--shell',choices=DEFAULT_INDEXES,action='append'); ap.add_argument('--out',type=Path,default=OUT); ap.add_argument('--limit',type=int,default=0); args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    shells=args.shell or list(DEFAULT_INDEXES)
    all_items=[]
    for shell in shells:
        path=(args.offline_dir / f'{shell}.html') if args.offline_dir else None
        if path and path.exists(): html=path.read_text(encoding='utf-8',errors='replace')
        else:
            try: html=fetch(DEFAULT_INDEXES[shell])
            except Exception as e:
                print(f'[WARN] unable to fetch {shell}: {e}',file=sys.stderr); continue
        items=parse_index(html,DEFAULT_INDEXES[shell],shell)
        if args.limit: items=items[:args.limit]
        (args.out/f'{shell}.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (args.out/f'{shell}.bash_aliases').write_text('\n'.join(alias_line(x) for x in items)+'\n',encoding='utf-8')
        all_items.extend(items)
    manifest={"schema":1,"generator":"ChimeraIIOS SS64 Arabic Alias Generator","source":"https://ss64.com/","policy":"command metadata and short Arabic labels; do not mirror SS64 article text","commands":all_items}
    (args.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'[OK] generated {len(all_items)} command aliases in {args.out}')

if __name__=='__main__': main()
