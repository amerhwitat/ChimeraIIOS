#!/usr/bin/env python3
"""Chimera II local PyPDF bridge. PDF bytes stay local and are never published."""
import base64,json,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
try:
    from pypdf import PdfReader
except Exception:
    PdfReader=None
PORT=8767
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,code,obj):
        raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Access-Control-Allow-Origin","*");self.send_header("Access-Control-Allow-Headers","Content-Type");self.end_headers();self.wfile.write(raw)
    def do_OPTIONS(self): self.send(204,{})
    def do_GET(self):
        if self.path=="/health": return self.send(200,{"ok":True,"pypdf":PdfReader is not None,"port":PORT})
        return self.send(404,{"error":"not-found"})
    def do_POST(self):
        if self.path!="/pdf/read": return self.send(404,{"error":"not-found"})
        if PdfReader is None:return self.send(503,{"error":"pypdf-not-installed","hint":"python -m pip install pypdf"})
        try:
            n=int(self.headers.get("Content-Length","0"));d=json.loads(self.rfile.read(n));raw=base64.b64decode(d["pdf"]);from io import BytesIO
            reader=PdfReader(BytesIO(raw));pages=[]
            for i,p in enumerate(reader.pages):
                try:t=p.extract_text() or ""
                except Exception as e:t="[page extraction error: %s]"%e
                pages.append({"page":i+1,"text":t})
            meta={str(k):str(v) for k,v in (reader.metadata or {}).items()}
            return self.send(200,{"ok":True,"filename":d.get("filename",""),"pages":len(reader.pages),"text":"\n\n".join("=== Page %d ===\n%s"%(x["page"],x["text"]) for x in pages),"metadata":meta})
        except Exception as e:return self.send(400,{"error":str(e)})
ThreadingHTTPServer(("127.0.0.1",PORT),Handler).serve_forever()
