#!/usr/bin/env python3
"""Chimera II OS Mobile Edition Flash Tool GUI."""
import json,queue,subprocess,threading,sys,os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox,ttk
ROOT=Path(__file__).resolve().parents[2]; BUILDER=Path(__file__).with_name("chimera-mobile-build.py"); CLI=Path(__file__).with_name("chimera-mobile-flash.sh"); SCANNER=Path(__file__).with_name("chimera-device-port-scan.py"); PYTHON=sys.executable
class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title("Chimera II OS — Mobile Edition Flash Tool"); self.geometry("1400x900"); self.q=queue.Queue(); self._ui(); self.after(100,self._drain); self.after(250,self._poll_progress); self.detect()
 def _ui(self):
  r=ttk.Frame(self,padding=18); r.pack(fill="both",expand=True)
  ttk.Label(r,text="Chimera II OS Mobile Edition",font=("TkDefaultFont",22,"bold")).pack(anchor="w")
  ttk.Label(r,text="Universal USB/port detection • Android ADB/Fastboot • Apple usbmux • MTP • serial • Thunderbolt/USB4").pack(anchor="w",pady=(3,8))
  self.progressbar=ttk.Progressbar(r,orient="horizontal",mode="determinate",maximum=100); self.progressbar.pack(fill="x"); self.progress_text=tk.StringVar(value="0% — Ready"); ttk.Label(r,textvariable=self.progress_text).pack(anchor="w",pady=4)
  b=ttk.Frame(r); b.pack(fill="x")
  buttons=[("Scan All Ports",self.port_scan),("Detect / Inspect",self.detect),("Wake / Power-On",self.wake),("Find ROMs + Security",self.discover_roms),("Compile ROM + ISO",self.build),("Validate",self.validate),("Flash ROM",self.flash),("Generic Flash Disabled",self.generic_flash)]
  for label,fn in buttons: ttk.Button(b,text=label,command=fn).pack(side="left",padx=3)
  p=ttk.Panedwindow(r,orient="horizontal"); p.pack(fill="both",expand=True,pady=12); a=ttk.LabelFrame(p,text="Devices / hardware / software",padding=10); z=ttk.LabelFrame(p,text="Build / flash log",padding=10); p.add(a,weight=1); p.add(z,weight=2)
  self.info=tk.Text(a,state="disabled",wrap="word"); self.info.pack(fill="both",expand=True); self.log=tk.Text(z,state="disabled",wrap="word"); self.log.pack(fill="both",expand=True); self.status=tk.StringVar(value="Ready"); ttk.Label(r,textvariable=self.status).pack(anchor="w")
 def put(self,w,s): w.configure(state="normal"); w.insert("end",str(s)+"\n"); w.see("end"); w.configure(state="disabled")
 def _drain(self):
  try:
   while True:
    k,s=self.q.get_nowait()
    if k=="status": self.status.set(s)
    else: self.put(self.info if k=="info" else self.log,s)
  except queue.Empty: pass
  self.after(100,self._drain)
 def _poll_progress(self):
  p=ROOT/"build/mobile/aurora-progress/state.json"
  if p.is_file():
   try: d=json.loads(p.read_text()); self.progressbar["value"]=max(0,min(100,int(d.get("percent",0)))); self.progress_text.set(f'{self.progressbar["value"]}% — {d.get("message_en","")} / {d.get("message_ar","")}')
   except Exception: pass
  self.after(250,self._poll_progress)
 def work(self,fn):
  self.q.put(("status","Working…"))
  def w():
   try: fn()
   except Exception as e: self.q.put(("log","ERROR: "+str(e)))
   finally: self.q.put(("status","Ready"))
  threading.Thread(target=w,daemon=True).start()
 def cmd(self,args,title=""):
  p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); self.q.put(("info",(title+"\n" if title else "")+p.stdout)); self.q.put(("log",p.stdout))
 def port_scan(self): self.work(lambda:self.cmd([PYTHON,str(SCANNER),"--json"],"UNIVERSAL HOST-PORT INVENTORY"))
 def detect(self): self.work(lambda:self.cmd([PYTHON,str(BUILDER),"--detect"],"DEVICE + SOFTWARE DETECTION"))
 def wake(self): self.work(lambda:self.cmd([PYTHON,str(BUILDER),"--detect","--power-on"]))
 def discover_roms(self): self.work(lambda:self.cmd([PYTHON,str(BUILDER),"--discover-roms"],"ROM / PUBLIC SECURITY METADATA"))
 def build(self): self.work(lambda:self.cmd([PYTHON,str(BUILDER),"--build"]))
 def validate(self):
  p=ROOT/"build/mobile/last-build.json"
  if not p.exists(): messagebox.showerror("Validation","Build first."); return
  r=json.loads(p.read_text()); self.put(self.info,json.dumps({"ROM":r["rom"],"ROM_SHA256":r["rom_sha256"],"ISO":r["iso"],"ISO_SHA256":r["iso_sha256"],"profile":r["profile"]["id"],"target":r["target"]},indent=2,ensure_ascii=False))
 def flash(self):
  if not (ROOT/"build/mobile/last-build.json").exists(): messagebox.showerror("Flash","Build the exact-device ROM first."); return
  if not messagebox.askyesno("Confirm flash","Exact profile, live serial, partitions and SHA-256 will be rechecked before writing. Continue?"): return
  self.work(lambda:self.cmd(["bash",str(CLI),"flash"]))
 def generic_flash(self):
  messagebox.showwarning("Generic flash disabled","Unprofiled partition writes are disabled. Use a hardware-validated exact-device profile with signed images and an approved vendor adapter.")
if __name__=="__main__": App().mainloop()
