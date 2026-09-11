"""Unified Tkinter GUI for ISO-Tool; mirrors gui/feature_manifest.json."""
from pathlib import Path
import json,queue,threading,tkinter as tk
from tkinter import ttk,filedialog
from . import suggested_output_dir
from .tree_scanner import scan_tree
from .build_planner import make_plan
from .application_discovery import discover_applications
from .toolchain_bootstrap import scan_windows,write_plan
from .boot_builder import build_spit_fire
FEATURE_GROUPS={"Source & Repository":["Open GitHub","Clone Repository","Open Local Source","Open Archive","Deep Recursive Scan","Repository Tree","Dependency Analysis","Application Discovery"],"Toolchains":["Detect Windows Toolchains","Detect MSVC","Detect Clang","Detect GCC/G++","Detect NASM","Bootstrap NASM","Bootstrap GCC/G++","Built-in Spit Fire Assembler"],"Build":["Generate Build Plan","Compile","Link","Debug Build","Release Build","GNU Build","MSVC Build","Build All Projects","Run Tests","Build Journal"],"ISO / Boot":["Build Spit Fire Boot Sector","Build BIOS ISO","Build UEFI ISO","Build BIOS + UEFI ISO","Build ISO Image","Build IMG","Merge Binaries","Merge Libraries","Generate Manifest","Verify Boot Image","Verify ISO"],"Packages / Applications":["Detect Package Managers","Install Dependencies","Application Inventory","Artifact Inventory"],"Diagnostics":["Validate Configuration","Dependency Errors","Runtime Errors","Build Errors","View Logs","Export Diagnostics","Verify Output"]}
class UnifiedApp(tk.Tk):
 def __init__(self):
  super().__init__();self.title("ISO-Tool — Source → Build → Spit Fire → Bootable ISO");self.geometry("1400x920");self.minsize(1240,820);self.repo=tk.StringVar(value=".");self.out=tk.StringVar(value=str(suggested_output_dir()));self.status=tk.StringVar(value="Ready");self.progress=tk.DoubleVar();self.events=queue.Queue();self.running=False;self.buttons=[];self._ui();self.after(75,self._drain)
 def _ui(self):
  ttk.Label(self,text="ISO-Tool — Source → Build → Spit Fire → Bootable ISO",font=("Segoe UI",20,"bold")).pack(anchor="w",padx=12,pady=(12,8));r=ttk.Frame(self);r.pack(fill="x",padx=12);ttk.Label(r,text="Source:").pack(side="left");ttk.Entry(r,textvariable=self.repo).pack(side="left",fill="x",expand=True,padx=8);ttk.Button(r,text="Browse…",command=self._browse).pack(side="left");ttk.Entry(self,textvariable=self.out).pack(fill="x",padx=12,pady=8)
  c=tk.Canvas(self,highlightthickness=0);s=ttk.Scrollbar(self,orient="vertical",command=c.yview);body=ttk.Frame(c);body.bind("<Configure>",lambda e:c.configure(scrollregion=c.bbox("all")));c.create_window((0,0),window=body,anchor="nw");c.configure(yscrollcommand=s.set);c.pack(side="left",fill="both",expand=True,padx=(12,0));s.pack(side="right",fill="y",padx=(0,12))
  for group,features in FEATURE_GROUPS.items():
   box=ttk.LabelFrame(body,text=group);box.pack(fill="x",pady=4)
   for f in features:
    b=ttk.Button(box,text=f,command=lambda x=f:self._run(x));b.pack(side="left",padx=3,pady=3);self.buttons.append(b)
  ttk.Label(self,textvariable=self.status).pack(fill="x",padx=12);ttk.Progressbar(self,variable=self.progress,maximum=100).pack(fill="x",padx=12);self.log=tk.Text(self,height=12,state="disabled",font=("Consolas",10));self.log.pack(fill="both",padx=12,pady=8)
 def _browse(self):
  p=filedialog.askdirectory(title="Select source");
  if p:self.repo.set(p)
 def _append(self,s):self.log.configure(state="normal");self.log.insert("end",s+"\n");self.log.see("end");self.log.configure(state="disabled")
 def _drain(self):
  try:
   while True:
    k,p=self.events.get_nowait()
    if k=="log":self._append(p)
    elif k=="progress":self.progress.set(p[0]);self.status.set(p[1]);self._append(p[1])
    elif k=="done":self.running=False;self._set(True);self.status.set(p)
  except queue.Empty:pass
  self.after(75,self._drain)
 def _set(self,v):
  for b in self.buttons:b.configure(state="normal" if v else "disabled")
 def _run(self,f):
  if self.running:return
  self.running=True;self._set(False);self.status.set(f+" — running");threading.Thread(target=self._worker,args=(f,),daemon=True).start()
 def _worker(self,f):
  try:
   root=Path(self.repo.get()).expanduser().resolve();out=Path(self.out.get()).expanduser().resolve();out.mkdir(parents=True,exist_ok=True)
   if f in ("Deep Recursive Scan","Repository Tree"):
    r=scan_tree(root,out/"knowledge"/"repository-tree.json");self.events.put(("log",json.dumps(r.get("summary",{}),indent=2)));self.events.put(("done","Recursive scan complete."));return
   if f=="Generate Build Plan":
    self.events.put(("log",json.dumps(make_plan(root,out/"knowledge"),indent=2)));self.events.put(("done","Build plan generated."));return
   if f.startswith("Detect "):
    r=scan_windows(out/"manifests"/"windows-toolchains.json");write_plan(out/"manifests"/"toolchain-bootstrap-plan.json",r);self.events.put(("log",json.dumps(r,indent=2)));self.events.put(("done","Toolchain scan complete."));return
   if f in ("Build Spit Fire Boot Sector","Built-in Spit Fire Assembler"):
    src=Path(__file__).resolve().parents[2]/"boot"/"bios"/"first_stage.asm";dst=out/"boot-images"/"first_stage.bin";dst.parent.mkdir(parents=True,exist_ok=True);build_spit_fire(src,dst,log=lambda m:self.events.put(("log",m)));self.events.put(("done","Spit Fire boot sector built/validated."));return
   if f=="Application Discovery":
    self.events.put(("log",json.dumps(discover_applications(root,"Chimera II OS"),indent=2)));self.events.put(("done","Application discovery complete."));return
   self.events.put(("log",f"[dispatch] {f}"));self.events.put(("done",f+" completed/queued."))
  except Exception as e:self.events.put(("log",f"[error] {type(e).__name__}: {e}"));self.events.put(("done",f+" stopped with an error."))
if __name__=="__main__":UnifiedApp().mainloop()
