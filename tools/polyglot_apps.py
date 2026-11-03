#!/usr/bin/env python3
"""Inventory, GUI launcher and PyInstaller packager for first-party Python/Java/Web apps."""
from __future__ import annotations
import argparse,json,os,pathlib,re,shutil,subprocess,sys,webbrowser
SKIP={".git",".venv","venv","__pycache__","node_modules","tests","test",".build","build","dist","out",".pytest_cache",".chimera-fix-backups"}
def excluded(rel):
    parts=rel.parts
    if any(part in SKIP for part in parts):return True
    if "vendor" in parts:
        return not (parts[:3]==("vendor","chimera-ii-os","source") and "vendor" not in parts[3:])
    return False
WEB={".html",".htm",".js",".jsx",".ts",".tsx",".css"}
def inventory(root):
    py=[];java=[];web=[]
    for p in sorted(root.rglob("*")):
        if not p.is_file():continue
        rel=p.relative_to(root)
        if excluded(rel):continue
        if p.suffix==".py":
            src=p.read_text(encoding="utf-8",errors="replace")
            entry=p.name in {"main.py","__main__.py"} or p.name.startswith("launch") or bool(re.search(r"""if\s+__name__\s*==\s*["']__main__["']""",src))
            py.append({"id":"py-"+re.sub(r"[^a-z0-9]+","-",rel.as_posix().lower()).strip("-"),"name":p.stem.replace("_"," ").title(),"kind":"python-entrypoint" if entry else "python-module","source":rel.as_posix(),"platforms":["Linux","Windows"],"gui":"Tkinter GUI wrapper" if entry else "Library/module; no standalone GUI","build":"inventory-only"})
        elif p.suffix==".java":java.append(rel.as_posix())
        elif p.suffix.lower() in WEB:web.append(rel.as_posix())
    return py,java,web
def call(cmd,cwd):return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
def make_wrapper(source,name):
    return """import pathlib,subprocess,sys,tkinter as tk,runpy,contextlib,io
from tkinter import ttk,messagebox
ROOT=pathlib.Path(__file__).resolve().parent
BUNDLE=pathlib.Path(getattr(sys,"_MEIPASS",ROOT))
SOURCE=BUNDLE/"python-source"/"""+repr(source)+"""
def main():
 w=tk.Tk();w.title("""+repr(name)+"""+" — App");w.geometry("900x620")
 ttk.Label(w,text="""+repr(name)+""",font=("Segoe UI",16,"bold")).pack(anchor="w",padx=16,pady=12)
 out=tk.Text(w,wrap="word");out.pack(fill="both",expand=True,padx=16,pady=8)
 def launch():
  if not SOURCE.is_file():messagebox.showerror("Missing source",str(SOURCE));return
  sys.path.insert(0,str(BUNDLE/"python-source"));sys.path.insert(0,str(SOURCE.parent));buf=io.StringIO()
  try:
   with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):runpy.run_path(str(SOURCE),run_name="__main__")
   code=0
  except SystemExit as exc:code=exc.code if isinstance(exc.code,int) else 1
  except Exception as exc:buf.write(str(exc));code=1
  out.insert("end",(buf.getvalue() or "No console output.")+"\\nExit code: "+str(code)+"\\n")
 bar=ttk.Frame(w);bar.pack(fill="x",padx=16,pady=12)
 ttk.Button(bar,text="Run",command=launch).pack(side="left")
 ttk.Button(bar,text="Close",command=w.destroy).pack(side="right")
 w.mainloop()
if __name__=="__main__":main()
"""
def build(root,out,platform):
    py,java,web=inventory(root);out.mkdir(parents=True,exist_ok=True);dist=out/"dist";dist.mkdir(exist_ok=True);tool=shutil.which("pyinstaller");source_tree=out/"python-source";source_tree.mkdir(exist_ok=True)
    for source in root.rglob("*.py"):
        rel=source.relative_to(root)
        if not excluded(rel):
            target=source_tree/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    for app in py:
        if app["kind"]!="python-entrypoint":continue
        app["build"]="source-only: PyInstaller unavailable"
        if not tool:continue
        wrapper=out/(app["id"]+".py");wrapper.write_text(make_wrapper(app["source"],app["name"]));name=app["id"][3:]
        sep=";" if platform=="windows" else ":"
        r=call([tool,"--noconfirm","--clean","--onefile","--windowed","--name",name,"--distpath",str(dist),"--add-data",str(source_tree)+sep+"python-source",str(wrapper)],root)
        app["build"]="built" if r.returncode==0 else "failed";app["log"]=r.stdout[-2000:]
        app["artifact"]=str((dist/(name+(".exe" if platform=="windows" else ""))).relative_to(out)) if r.returncode==0 else None
    poms=[p for p in root.rglob("pom.xml") if not any(part in SKIP for part in p.relative_to(root).parts)];pom=poms[0] if poms else None;java_status="sources inventoried; no Maven project" if java else "no Java sources"
    if pom and shutil.which("mvn"):
        r=call(["mvn","-B","-f",str(pom),"package","-DskipTests"],root);java_status=("selected Maven project built; other Java sources catalogued" if r.returncode==0 else "Maven project build failed")
    elif java and not shutil.which("javac"):java_status="sources inventoried; JDK unavailable"
    data={"schema":"chimera-polyglot-apps/v1","platform_build":platform,"python_source_count":len(py),"python_entrypoints":sum(a["kind"]=="python-entrypoint" for a in py),"java_source_count":len(java),"web_source_count":len(web),"java_build":java_status,"python":py,"java_sources":java,"web_sources":web,"compatibility":{"windows":"Build PyInstaller .exe on Windows; Windows binaries are not Linux executables.","wine":"Optional Wine runtime may launch compatible Windows .exe files; not guaranteed for every app.","linux":"Build separate Linux-native PyInstaller artifacts."}}
    (out/"polyglot-apps.json").write_text(json.dumps(data,indent=2)+"\n")
    panel=out/"polyglot-panel.py"
    panel.write_text("""import os,pathlib,runpy,sys
if sys.platform.startswith("linux"):
 os.environ.setdefault("CHIMERA_WINDOWS_APPS_DIR","/opt/aurora/apps/polyglot/windows")
 os.environ.setdefault("CHIMERA_LINUX_APPS_DIR","/opt/aurora/apps/polyglot/linux")
base=pathlib.Path(getattr(sys,"_MEIPASS",pathlib.Path(__file__).resolve().parent))
sys.argv=["polyglot_apps.py","--gui","--root",str(base/"python-source"),"--manifest",str(base/"polyglot-apps.json")]
runpy.run_path(str(base/"python-source"/"tools"/"polyglot_apps.py"),run_name="__main__")
""")
    sep=";" if platform=="windows" else ":"
    r=call([tool,"--noconfirm","--clean","--onefile","--windowed","--name","PolyglotAppsPanel","--distpath",str(dist),"--add-data",str(source_tree)+sep+"python-source","--add-data",str(out/"polyglot-apps.json")+sep+".",str(panel)],root) if tool else None
    data["panel_build"]=("built" if r and r.returncode==0 else "source-only: PyInstaller unavailable" if not tool else "failed")
    data["panel_artifact"]=str((dist/("PolyglotAppsPanel"+(".exe" if platform=="windows" else ""))).relative_to(out)) if r and r.returncode==0 else None
    if r and r.returncode!=0:data["panel_build_log"]=r.stdout[-2000:]
    (out/"polyglot-apps.json").write_text(json.dumps(data,indent=2)+"\n");return data
def gui(root,manifest):
    data=json.loads(manifest.read_text());import tkinter as tk
    from tkinter import ttk,messagebox
    w=tk.Tk();w.title("Apps Panel — Python / Java / Web");w.geometry("1000x700")
    ttk.Label(w,text="Apps Panel",font=("Segoe UI",22,"bold")).pack(anchor="w",padx=18,pady=12)
    ttk.Label(w,text=str(data["python_source_count"])+" Python · "+str(data["java_source_count"])+" Java · "+str(data["web_source_count"])+" Web sources").pack(anchor="w",padx=18)
    frame=ttk.Frame(w);frame.pack(fill="both",expand=True,padx=18,pady=12);listing=tk.Listbox(frame,width=50);listing.pack(side="left",fill="y");output=tk.Text(frame,wrap="word");output.pack(side="left",fill="both",expand=True,padx=12)
    apps=list(data["python"])
    for a in apps:listing.insert("end",a["name"]+" — "+a["kind"]+" · "+a["source"])
    for source in data.get("java_sources",[]):
        item={"kind":"java-source","name":pathlib.Path(source).name,"source":source};apps.append(item);listing.insert("end",item["name"]+" — Java source")
    for source in data.get("web_sources",[]):
        item={"kind":"web-source","name":pathlib.Path(source).name,"source":source};apps.append(item);listing.insert("end",item["name"]+" — Web source")
    windows_dir=(pathlib.Path(sys.executable).resolve().parent if sys.platform=="win32" else pathlib.Path(os.environ.get("CHIMERA_WINDOWS_APPS_DIR",str(manifest.parent/"windows"))))
    windows_apps=sorted(x for x in windows_dir.glob("*.exe") if x.resolve()!=pathlib.Path(sys.executable).resolve()) if windows_dir.is_dir() else []
    for exe in windows_apps:listing.insert("end",exe.stem+" — Windows executable (Wine)")
    apps.extend([{"kind":"windows-exe","name":exe.stem,"source":str(exe)} for exe in windows_apps])
    def launch():
        if not listing.curselection():return
        a=apps[listing.curselection()[0]]
        if a["kind"]=="windows-exe":
            wine=shutil.which("wine") or shutil.which("wine64")
            if not wine:messagebox.showerror("Wine unavailable","Install the optional Wine 32/64-bit compatibility runtime to launch Windows executables.");return
            subprocess.Popen([wine,a["source"]]);return
        if a["kind"]=="python-module":messagebox.showinfo("Python module","This file is a library/module, not a standalone application entrypoint.");return
        if a["kind"]=="java-source":messagebox.showinfo("Java source","Source is included; only configured Java projects are compiled into runnable artifacts.");return
        src=root/a["source"]
        if a["kind"]=="web-source":
            if src.suffix.lower() in {".html",".htm"}:webbrowser.open(src.resolve().as_uri())
            else:messagebox.showinfo("Web asset","This JavaScript/CSS asset is loaded by its parent web application.")
            return
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
    if a.build:
        failed=[x["source"] for x in data["python"] if x["kind"]=="python-entrypoint" and x.get("build")!="built"]
        if failed or data.get("panel_build")!="built" or (data["java_source_count"] and data.get("java_build")=="Maven project build failed"):
            print("ERROR: one or more application build gates failed",file=sys.stderr)
            raise SystemExit(1)
if __name__=="__main__":main()
