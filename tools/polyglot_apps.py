#!/usr/bin/env python3
"""Inventory, GUI launcher and PyInstaller packager for first-party Python/Java/Web apps."""
from __future__ import annotations
import argparse,json,pathlib,re,shutil,subprocess,sys
SKIP={".git",".venv","venv","__pycache__","node_modules","vendor","tests","test","build","dist",".pytest_cache",".chimera-fix-backups"}
WEB={".html",".htm",".js",".jsx",".ts",".tsx",".css"}
def inventory(root):
    py=[];java=[];web=[]
    for p in sorted(root.rglob("*")):
        if not p.is_file():continue
        rel=p.relative_to(root)
        if any(x in SKIP for x in rel.parts):continue
        if p.suffix==".py":
            src=p.read_text(encoding="utf-8",errors="replace")
            entry=p.name in {"main.py","__main__.py"} or p.name.startswith("launch") or bool(re.search(r"""if\s+__name__\s*==\s*["']__main__["']""",src))
            py.append({"id":"py-"+re.sub(r"[^a-z0-9]+","-",rel.as_posix().lower()).strip("-"),"name":p.stem.replace("_"," ").title(),"kind":"python-entrypoint" if entry else "python-module","source":rel.as_posix(),"platforms":["Linux","Windows"],"gui":"Tkinter GUI wrapper" if entry else "Library/module; no standalone GUI","build":"inventory-only"})
        elif p.suffix==".java":java.append(rel.as_posix())
        elif p.suffix.lower() in WEB:web.append(rel.as_posix())
    return py,java,web
def call(cmd,cwd):return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
def make_wrapper(source,name):
    return """import pathlib,subprocess,sys,tkinter as tk
from tkinter import ttk,messagebox
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT/"""+repr(source)+"""
def main():
 w=tk.Tk();w.title("""+repr(name)+"""+" — App");w.geometry("900x620")
 ttk.Label(w,text="""+repr(name)+""",font=("Segoe UI",16,"bold")).pack(anchor="w",padx=16,pady=12)
 out=tk.Text(w,wrap="word");out.pack(fill="both",expand=True,padx=16,pady=8)
 def launch():
  if not SOURCE.is_file():messagebox.showerror("Missing source",str(SOURCE));return
  p=subprocess.Popen([sys.executable,str(SOURCE)],cwd=str(SOURCE.parent),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  text,_=p.communicate();out.insert("end",(text or "No console output.")+"\\nExit code: "+str(p.returncode)+"\\n")
 bar=ttk.Frame(w);bar.pack(fill="x",padx=16,pady=12)
 ttk.Button(bar,text="Run",command=launch).pack(side="left")
 ttk.Button(bar,text="Close",command=w.destroy).pack(side="right")
 w.mainloop()
if __name__=="__main__":main()
"""
def build(root,out,platform):
    py,java,web=inventory(root);out.mkdir(parents=True,exist_ok=True);dist=out/"dist";dist.mkdir(exist_ok=True);tool=shutil.which("pyinstaller")
    for app in py:
        if app["kind"]!="python-entrypoint":continue
        app["build"]="source-only: PyInstaller unavailable"
        if not tool:continue
        wrapper=out/(app["id"]+".py");wrapper.write_text(make_wrapper(app["source"],app["name"]));name=app["id"][3:]
        r=call([tool,"--noconfirm","--clean","--onefile","--windowed","--name",name,"--distpath",str(dist),str(wrapper)],root)
        app["build"]="built" if r.returncode==0 else "failed";app["log"]=r.stdout[-2000:]
        app["artifact"]=str((dist/(name+(".exe" if platform=="windows" else ""))).relative_to(out)) if r.returncode==0 else None
    pom=next(iter(root.rglob("pom.xml")),None);java_status="sources inventoried; no Maven project" if java else "no Java sources"
    if pom and shutil.which("mvn"):
        r=call(["mvn","-B","-f",str(pom),"package","-DskipTests"],root);java_status="built" if r.returncode==0 else "failed"
    elif java and not shutil.which("javac"):java_status="sources inventoried; JDK unavailable"
    data={"schema":"chimera-polyglot-apps/v1","platform_build":platform,"python_source_count":len(py),"python_entrypoints":sum(a["kind"]=="python-entrypoint" for a in py),"java_source_count":len(java),"web_source_count":len(web),"java_build":java_status,"python":py,"java_sources":java,"web_sources":web,"compatibility":{"windows":"Build PyInstaller .exe on Windows; Windows binaries are not Linux executables.","wine":"Optional Wine runtime may launch compatible Windows .exe files; not guaranteed for every app.","linux":"Build separate Linux-native PyInstaller artifacts."}}
    (out/"polyglot-apps.json").write_text(json.dumps(data,indent=2)+"\n");return data
def gui(root,manifest):
    data=json.loads(manifest.read_text());import tkinter as tk
    from tkinter import ttk,messagebox
    w=tk.Tk();w.title("Apps Panel — Python / Java / Web");w.geometry("1000x700")
    ttk.Label(w,text="Apps Panel",font=("Segoe UI",22,"bold")).pack(anchor="w",padx=18,pady=12)
    ttk.Label(w,text=str(data["python_source_count"])+" Python · "+str(data["java_source_count"])+" Java · "+str(data["web_source_count"])+" Web sources").pack(anchor="w",padx=18)
    frame=ttk.Frame(w);frame.pack(fill="both",expand=True,padx=18,pady=12);listing=tk.Listbox(frame,width=50);listing.pack(side="left",fill="y");output=tk.Text(frame,wrap="word");output.pack(side="left",fill="both",expand=True,padx=12)
    apps=[a for a in data["python"] if a["kind"]=="python-entrypoint"]
    for a in apps:listing.insert("end",a["name"]+" — "+a["source"])
    def launch():
        if not listing.curselection():return
        a=apps[listing.curselection()[0]];src=root/a["source"]
        if not src.is_file():messagebox.showerror("Missing source",str(src));return
        output.delete("1.0","end");output.insert("end","Launching "+a["name"]+"\n")
        p=subprocess.Popen([sys.executable,str(src)],cwd=str(src.parent),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);text,_=p.communicate();output.insert("end",(text or "No console output.")+"\nExit code: "+str(p.returncode))
    ttk.Button(w,text="Run selected app",command=launch).pack(anchor="w",padx=18,pady=12);w.mainloop()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1]);ap.add_argument("--output",type=pathlib.Path,default=pathlib.Path("build/polyglot"));ap.add_argument("--platform",choices=["linux","windows"],default="linux");ap.add_argument("--build",action="store_true");ap.add_argument("--gui",action="store_true");ap.add_argument("--manifest",type=pathlib.Path)
    a=ap.parse_args();root=a.root.resolve()
    if a.gui:gui(root,a.manifest or a.output/"polyglot-apps.json");return
    if a.build:data=build(root,a.output.resolve(),a.platform)
    else:
        py,java,web=inventory(root);data={"schema":"chimera-polyglot-apps/v1","platform_build":"inventory-only","python_source_count":len(py),"python_entrypoints":sum(x["kind"]=="python-entrypoint" for x in py),"java_source_count":len(java),"web_source_count":len(web),"python":py,"java_sources":java,"web_sources":web};a.output.mkdir(parents=True,exist_ok=True);(a.output/"polyglot-apps.json").write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:v for k,v in data.items() if k not in {"python","java_sources","web_sources"}},indent=2))
if __name__=="__main__":main()
