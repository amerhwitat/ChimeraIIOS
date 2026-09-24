#!/usr/bin/env python3
import json, os, subprocess, tkinter as tk
from tkinter import messagebox, ttk
ROOT=os.environ.get("CHIMERA_ROOT","/usr/share/chimera")
p=os.path.join(ROOT,"applications","ecosystem","repos.json")
class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title("Aurora Repository Application Center"); self.geometry("800x520")
  ttk.Label(self,text="Aurora • Chimera II OS Repository Applications",font=("TkDefaultFont",15,"bold")).pack(pady=10)
  self.tree=ttk.Treeview(self,columns=("name","integration","url"),show="headings")
  for c,w in [("name",180),("integration",250),("url",340)]: self.tree.heading(c,text=c.title()); self.tree.column(c,width=w)
  self.tree.pack(fill="both",expand=True,padx=15,pady=10)
  ttk.Button(self,text="Open Project",command=self.open).pack(pady=10)
  try:
   data=json.load(open(p))
   for x in data.get("source_repositories",[]): self.tree.insert("","end",values=(x["name"],x.get("integration",""),x["url"]))
  except Exception as e: messagebox.showerror("Catalog",str(e))
 def open(self):
  s=self.tree.selection()
  if not s:return
  url=self.tree.item(s[0],"values")[2]
  subprocess.Popen(["xdg-open",url])
if __name__=="__main__": App().mainloop()
