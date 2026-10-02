#!/usr/bin/env python3
"""Chimera II OS Mobile Edition Flash Tool GUI."""
import json,queue,subprocess,threading,sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox,ttk
ROOT=Path(__file__).resolve().parents[2]; BUILDER=Path(__file__).with_name("chimera-mobile-build.py"); CLI=Path(__file__).with_name("chimera-mobile-flash.sh"); PYTHON=sys.executable
class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title("Chimera II OS — Mobile Edition Flash Tool"); self.geometry("1200x780"); self.q=queue.Queue(); self._ui(); self.after(100,self._drain); self.detect()
 def _ui(self):
  r=ttk.Frame(self,padding=18); r.pack(fill="both",expand=True); ttk.Label(r,text="Chimera II OS Mobile Edition",font=("TkDefaultFont",22,"bold")).pack(anchor="w"); ttk.Label(r,text="Wake → detect hardware/software/ROM → exact profile → compile → verify → flash").pack(anchor="w",pady=(3,12))
  b=ttk.Frame(r); b.pack(fill="x")
  for label,fn in [("Scan USB",self.usb_scan),("Wake / Power-On",self.wake),("Detect / Inspect",self.detect),("Compile ROM + ISO",self.build),("Validate artifacts",self.validate),("Flash ROM",self.flash)]: ttk.Button(b,text=label,command=fn).pack(side="left",padx=4)
  p=ttk.Panedwindow(r,orient="horizontal"); p.pack(fill="both",expand=True,pady=12); a=ttk.LabelFrame(p,text="Phone / profile",padding=10); z=ttk.LabelFrame(p,text="Build / flash log",padding=10); p.add(a,weight=1); p.add(z,weight=2)
  self.info=tk.Text(a,state="disabled",wrap="word"); self.info.pack(fill="both",expand=True); self.log=tk.Text(z,state="disabled",wrap="word"); self.log.pack(fill="both",expand=True); self.status=tk.StringVar(value="Ready"); ttk.Label(r,textvariable=self.status).pack(anchor="w")
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
 def work(self,fn):
  self.q.put(("status","Working…"))
  def worker():
   try: fn()
   except Exception as e: self.q.put(("log","ERROR: "+str(e)))
   finally: self.q.put(("status","Ready"))
  threading.Thread(target=worker,daemon=True).start()
 def usb_scan(self):
  def run():
   p=subprocess.run([PYTHON,str(BUILDER),"--usb-scan"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("info",p.stdout)); self.q.put(("log","USB scan completed.\n"+p.stdout))
  self.work(run)
 def wake(self):
  def run():
   p=subprocess.run([PYTHON,str(BUILDER),"--detect","--power-on"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("info",p.stdout)); self.q.put(("log",p.stdout))
  self.work(run)
 def detect(self):
  def run():
   scan=subprocess.run([PYTHON,str(BUILDER),"--usb-scan"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("info","USB CONNECTION SCAN\\n"+scan.stdout))
   detect=subprocess.run([PYTHON,str(BUILDER),"--detect"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   self.q.put(("info","PHONE DETECTION\\n"+detect.stdout))
   self.q.put(("log","Phone detection completed." if detect.returncode==0 else "Detection diagnostics:\\n"+detect.stdout))
  self.work(run)
 def build(self):
  def run():
   p=subprocess.run([PYTHON,str(BUILDER),"--build"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); self.q.put(("log",p.stdout)); self.q.put(("info",p.stdout))
  self.work(run)
 def validate(self):
  p=ROOT/"build/mobile/last-build.json"
  if not p.exists(): messagebox.showerror("Validation","Build ROM + ISO first."); return
  r=json.loads(p.read_text(encoding="utf-8")); self.put(self.info,json.dumps({"ROM":r["rom"],"ROM_SHA256":r["rom_sha256"],"ISO":r["iso"],"ISO_SHA256":r["iso_sha256"],"profile":r["profile"]["id"]},indent=2))
 def flash(self):
  if not (ROOT/"build/mobile/last-build.json").exists(): messagebox.showerror("Flash","Build and validate the device-specific ROM first."); return
  if not messagebox.askyesno("Confirm flash","This operation uses only partitions declared by the matched profile. Continue?"): return
  def run():
   p=subprocess.run(["bash",str(CLI),"flash"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,input="FLASH CHIMERA\n"); self.q.put(("log",p.stdout))
  self.work(run)
if __name__=="__main__": App().mainloop()
