#!/bin/sh
set -eu
PLATFORM=${CHIMERA_ROM_PLATFORM:-all}
QUERY=${*:-"PlayStation public domain homebrew ROM ISO"}
MAX=${CHIMERA_ROM_SEARCH_MAX:-25}
OUT=${CHIMERA_ROM_SEARCH_OUT:-}
case "$PLATFORM" in
  PSX|PS1) PLATFORM_QUERY="PSX OR PS1" ;;
  PS2) PLATFORM_QUERY="PS2" ;;
  PS3) PLATFORM_QUERY="PS3" ;;
  PS4) PLATFORM_QUERY="PS4" ;;
  PS5) PLATFORM_QUERY="PS5" ;;
  all|ALL) PLATFORM_QUERY="PSX OR PS1 OR PS2 OR PS3 OR PS4 OR PS5" ;;
  *) echo "Unsupported platform: $PLATFORM" >&2; exit 2 ;;
esac
SAFE_QUERY="$PLATFORM_QUERY $QUERY (homebrew OR "public domain" OR "open source" OR "creative commons" OR demo)"
if command -v python3 >/dev/null 2>&1; then
python3 - "$SAFE_QUERY" "$MAX" "$OUT" <<'PY'
import html,re,sys,urllib.parse,urllib.request
q=sys.argv[1]; limit=int(sys.argv[2]); out=sys.argv[3]
engines=[
 ("duckduckgo","https://html.duckduckgo.com/html/?q="+urllib.parse.quote_plus(q)),
 ("bing","https://www.bing.com/search?q="+urllib.parse.quote_plus(q))]
blocked=re.compile(r"\b(pirated|warez|crack|keygen|commercial[ _-]?rom|bios[ _-]?download)\b",re.I)
rows=[]
for engine,url in engines:
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"ChimeraIIOS-ROM-Search/1.0"})
  data=urllib.request.urlopen(req,timeout=12).read().decode("utf-8","ignore")
 except Exception as e:
  print(f"# {engine}: search unavailable: {e}",file=sys.stderr); continue
 for href,title in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',data,re.I|re.S):
  title=re.sub("<[^>]+>"," ",title); title=html.unescape(re.sub(r"\s+"," ",title)).strip()
  href=html.unescape(href)
  if not href.startswith("http") or blocked.search(title+" "+href): continue
  rows.append((title,href,engine))
  if len(rows)>=limit: break
 if len(rows)>=limit: break
seen=set(); dest=open(out,"w",encoding="utf-8") if out else sys.stdout
print("platform\ttitle\turl\tsource\trights_hint\tquery",file=dest)
for title,url,engine in rows:
 if url in seen: continue
 seen.add(url)
 print(f"{PLATFORM}\t{title.replace(chr(9),' ')}\t{url}\t{engine}\tVERIFY_LICENSE_BEFORE_IMPORT\t{q.replace(chr(9),' ')}",file=dest)
if out: dest.close()
print(f"Found {len(seen)} candidate results. Discovery only; no files were downloaded.",file=sys.stderr)
PY
else
 echo "Python 3 is required for deep web search." >&2; exit 1
fi
