#!/usr/bin/env python3
import json, os, subprocess, tkinter as tk
from tkinter import messagebox, ttk
ROOT=os.environ.get("CHIMERA_ROOT","/usr/share/chimera")
REG=os.path.join(ROOT,"applications/crypto/crypto_ecosystem_registry.json")
class CryptoCenter(tk.Tk):
 def __init__(self):
  super().__init__(); self.title("Aurora Crypto Center"); self.geometry("1000x620")
  ttk.Label(self,text="Aurora Crypto Center — Open-Source Mainnet Wallets & Nodes",font=("TkDefaultFont",15,"bold")).pack(pady=10)
  ttk.Label(self,text="Software integration only; verify releases/signatures and protect wallet secrets.").pack()
  self.tree=ttk.Treeview(self,columns=("symbol","name","node","launcher","upstream"),show="headings")
  for c,w in [("symbol",80),("name",190),("node",180),("launcher",170),("upstream",360)]: self.tree.heading(c,text=c.upper()); self.tree.column(c,width=w)
  self.tree.pack(fill="both",expand=True,padx=15,pady=10)
  ttk.Button(self,text="Open Project",command=self.open).pack(pady=8)
  try:
   for x in json.load(open(REG))["mainnet_networks"]:
    node=x.get("node") or ", ".join(x.get("execution_clients",[]))
    up=x.get("upstream"); up=up[0] if isinstance(up,list) else up
    self.tree.insert("","end",values=(x.get("symbol",""),x["id"],node,x.get("launcher",""),up))
  except Exception as e: messagebox.showerror("Crypto registry",str(e))
 def open(self):
  s=self.tree.selection()
  if not s:return
  url=self.tree.item(s[0],"values")[4]
  if url: subprocess.Popen(["xdg-open",url])
if __name__=="__main__": CryptoCenter().mainloop()
