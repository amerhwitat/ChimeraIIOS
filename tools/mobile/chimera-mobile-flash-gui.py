#!/usr/bin/env python3
"""Chimera II OS Mobile Edition Flash Tool GUI with universal port detection."""
import json,queue,subprocess,threading,sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox,ttk
ROOT=Path(__file__).resolve().parents[2]
BUILDER=Path(__file__).with_name("chimera-mobile-build.py")
CLI=Path(__file__).with_name("chimera-mobile-flash.sh")
SCANNER=Path(__file__).with_name("chimera-device-port-scan.py")
PYTHON=sys.executable

class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title("Chimera II OS — Mobile Edition Flash Tool"); self.geometry("1300x850"); self.q=queue.Queue(); self._aurora_style(); self._ui(); self.after(100,self._drain); self.after(250,self._poll_progress); self.detect()
 def _aurora_style(self):
  style=ttk.Style(self)
  try: style.theme_use("clam")
  except tk.TclError: pass
  style.configure("Aurora.Horizontal.TProgressbar",thickness=18,troughcolor="#101a2b",background="#62e8ff",lightcolor="#a9f3ff",darkcolor="#2cb9df",bordercolor="#263b55")
 def _ui(self):
  r=ttk.Frame(self,padding=18); r.pack(fill="both",expand=True)
  ttk.Label(r,text="Chimera II OS Mobile Edition",font=("TkDefaultFont",22,"bold")).pack(anchor="w")
  ttk.Label(r,text="Universal host-port detection • Android ADB/Fastboot • Apple usbmux • MTP • serial • Thunderbolt/USB4").pack(anchor="w",pady=(3,8))
  self.progressbar=ttk.Progressbar(r,style="Aurora.Horizontal.TProgressbar",orient="horizontal",mode="determinate",maximum=100); self.progressbar.pack(fill="x",pady=(0,4))
  self.progress_text=tk.StringVar(value="0% — Ready"); ttk.Label(r,textvariable=self.progress_text).pack(anchor="w",pady=(0,8))
  b=ttk.Frame(r); b.pack(fill="x")
  for label,fn in [("Scan All Ports",self.port_scan),("Detect / Inspect",self.detect),("Wake / Power-On",self.wake),("Find ROMs + Security",self.discover_roms),("Compile ROM + ISO",self.build),("Validate artifacts",self.validate),("Flash ROM",self.flash)]: ttk.Button(b,text=label,command=fn).pack(side="left",padx=4)
  p=ttk.Panedwindow(r,orient="horizontal"); p.pack(fill="both",expand=True,pady=12)
  a=ttk.LabelFrame(p,text="Connected devices / hardware / software",padding=10); z=ttk.LabelFrame(p,text="Build / flash log",padding=10); p.add(a,weight=1); p.add(z,weight=2)
  self.info=tk.Text(a,state="disabled",wrap="word"); self.info.pack(fill="both",expand=True)
  self.log=tk.Text(z,state="disabled",wrap="word"); self.log.pack(fill="both",expand=True)
  self.status=tk.StringVar(value="Ready"); ttk.Label(r,textvariable=self.status).pack(anchor="w")
 def put(self,w,s):
  w.configure(state="normal"); w.insert("end",str(s)+"\n"); w.see("end"); w.configure(state="disabled")
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
   try:
    d=json.loads(p.read_text(encoding="utf-8")); pct=max(0,min(100,int(d.get("percent",0))))
    self.progressbar["value"]=pct; self.progress_text.set(f'{pct}% — {d.get("message_en","")} / {d.get("message_ar","")}')
   except Exception: pass
  self.after(250,self._poll_progress)
 def work(self,fn):
  self.q.put(("status","Working…"))
  def worker():
   try: fn()
   except Exception as e: self.q.put(("log","ERROR: "+str(e)))
   finally: self.q.put(("status","Ready"))
  threading.Thread(target=worker,daemon=True).start()
 def port_scan(self):
  def run():
   p=subprocess.run([PYTHON,str(SCANNER),"--json"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("info","UNIVERSAL HOST-PORT INVENTORY\n"+p.stdout)); self.q.put(("log","All-port scan completed.\n"+p.stdout))
  self.work(run)
 def detect(self):
  def run():
   p=subprocess.run([PYTHON,str(BUILDER),"--detect"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("info","DEVICE + SOFTWARE DETECTION\n"+p.stdout)); self.q.put(("log",p.stdout))
  self.work(run)
 def wake(self):
  def run():
   p=subprocess.run([PYTHON,str(BUILDER),"--detect","--power-on"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("info",p.stdout)); self.q.put(("log",p.stdout))
  self.work(run)
 def discover_roms(self):
  def run():
   p=subprocess.run([PYTHON,str(BUILDER),"--discover-roms"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("log",p.stdout)); self.q.put(("info","ROM / PUBLIC SECURITY METADATA DISCOVERY\n"+p.stdout))
  self.work(run)
 def build(self):
  def run():
   p=subprocess.run([PYTHON,str(BUILDER),"--build"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("log",p.stdout)); self.q.put(("info",p.stdout))
  self.work(run)
 def validate(self):
  p=ROOT/"build/mobile/last-build.json"
  if not p.exists(): messagebox.showerror("Validation","Build and profile the exact device first."); return
  r=json.loads(p.read_text(encoding="utf-8"))
  self.put(self.info,json.dumps({"ROM":r["rom"],"ROM_SHA256":r["rom_sha256"],"ISO":r["iso"],"ISO_SHA256":r["iso_sha256"],"profile":r["profile"]["id"],"target":r["target"]},indent=2,ensure_ascii=False))
 def flash(self):
  if not (ROOT/"build/mobile/last-build.json").exists(): messagebox.showerror("Flash","Build and validate the exact device-specific ROM first."); return
  if not messagebox.askyesno("Confirm flash","The tool will re-check the live serial, exact device profile, partition map and SHA-256 hashes before writing. Continue?"): return
  def run():
   p=subprocess.run(["bash",str(CLI),"flash"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,input="FLASH CHIMERA\n")
   self.q.put(("log",p.stdout))
  self.work(run)
if __name__=="__main__": App().mainloop()
