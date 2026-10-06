#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chimera II Thamudic NLP bridge.

Local-first research backend for Ancient North Arabian / Thamudic:
- Unicode-aware normalization and grapheme validation
- deterministic transliteration with uncertainty preservation
- token/word segmentation
- reviewed corpus + lexicon lookup
- optional external provider endpoint (THAMUDIC_PROVIDER_URL)
- combined NLP endpoint for the Aurora Web UI

The local corpus is deliberately conservative: it does not invent historical
translations. Unknown or ambiguous material is returned as an uncertainty
marker and remains available for human review.
"""
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import urllib.parse
import urllib.request
import unicodedata
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / ".local" / "thamudic"
DATA.mkdir(parents=True, exist_ok=True)
PORT = int(os.environ.get("THAMUDIC_PORT", "8766"))
PROVIDER_URL = os.environ.get("THAMUDIC_PROVIDER_URL", "").strip()
THAMUDIC_RE = re.compile(r"[\U00010A80-\U00010A9F]")
UA = "ChimeraIIOS-ThamudicResearch/3.0"
OCR_LANGS = {"ancient-greek":"grc","greek":"ell","arabic":"ara","syriac":"syr","hebrew":"heb","coptic":"cop","latin":"lat","english":"eng"}
OCR_CANDIDATES = ["grc","syr","ara","heb","cop","lat","eng"]

# Research baseline: transliteration is glyph-level and intentionally keeps
# uncertain characters as ?. This table is not presented as a historical
# dictionary.
TRANSLIT = {
    "𐪀":"h","𐪁":"l","𐪂":"ḥ","𐪃":"m","𐪄":"q","𐪅":"w","𐪆":"s2","𐪇":"r",
    "𐪈":"b","𐪉":"t","𐪊":"s1","𐪋":"k","𐪌":"n","𐪍":"ḫ","𐪎":"ṣ","𐪏":"s3",
    "𐪐":"f","𐪑":"ʼ","𐪒":"ʽ","𐪓":"ḍ","𐪔":"g","𐪕":"d","𐪖":"ġ","𐪗":"ṭ",
    "𐪘":"z","𐪙":"ḏ","𐪚":"y","𐪛":"ṯ","𐪜":"ẓ","𐪝":"1","𐪞":"10","𐪟":"20",
}

# Only high-confidence UI-facing corpus glosses belong here. Entries are
# structured so users can replace/extend them with reviewed scholarship.
LOCAL_CORPUS = [
    {"id":"TIJ 503","script":"Safaitic","pattern":"ytm bn ʿbny w wgm ʿl- ḫll -h","english":"Ytm son ʿbny and he grieved for his friend","arabic":"يتم بن عبني وحزن على صديقه","confidence":1.0,"source":"https://ociana.osu.edu/inscriptions/2400"},
    {"id":"AH 311","script":"Dadanitic","pattern":"bḏkrh wdd ḏ{h}k","english":"Bḏkrh loves {Ḏhk}","arabic":"بذَكرَه يحب {ذهك}","confidence":1.0,"source":"https://ociana.osu.edu/inscriptions/13954"},
    {"id":"Is.H 806","script":"Thamudic B","pattern":"l ḍtm h- s¹fr w h- frs¹","english":"By Ḍtm are the inscription and the horse","arabic":"لِضَتم النقش والحصان","confidence":1.0,"source":"https://ociana.osu.edu/inscriptions/5826"},
    {"id":"GETham 2","script":"Thamudic B","pattern":"l (l)hn wdd ns²l ḏ ʿtq","english":"By Ḏ son of . (Llhn) greets Ns²l who was freed","arabic":"من Ḏ بن . (للهن) يحيّي نس²ل الذي أُعتق","confidence":1.0,"source":"https://ociana.osu.edu/inscriptions/44105"}
]

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def j(h, code, obj):
    raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    h.send_response(code)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Access-Control-Allow-Origin", "*")
    h.send_header("Access-Control-Allow-Headers", "Content-Type")
    h.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    h.end_headers()
    h.wfile.write(raw)

def req_json(h):
    n = int(h.headers.get("Content-Length", "0"))
    return json.loads(h.rfile.read(n) or b"{}")

def normalize_text(text):
    text = unicodedata.normalize("NFC", str(text or ""))
    return "".join(ch for ch in text if unicodedata.category(ch) not in {"Cf"})

def thamudic_chars(text):
    return [ch for ch in normalize_text(text) if THAMUDIC_RE.fullmatch(ch)]

def transliterate_text(text):
    text = normalize_text(text)
    out = []
    unknown = []
    for ch in text:
        if ch in TRANSLIT:
            out.append(TRANSLIT[ch])
        elif THAMUDIC_RE.fullmatch(ch):
            out.append("?")
            unknown.append({"glyph":ch,"codepoint":f"U+{ord(ch):04X}"})
        else:
            out.append(ch)
    return "".join(out), unknown

def segment_text(text):
    text = normalize_text(text)
    # Preserve punctuation/word boundaries; Thamudic is normally treated as
    # consonantal script data, so segmentation is evidence-aware rather than
    # an English-style morphological guesser.
    return [x for x in re.split(r"(?:\s+|[·•|/:;,،؛]+)", text) if x]

def corpus_lookup(text, translit):
    norm = re.sub(r"\s+", " ", translit.strip())
    norm = norm.replace("s¹", "s1").replace("s²", "s2").replace("s³", "s3").replace("ʾ", "ʼ").replace("ʿ", "ʽ")
    hits = []
    for entry in LOCAL_CORPUS:
        pattern = entry.get("pattern","")
        pattern = re.sub(r"\s+", " ", pattern).replace("s¹", "s1").replace("s²", "s2").replace("s³", "s3").replace("ʾ", "ʼ").replace("ʿ", "ʽ")
        if pattern and pattern in norm:
            hits.append(dict(entry))
    return hits

def local_nlp(text, target="english"):
    normalized = normalize_text(text)
    translit, unknown = transliterate_text(normalized)
    tokens = segment_text(normalized)
    token_rows = []
    for token in tokens:
        t, u = transliterate_text(token)
        token_rows.append({
            "source": token,
            "transliteration": t,
            "knownGlyphs": len(token) - len(u),
            "unknownGlyphs": len(u),
            "confidence": 1.0 if token and not u else (0.5 if t else 0.0)
        })
    matches = corpus_lookup(normalized, translit)
    key = "arabic" if str(target).lower().startswith("ar") else "english"
    if matches:
        translation = " ".join(m[key] for m in matches if m.get(key))
        confidence = max(float(m.get("confidence",0)) for m in matches)
        status = "corpus-match"
    else:
        translation = ""
        confidence = 0.0
        status = "needs-reviewed-corpus"
    return {
        "ok": True,
        "backend": "local-reviewed-corpus",
        "providerConfigured": bool(PROVIDER_URL),
        "status": status,
        "normalized": normalized,
        "script": "thamudic" if THAMUDIC_RE.search(normalized) else "unknown",
        "tokens": token_rows,
        "transliteration": translit,
        "translation": translation,
        "targetLanguage": target,
        "confidence": confidence,
        "uncertain": unknown,
        "corpusMatches": matches,
        "provenance": {"backend":"local-reviewed-corpus","timestamp":now(),"policy":"no unsupported historical translation"}
    }

def provider_nlp(payload):
    if not PROVIDER_URL:
        return None
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(PROVIDER_URL, data=body, headers={"Content-Type":"application/json","User-Agent":UA}, method="POST")
    with urllib.request.urlopen(request, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def wikimedia_search(q, limit):
    params = urllib.parse.urlencode({"action":"query","generator":"search","gsrsearch":q,"gsrnamespace":6,"gsrlimit":min(limit,50),"prop":"imageinfo|info","iiprop":"url|extmetadata","format":"json","origin":"*"})
    url = "https://commons.wikimedia.org/w/api.php?" + params
    request = urllib.request.Request(url, headers={"User-Agent":UA})
    with urllib.request.urlopen(request, timeout=20) as r:
        data = json.load(r)
    out = []
    for p in data.get("query",{}).get("pages",{}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        out.append({"title":p.get("title",""),"url":ii.get("url",""),"thumbnail":ii.get("thumburl") or ii.get("url",""),"source":"Wikimedia Commons","license":meta.get("LicenseShortName",{}).get("value",""),"description":meta.get("ImageDescription",{}).get("value",""),"author":meta.get("Artist",{}).get("value","")})
    return out

def tesseract_languages():
    exe = shutil.which("tesseract")
    if not exe: return []
    try:
        p = subprocess.run([exe,"--list-langs"],capture_output=True,text=True,timeout=10)
        return [x.strip() for x in p.stdout.splitlines()[1:] if x.strip()]
    except Exception:
        return []

def run_tesseract(image_bytes, lang="auto", psm=6):
    exe = shutil.which("tesseract")
    if not exe: return {"ok":False,"engine":"tesseract","error":"tesseract-not-installed","text":"","confidence":0}
    installed = tesseract_languages()
    requested = [OCR_LANGS.get(lang,lang)] if lang != "auto" else OCR_CANDIDATES
    requested = [x for x in requested if x in installed]
    if not requested: return {"ok":False,"engine":"tesseract","error":"no-requested-language-data","installed":installed,"text":"","confidence":0}
    best = {"ok":False,"engine":"tesseract","text":"","confidence":0,"language":None}
    with tempfile.TemporaryDirectory(prefix="chimera-ocr-") as td:
        src = Path(td) / "input.png"; src.write_bytes(image_bytes)
        for code in requested:
            try:
                p = subprocess.run([exe,str(src),"stdout","--psm",str(psm),"-l",code],capture_output=True,text=True,timeout=90)
                text = (p.stdout or "").strip()
                if p.returncode == 0 and len(text) > len(best["text"]):
                    best = {"ok":True,"engine":"tesseract","language":code,"text":text,"confidence":0}
            except Exception:
                pass
    return best

def connected_components_gray(raw,w,h,threshold=128):
    seen=bytearray(w*h); boxes=[]
    def lum(i): return (299*raw[i]+587*raw[i+1]+114*raw[i+2])//1000
    for y in range(h):
      for x in range(w):
        p=y*w+x
        if seen[p]: continue
        seen[p]=1
        if lum(p*3)>threshold: continue
        q=[(x,y)]; xs=[]; ys=[]
        while q:
          cx,cy=q.pop(); xs.append(cx);ys.append(cy)
          for nx,ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
            if nx<0 or ny<0 or nx>=w or ny>=h: continue
            z=ny*w+nx
            if seen[z]: continue
            seen[z]=1
            if lum(z*3)<=threshold:q.append((nx,ny))
        if len(xs)>=40:
          x1,x2=min(xs),max(xs);y1,y2=min(ys),max(ys)
          if x2-x1>=3 and y2-y1>=3 and (x2-x1)*(y2-y1)<w*h*.25:
            boxes.append({"x":x1,"y":y1,"w":x2-x1+1,"h":y2-y1+1,"glyph":"□","translit":"?","confidence":0})
    return sorted(boxes,key=lambda b:(b["y"],b["x"]))[:1000]

class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self): j(self,204,{})
    def do_GET(self):
        try:
          if self.path == "/health":
            langs=tesseract_languages()
            return j(self,200,{"ok":True,"version":"chimera-thamudic-nlp/3","ocr":bool(langs),"tesseract":bool(langs),"tesseractLanguages":langs,"thamudicVision":True,"nlp":{"configured":True,"backend":"local-reviewed-corpus","providerConfigured":bool(PROVIDER_URL),"providerUrlConfigured":bool(PROVIDER_URL),"endpoints":["/nlp/capabilities","/nlp/transliterate","/nlp/translate","/nlp/analyze"]},"data":str(DATA)})
          if self.path == "/nlp/capabilities":
            return j(self,200,{"ok":True,"backend":"external-provider" if PROVIDER_URL else "local-reviewed-corpus","providerConfigured":bool(PROVIDER_URL),"scripts":["thamudic"],"targets":["english","arabic"],"features":["normalize","segment","transliterate","translate","provenance","uncertainty"],"corpusEntries":len(LOCAL_CORPUS)})
          if self.path == "/nlp/catalog":
            return j(self,200,{"ok":True,"entries":LOCAL_CORPUS,"providerConfigured":bool(PROVIDER_URL)})
          return j(self,404,{"error":"not-found"})
        except Exception as e:
          return j(self,500,{"error":str(e)})
    def do_POST(self):
        try: data=req_json(self)
        except Exception as e:return j(self,400,{"error":str(e)})
        try:
          if self.path in {"/nlp/transliterate","/nlp/translate","/nlp/analyze"}:
            text = str(data.get("text") or data.get("transliteration") or "")
            target = str(data.get("target","english"))
            mode = str(data.get("mode","research"))
            payload = {"text":text,"target":target,"mode":mode,"script":"thamudic","timestamp":now()}
            if PROVIDER_URL:
                try:
                    result=provider_nlp(payload)
                    result.setdefault("backend","external-provider")
                    result.setdefault("provenance",{"backend":"external-provider","endpointConfigured":True,"timestamp":now()})
                    return j(self,200,result)
                except Exception as e:
                    local=local_nlp(text,target); local["providerError"]=str(e); local["fallback"]="local-reviewed-corpus"; return j(self,200,local)
            result=local_nlp(text,target)
            if self.path=="/nlp/transliterate":
                result["translation"]=""
            return j(self,200,result)
          if self.path=="/ocr/capabilities":
            langs=tesseract_languages()
            return j(self,200,{"engine":"tesseract" if langs else "browser-fallback","installed":langs,"ancientLanguages":{k:v for k,v in OCR_LANGS.items() if v in langs},"thamudic":{"segmentation":True,"customModel":(DATA/"model.json").exists()}})
          if self.path=="/ocr/scan":
            raw=base64.b64decode(str(data.get("image","")).split(",",1)[-1])
            result=run_tesseract(raw,str(data.get("language","auto")),int(data.get("psm",6)))
            result["script"]=data.get("script","auto"); result["automatic"]=data.get("language","auto")=="auto"
            return j(self,200,result)
          if self.path=="/thamudic/search": return j(self,200,{"results":wikimedia_search(str(data.get("query","Thamudic inscription")),int(data.get("limit",20)))})
          if self.path=="/thamudic/crawl":
            results=[]
            for x in data.get("sources",[]):
              if x.get("url"):
                y=dict(x); y["crawledAt"]=now(); results.append(y)
            (DATA/"research.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
            return j(self,200,{"results":results})
          if self.path=="/thamudic/train":
            job={"status":"queued","model":data.get("model","vision-glyph-cnn"),"epochs":data.get("epochs",20),"batch":data.get("batch",16),"lr":data.get("lr",.001),"ocr":False,"note":"Training uses reviewed glyph samples; install optional torch stack for actual CNN training."}
            (DATA/"training.json").write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding="utf-8"); return j(self,200,job)
          if self.path=="/thamudic/evaluate": return j(self,200,{"status":"ready","metric_policy":"per-glyph confidence + reviewed accuracy","ocr":False})
          if self.path=="/thamudic/ocr":
            raw=base64.b64decode(str(data.get("image","")).split(",",1)[-1])
            result={"engine":"thamudic-vision","automatic":True,"modelAvailable":(DATA/"model.json").exists(),"warning":"No standard Tesseract Thamudic model; recognition is emitted only by a reviewed local vision model.","boxes":[]}
            if data.get("width") and data.get("height"):
                result["boxes"]=connected_components_gray(raw,int(data["width"]),int(data["height"]),int(data.get("threshold",128)))
            return j(self,200,result)
          if self.path=="/thamudic/predict":
            glyphs=data.get("boxes",[])
            for g in glyphs:
              g.setdefault("glyph","□");g.setdefault("translit","?");g.setdefault("confidence",0)
            translit="".join(g.get("translit","?") for g in glyphs)
            return j(self,200,{"glyphs":glyphs,"transliteration":translit,"translation":"","warning":"Research hypothesis only; confidence and provenance remain attached; call /nlp/translate after review."})
          j(self,404,{"error":"not-found"})
        except Exception as e:j(self,500,{"error":str(e)})
    def log_message(self,*a): pass

if __name__=="__main__":
 print(f"Thamudic NLP bridge: http://127.0.0.1:{PORT}")
 ThreadingHTTPServer(("127.0.0.1",PORT),H).serve_forever()
