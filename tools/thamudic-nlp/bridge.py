#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chimera II Thamudic NLP local bridge. Vision-first; no OCR/Tesseract."""
import base64, json, os, re, shutil, subprocess, tempfile, threading, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/".local"/"thamudic"
DATA.mkdir(parents=True,exist_ok=True)
PORT=8766
THAMUDIC_RE=re.compile(r"[\U00010A80-\U00010A9F]")
UA="ChimeraIIOS-ThamudicResearch/2.0"
OCR_LANGS={"ancient-greek":"grc","greek":"ell","arabic":"ara","syriac":"syr","hebrew":"heb","coptic":"cop","latin":"lat","english":"eng"}
OCR_CANDIDATES=["grc","syr","ara","heb","cop","lat","eng"]

def j(h,code,obj):
    raw=json.dumps(obj,ensure_ascii=False).encode()
    h.send_response(code); h.send_header("Content-Type","application/json; charset=utf-8")
    h.send_header("Access-Control-Allow-Origin","*"); h.send_header("Access-Control-Allow-Headers","Content-Type")
    h.end_headers(); h.wfile.write(raw)

def req_json(h):
    n=int(h.headers.get("Content-Length","0")); return json.loads(h.rfile.read(n) or b"{}")

def wikimedia_search(q,limit):
    params=urllib.parse.urlencode({"action":"query","generator":"search","gsrsearch":q,"gsrnamespace":6,"gsrlimit":min(limit,50),"prop":"imageinfo|info","iiprop":"url|extmetadata","format":"json","origin":"*"})
    url="https://commons.wikimedia.org/w/api.php?"+params
    request=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(request,timeout=20) as r: data=json.load(r)
    out=[]
    for p in data.get("query",{}).get("pages",{}).values():
        ii=(p.get("imageinfo") or [{}])[0]; meta=ii.get("extmetadata") or {}
        out.append({"title":p.get("title",""),"url":ii.get("url",""),"thumbnail":ii.get("thumburl") or ii.get("url",""),"source":"Wikimedia Commons","license":meta.get("LicenseShortName",{}).get("value",""),"description":meta.get("ImageDescription",{}).get("value",""),"author":meta.get("Artist",{}).get("value","")})
    return out

def tesseract_languages():
    exe=shutil.which("tesseract")
    if not exe: return []
    try:
        p=subprocess.run([exe,"--list-langs"],capture_output=True,text=True,timeout=10)
        return [x.strip() for x in p.stdout.splitlines()[1:] if x.strip()]
    except Exception:
        return []

def run_tesseract(image_bytes,lang="auto",psm=6):
    exe=shutil.which("tesseract")
    if not exe: return {"ok":False,"engine":"tesseract","error":"tesseract-not-installed","text":"","confidence":0}
    installed=tesseract_languages()
    requested=[OCR_LANGS.get(lang,lang)] if lang!="auto" else OCR_CANDIDATES
    requested=[x for x in requested if x in installed]
    if not requested: return {"ok":False,"engine":"tesseract","error":"no-requested-language-data","installed":installed,"text":"","confidence":0}
    best={"ok":False,"engine":"tesseract","text":"","confidence":0,"language":None}
    with tempfile.TemporaryDirectory(prefix="chimera-ocr-") as td:
        src=Path(td)/"input.png"; src.write_bytes(image_bytes)
        for code in requested:
            try:
                p=subprocess.run([exe,str(src),"stdout","--psm",str(psm),"-l",code],capture_output=True,text=True,timeout=90)
                text=(p.stdout or "").strip()
                if p.returncode==0 and len(text)>len(best["text"]):
                    best={"ok":True,"engine":"tesseract","language":code,"text":text,"confidence":0}
            except Exception:
                pass
    return best

def connected_components_gray(raw,w,h,threshold=128):
    # raw = RGB bytes. Return coarse boxes; detailed segmentation can be upgraded locally with numpy/OpenCV-free PIL.
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
          if x2-x1>=3 and y2-y1>=3 and (x2-x1)*(y2-y1)<w*h*.25: boxes.append({"x":x1,"y":y1,"w":x2-x1+1,"h":y2-y1+1,"glyph":"□","translit":"?","confidence":0})
    return sorted(boxes,key=lambda b:(b["y"],b["x"]))[:1000]

class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self): j(self,204,{})
    def do_GET(self):
        if self.path=="/health":
            langs=tesseract_languages()
            return j(self,200,{"ok":True,"version":"chimera-thamudic-nlp/2","ocr":bool(langs),"tesseract":bool(langs),"tesseractLanguages":langs,"thamudicVision":True,"data":str(DATA)})
        j(self,404,{"error":"not-found"})
    def do_POST(self):
        try: data=req_json(self)
        except Exception as e:return j(self,400,{"error":str(e)})
        try:
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
                y=dict(x); y["crawledAt"]=__import__("datetime").datetime.utcnow().isoformat()+"Z"; results.append(y)
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
            # Do not invent historical readings. Return existing labels or uncertainty.
            for g in glyphs:
              g.setdefault("glyph","□");g.setdefault("translit","?");g.setdefault("confidence",0)
            return j(self,200,{"glyphs":glyphs,"transliteration":"".join(g.get("translit","?") for g in glyphs),"translation":"","warning":"Research hypothesis only; confidence and provenance remain attached; no unsupported historical translation generated."})
          j(self,404,{"error":"not-found"})
        except Exception as e:j(self,500,{"error":str(e)})
    def log_message(self,*a): pass

if __name__=="__main__":
 print(f"Thamudic NLP bridge: http://127.0.0.1:{PORT}")
 ThreadingHTTPServer(("127.0.0.1",PORT),H).serve_forever()
