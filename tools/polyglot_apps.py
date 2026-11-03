#!/usr/bin/env python3
"""Inventory, GUI launcher and PyInstaller packager for first-party Python/Java/Web apps."""
from __future__ import annotations
import argparse,json,os,pathlib,re,shutil,subprocess,sys,webbrowser
SKIP={".git",".venv","venv","__pycache__","node_modules","tests","test",".build","build","dist","out",".pytest_cache",".chimera-fix-backups","target",".gradle",".idea"}
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
    py,java,web=inventory(root)
    out.mkdir(parents=True,exist_ok=True)
    dist=out/"dist";dist.mkdir(exist_ok=True)
    tool=shutil.which("pyinstaller")
    source_tree=out/"python-source";source_tree.mkdir(exist_ok=True)
    # Stage all first-party Python modules as importable source; compile every
    # module for syntax/bytecode validation, but only entrypoints become apps.
    for source in root.rglob("*.py"):
        rel=source.relative_to(root)
        if not excluded(rel):
            target=source_tree/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
            py_compile_target=out/"py_compile"/rel
            py_compile_target.parent.mkdir(parents=True,exist_ok=True)
            try:
                import py_compile
                py_compile.compile(str(source),cfile=str(py_compile_target)+"c",doraise=True)
            except Exception as exc:
                raise RuntimeError(f"Python compilation failed: {rel}: {exc}") from exc
    for app in py:
        if app["kind"]!="python-entrypoint":
            app["build"]="compiled-module: bytecode validated; library is not a standalone app"
            continue
        app["build"]="failed: PyInstaller unavailable"
        if not tool:continue
        wrapper=out/(app["id"]+".py")
        wrapper.write_text(make_wrapper(app["source"],app["name"]))
        name=app["id"][3:]
        sep=";" if platform=="windows" else ":"
        r=call([tool,"--noconfirm","--clean","--onefile","--windowed","--name",name,
                "--distpath",str(dist),"--add-data",str(source_tree)+sep+"python-source",
                str(wrapper)],root)
        app["build"]="built" if r.returncode==0 else "failed"
        app["log"]=r.stdout[-3000:]
        app["artifact"]=str((dist/(name+(".exe" if platform=="windows" else ""))).relative_to(out)) if r.returncode==0 else None
    # Build every Maven project, not just the first pom.xml. Also compile
    # standalone Java source trees that are not owned by a Maven project.
    poms=sorted(p for p in root.rglob("pom.xml")
                if not any(part in SKIP for part in p.relative_to(root).parts))
    maven_roots={p.parent.resolve() for p in poms}
    java_results=[]
    if java and not shutil.which("javac"):
        java_results.append({"status":"failed","reason":"JDK javac unavailable"})
    else:
        for index,pom in enumerate(poms):
            if not shutil.which("mvn"):
                java_results.append({"project":pom.relative_to(root).as_posix(),"status":"failed","reason":"Maven unavailable"})
                continue
            r=call(["mvn","-B","-f",str(pom),"package","-DskipTests"],root)
            java_results.append({"project":pom.relative_to(root).as_posix(),"status":"built" if r.returncode==0 else "failed","log":r.stdout[-3000:]})
            if r.returncode==0:
                target=pom.parent/"target"
                for jar in sorted(target.glob("*.jar")):
                    if jar.is_file():
                        shutil.copy2(jar,dist/(f"java-{index}-{jar.name}"))
        standalone=[root/s for s in java if not any((root/s).is_relative_to(m) for m in maven_roots)]
        if standalone and shutil.which("javac"):
            classes=out/"java-classes";classes.mkdir(exist_ok=True)
            r=call(["javac","-encoding","UTF-8","-d",str(classes),*[str(p) for p in standalone]],root)
            java_results.append({"project":"standalone-java-sources","status":"built" if r.returncode==0 else "failed","source_count":len(standalone),"log":r.stdout[-3000:]})
    java_status=("no Java sources" if not java else
                 "built" if java_results and all(x["status"]=="built" for x in java_results) else
                 "failed")
    # Validate first-party JavaScript syntax and parse HTML documents. JSX/TS
    # are explicitly inventoried until a project compiler is configured.
    web_results={"javascript_checked":0,"html_parsed":0,"css_checked":0,"uncompiled_extensions":[]}
    node=shutil.which("node")
    for rel in web:
        path=root/rel
        suffix=path.suffix.lower()
        if suffix==".js":
            if not node:
                raise RuntimeError("Node.js is required to validate JavaScript sources")
            r=call([node,"--check",str(path)],root)
            if r.returncode:raise RuntimeError(f"JavaScript syntax failed: {rel}\n{r.stdout[-2000:]}")
            web_results["javascript_checked"]+=1
        elif suffix in {".html",".htm"}:
            from html.parser import HTMLParser
            class Validator(HTMLParser):
                pass
            try:
                Validator(convert_charrefs=True).feed(path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise RuntimeError(f"HTML parse failed: {rel}: {exc}") from exc
            web_results["html_parsed"]+=1
        elif suffix==".css":
            css=path.read_text(encoding="utf-8",errors="replace")
            if css.count("{")!=css.count("}"):
                raise RuntimeError(f"CSS brace mismatch: {rel}")
            web_results["css_checked"]+=1
        else:
            web_results["uncompiled_extensions"].append(suffix)
    data={"schema":"chimera-polyglot-apps/v2","platform_build":platform,
          "python_source_count":len(py),
          "python_entrypoints":sum(a["kind"]=="python-entrypoint" for a in py),
          "python_modules_compiled":sum(a["kind"]=="python-module" for a in py),
          "java_source_count":len(java),"java_projects":java_results,
          "java_build":java_status,"web_source_count":len(web),
          "web_validation":web_results,"python":py,"java_sources":java,"web_sources":web,
          "compatibility":{"windows":"Build PyInstaller .exe on Windows; Windows binaries are not Linux executables.",
          "wine":"Optional Wine runtime may launch compatible Windows .exe files; not guaranteed for every app.",
          "linux":"Build separate Linux-native PyInstaller artifacts.",
          "web":"HTML/CSS/JS are web assets; validation does not convert them into native executables."}}
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
    r=call([tool,"--noconfirm","--clean","--onefile","--windowed","--name","PolyglotAppsPanel",
            "--distpath",str(dist),"--add-data",str(source_tree)+sep+"python-source",
            "--add-data",str(out/"polyglot-apps.json")+sep+".",str(panel)],root) if tool else None
    data["panel_build"]=("built" if r and r.returncode==0 else "failed: PyInstaller unavailable" if not tool else "failed")
    data["panel_artifact"]=str((dist/("PolyglotAppsPanel"+(".exe" if platform=="windows" else ""))).relative_to(out)) if r and r.returncode==0 else None
    if r and r.returncode!=0:data["panel_build_log"]=r.stdout[-3000:]
    (out/"polyglot-apps.json").write_text(json.dumps(data,indent=2)+"\n")
    return data
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
        if a["kind"]=="python-entrypoint":
            artifact=a.get("artifact")
            if artifact:
                exe_name=pathlib.Path(artifact).name
                candidate=(pathlib.Path(sys.executable).resolve().parent/exe_name if sys.platform=="win32" else pathlib.Path(os.environ.get("CHIMERA_LINUX_APPS_DIR",str(manifest.parent/"linux")))/exe_name)
                if candidate.is_file():subprocess.Popen([str(candidate)]);return
            interpreter=shutil.which("python3") or shutil.which("python")
            if not interpreter:messagebox.showerror("Python unavailable","No native Python runtime or built executable is available for this entrypoint.");return
            subprocess.Popen([interpreter,str(src)],cwd=str(src.parent));return
        output.delete("1.0","end");output.insert("end","Source is present; no standalone launcher is defined for this item.")
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
        if failed or data.get("panel_build")!="built" or data.get("java_build")=="failed":
            print("ERROR: one or more application build gates failed",file=sys.stderr)
            raise SystemExit(1)
if __name__=="__main__":main()
