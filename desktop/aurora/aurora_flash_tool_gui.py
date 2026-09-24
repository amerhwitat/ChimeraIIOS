#!/usr/bin/env python3
import hashlib, json, os, subprocess, tkinter as tk
from tkinter import filedialog, messagebox, ttk
class FlashApp(tk.Tk):
 def __init__(self):
  super().__init__(); self.title("Aurora Flash Tool — Chimera II OS"); self.geometry("780x540")
  ttk.Label(self,text="Chimera II OS • Aurora Flash Tool",font=("TkDefaultFont",16,"bold")).pack(pady=12)
  f=ttk.Frame(self); f.pack(fill="x",padx=20); f.columnconfigure(1,weight=1)
  ttk.Label(f,text="Image:").grid(row=0,column=0,sticky="w"); self.img=ttk.Entry(f); self.img.grid(row=0,column=1,sticky="ew",padx=8); ttk.Button(f,text="Browse…",command=self.choose).grid(row=0,column=2)
  ttk.Label(f,text="Expected SHA-256 (optional):").grid(row=1,column=0,sticky="w",pady=8); self.sha=ttk.Entry(f); self.sha.grid(row=1,column=1,columnspan=2,sticky="ew")
  ttk.Button(self,text="Refresh removable devices",command=self.refresh).pack(pady=4)
  self.devices=ttk.Treeview(self,columns=("path","size","model","transport"),show="headings")
  for c,w in [("path",170),("size",100),("model",260),("transport",100)]: self.devices.heading(c,text=c.upper()); self.devices.column(c,width=w)
  self.devices.pack(fill="both",expand=True,padx=20,pady=8)
  self.status=tk.StringVar(value="Only removable whole-disk targets are displayed."); ttk.Label(self,textvariable=self.status).pack()
  ttk.Button(self,text="FLASH VERIFIED IMAGE",command=self.flash).pack(pady=12); self.refresh()
 def choose(self):
  p=filedialog.askopenfilename(filetypes=[("Chimera images","*.iso *.img"),("All files","*.*")])
  if p: self.img.delete(0,"end"); self.img.insert(0,p)
 def refresh(self):
  for i in self.devices.get_children(): self.devices.delete(i)
  try:
   d=json.loads(subprocess.check_output(["lsblk","-J","-o","NAME,PATH,TYPE,SIZE,RM,MODEL,TRAN"],text=True))
   for x in d.get("blockdevices",[]):
    if x.get("type")=="disk" and str(x.get("rm"))=="1": self.devices.insert("","end",values=(x.get("path"),x.get("size"),x.get("model") or "",x.get("tran") or ""))
  except Exception as e: self.status.set("Device enumeration failed: "+str(e))
 def flash(self):
  image=self.img.get().strip(); sel=self.devices.selection()
  if not image or not sel: return messagebox.showerror("Aurora Flash Tool","Choose an image and removable target.")
  target=self.devices.item(sel[0],"values")[0]
  if not messagebox.askyesno("FINAL DATA-LOSS CONFIRMATION",f"Everything on {target} will be erased.\n\nImage: {image}\nTarget: {target}\n\nContinue?"): return
  cmd=["python3",os.path.join(os.path.dirname(__file__),"aurora_flash_tool.py"),"--image",image,"--device",target]
  if self.sha.get().strip(): cmd += ["--sha256",self.sha.get().strip()]
  env=dict(os.environ); env["CHIMERA_FLASH_CONFIRM"]="YES"
  try: subprocess.run(["pkexec"]+cmd,env=env,check=True); messagebox.showinfo("Complete","Flash completed. Verify/eject the device before rebooting."); self.refresh()
  except Exception as e: messagebox.showerror("Flash failed",str(e))
if __name__=="__main__": FlashApp().mainloop()
