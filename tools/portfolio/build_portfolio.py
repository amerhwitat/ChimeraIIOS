#!/usr/bin/env python3
"""Recursive portfolio source importer/builder for the Chimera II ISO pipeline.

This tool never executes downloaded archives or post-install scripts. It clones
pinned/default branches, inventories source/build systems, and invokes only
recognized build commands in isolated working trees. Failures are recorded.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path

REPOS = [
 ("chimera-ii-os","https://github.com/amerhwitat/ChimeraIIOS"),
 ("bizx","https://github.com/amerhwitat/BizX"), ("bizxtreme","https://github.com/amerhwitat/BizXtreme"),
 ("general","https://github.com/amerhwitat/general"), ("nlp","https://github.com/amerhwitat/nlp"),
 ("cpu4096","https://github.com/amerhwitat/CPU4096"), ("cpu4096-simulator","https://github.com/amerhwitat/CPU4096Simulator"),
 ("pdfreaderpy","https://github.com/amerhwitat/PDFreaderPY"), ("eth-key-check","https://github.com/amerhwitat/eth-key-check"),
 ("keygen","https://github.com/amerhwitat/keygen"), ("bruteforce","https://github.com/amerhwitat/bruteforce"),
 ("test","https://github.com/amerhwitat/test")
]
def sha256(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def run(cmd,cwd,log):
 r=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1800)
 log.append({"cmd":cmd,"cwd":str(cwd),"returncode":r.returncode,"output":r.stdout[-12000:]})
 return r.returncode
def build_one(repo,src,out,log):
 markers=[(src/"CMakeLists.txt",["cmake","-S",".","-B","build","-DCMAKE_BUILD_TYPE=Release"],["cmake","--build","build","--parallel"]),
           (src/"Makefile",["make","-j2"],None),(src/"package.json",["npm","install","--ignore-scripts"],["npm","run","build"]),
           (src/"Cargo.toml",["cargo","build","--release"],None),(src/"pom.xml",["mvn","-B","-DskipTests","package"],None),
           (src/"build.gradle",["gradle","build","-x","test"],None),(src/"build.gradle.kts",["gradle","build","-x","test"],None)]
 for marker,pre,post in markers:
  if marker.exists():
   if shutil.which(pre[0]):
    rc=run(pre,src,log)
    if rc==0 and post and shutil.which(post[0]): run(post,src,log)
   else: log.append({"skip":"missing-tool","tool":pre[0]})
   break
 # Python projects are syntax-checked, not pip-installed.
 for p in src.rglob("*.py"):
  if ".git" not in p.parts:
   run(["python3","-m","py_compile",str(p)],src,log)
 # Stage common artifacts without guessing executability.
 for p in src.rglob("*"):
  if not p.is_file() or ".git" in p.parts: continue
  if p.suffix.lower() in {".so",".a",".dll",".lib",".exe",".elf",".bin",".img",".efi",".apk",".jar",".war",".wasm"}:
   d=out/"binaries"/repo; d.mkdir(parents=True,exist_ok=True); shutil.copy2(p,d/p.name)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); ap.add_argument("--references"); a=ap.parse_args()
 root=Path(a.output).resolve(); sources=root/"src"; root.mkdir(parents=True,exist_ok=True); sources.mkdir(exist_ok=True)
 report={"schema":"chimera-portfolio-build-v1","repositories":{},"references":{}}
 for rid,url in REPOS:
  dst=sources/rid; log=[]
  try:
   if not (dst/".git").exists(): run(["git","clone","--depth","1",url,str(dst)],root,log)
   else: run(["git","pull","--ff-only"],dst,log)
   build_one(rid,dst,root,log); report["repositories"][rid]={"url":url,"status":"processed","log":log}
  except Exception as e: report["repositories"][rid]={"url":url,"status":"failed","error":repr(e),"log":log}
 if a.references:
  refroot=Path(a.references); target=root/"docs"/"references"; target.mkdir(parents=True,exist_ok=True)
  for name in ["w2K-source.pdf","Win32API-x86-x64_2.docx","W2K-ASM.txt"]:
   p=refroot/name
   if p.exists():
    q=target/name; shutil.copy2(p,q); report["references"][name]={"sha256":sha256(q),"size":q.stat().st_size}
 report["policy"]="Source is preserved; failures are explicit; remote post-install scripts are not executed."
 (root/"portfolio-build-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report,indent=2))
if __name__=="__main__": main()
