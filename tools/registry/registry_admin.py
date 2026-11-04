#!/usr/bin/env python3
"""Transactional CHMRG01 registry editor with a Tk GUI."""
import argparse,base64,fcntl,json,os,pathlib,sys,tempfile,time
HERE=pathlib.Path(__file__).resolve().parent
GLOBAL_ROOT=pathlib.Path(os.environ.get("CHIMERA_REGISTRY_ROOT","/var/lib/chimera/registry"))
USER_STATE=pathlib.Path(os.environ.get("XDG_STATE_HOME",str(pathlib.Path.home()/".local/state")))
USER_ROOT=pathlib.Path(os.environ.get("CHIMERA_USER_REGISTRY_ROOT",str(USER_STATE/"chimera/registry")))
def root_for(h): return USER_ROOT if h=="environment" and "CHIMERA_REGISTRY_ROOT" not in os.environ else GLOBAL_ROOT
DEFAULTS=pathlib.Path(os.environ.get("CHIMERA_REGISTRY_DEFAULTS","/usr/share/chimera/registry"))
HIVES=("machine","environment","kernel")
sys.path.insert(0,str(HERE))
import registry_hive
def fsync_dir(p):
 fd=os.open(str(p),os.O_RDONLY)
 try: os.fsync(fd)
 finally: os.close(fd)
def atomic_write(p,data,mode=0o600):
 p.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix=".registry-",dir=str(p.parent))
 try:
  os.fchmod(fd,mode)
  with os.fdopen(fd,"wb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
  os.replace(tmp,p); fsync_dir(p.parent)
 except Exception:
  try: os.unlink(tmp)
  except OSError: pass
  raise
def source_path(root,h): return root/"source"/(h+".json")
def hive_path(root,h): return root/"hives"/(h+".hive")
def recover_locked(root):
 j=root/"transaction.json"
 if not j.exists(): return
 tx=json.loads(j.read_text())
 if tx.get("schema")!="CHM-REGISTRY-TXN-1" or tx.get("phase")!="prepared": raise RuntimeError("invalid transaction journal")
 for x in tx["hives"]:
  if x["name"] not in HIVES: raise RuntimeError("unknown hive in journal")
  if root_for(x["name"]) != root: raise RuntimeError("cross-scope transaction journal rejected")
  atomic_write(source_path(root,x["name"]),base64.b64decode(x["source"],validate=True),0o644 if root==GLOBAL_ROOT else 0o600)
  atomic_write(hive_path(root,x["name"]),base64.b64decode(x["binary"],validate=True),0o644 if root==GLOBAL_ROOT else 0o600)
 j.unlink(); fsync_dir(root)
def load_hive(h):
 if h not in HIVES: raise ValueError("unknown hive")
 root=root_for(h); root.mkdir(parents=True,exist_ok=True)
 with (root/".lock").open("a+b") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX); recover_locked(root)
  p=source_path(root,h)
  if not p.exists():
   d=DEFAULTS/(h+".defaults.json")
   if not d.is_file(): raise FileNotFoundError("defaults not installed: "+str(d))
   atomic_write(p,d.read_bytes(),0o644 if root==GLOBAL_ROOT else 0o600)
  obj=json.loads(p.read_text()); registry_hive.encode(obj); return obj
def commit(objects):
 if not objects: return
 roots={root_for(h) for h in objects}
 if len(roots)!=1: raise ValueError("one registry transaction cannot span privilege scopes")
 root=next(iter(roots)); root.mkdir(parents=True,exist_ok=True)
 with (root/".lock").open("a+b") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX); recover_locked(root); items=[]
  for h,obj in objects.items():
   if h not in HIVES: raise ValueError("unknown hive")
   current_path=source_path(root,h)
   if current_path.exists(): current_generation=int(json.loads(current_path.read_text()).get("generation",0))
   else: current_generation=int(json.loads((DEFAULTS/(h+".defaults.json")).read_text()).get("generation",0))
   if int(obj.get("generation",0)) != current_generation: raise RuntimeError("registry generation conflict; reload before editing")
   obj["generation"]=current_generation+1
   src=(json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode()
   binary=registry_hive.encode(obj)
   items.append({"name":h,"source":base64.b64encode(src).decode(),"binary":base64.b64encode(binary).decode()})
  journal={"schema":"CHM-REGISTRY-TXN-1","phase":"prepared","created_unix":int(time.time()),"hives":items}
  atomic_write(root/"transaction.json",(json.dumps(journal,separators=(",",":"))+"\n").encode())
  recover_locked(root)
def authorize(h,p):
 if (h in ("machine","kernel") or p.startswith(("machine.","kernel."))) and hasattr(os,"geteuid") and os.geteuid()!=0:
  raise PermissionError("machine/kernel changes require administrator privileges")
def set_value(h,p,t,v):
 authorize(h,p); obj=load_hive(h); found=False
 for e in obj["entries"]:
  if e["path"]==p: e.update(type=t,value=v); found=True; break
 if not found: obj["entries"].append({"path":p,"type":t,"value":v})
 registry_hive.encode(obj); commit({h:obj})
def delete_value(h,p):
 authorize(h,p); obj=load_hive(h); entries=[e for e in obj["entries"] if e["path"]!=p]
 if len(entries)==len(obj["entries"]): raise KeyError(p)
 obj["entries"]=entries; commit({h:obj})
def launch_gui():
 import tkinter as tk
 from tkinter import ttk,messagebox,simpledialog
 root=tk.Tk(); root.title("Aurora Registry & System Settings"); root.geometry("920x620"); root.minsize(720,460)
 hive=tk.StringVar(value="environment"); search=tk.StringVar(); current={"obj":None}
 top=ttk.Frame(root,padding=10); top.pack(fill="x")
 ttk.Label(top,text="Registry hive").pack(side="left")
 combo=ttk.Combobox(top,textvariable=hive,values=HIVES,state="readonly",width=18); combo.pack(side="left",padx=8)
 ttk.Label(top,text="Search").pack(side="left",padx=(18,4)); ttk.Entry(top,textvariable=search,width=34).pack(side="left",fill="x",expand=True)
 tree=ttk.Treeview(root,columns=("type","value"),show="tree headings",selectmode="browse")
 tree.heading("#0",text="Registry path"); tree.heading("type",text="Type"); tree.heading("value",text="Value")
 tree.column("#0",width=360); tree.column("type",width=100); tree.column("value",width=360)
 tree.pack(fill="both",expand=True,padx=10,pady=6)
 status=tk.StringVar(value="Journaled local transactions; machine/kernel edits require administrator.")
 ttk.Label(root,textvariable=status,padding=8).pack(fill="x")
 def refresh(*_):
  try:
   obj=load_hive(hive.get()); current["obj"]=obj; tree.delete(*tree.get_children()); term=search.get().casefold()
   for e in obj["entries"]:
    if term and term not in e["path"].casefold() and term not in str(e["value"]).casefold(): continue
    tree.insert("","end",iid=e["path"],text=e["path"],values=(e["type"],str(e["value"])))
   status.set(f'{hive.get()} · generation {obj.get("generation",0)} · {len(obj["entries"])} entries')
  except Exception as e: messagebox.showerror("Registry error",str(e))
 def convert(t,v):
  if t in ("u32","u64"): return int(v,0)
  if t=="bool":
   if v.lower() not in ("true","false"): raise ValueError("Enter true or false")
   return v.lower()=="true"
  return v
 def edit(_=None):
  sel=tree.selection()
  if not sel:return
  p=sel[0]; e=next(x for x in current["obj"]["entries"] if x["path"]==p)
  v=simpledialog.askstring("Edit registry value",p,initialvalue=str(e["value"]),parent=root)
  if v is None:return
  try:set_value(hive.get(),p,e["type"],convert(e["type"],v));refresh()
  except Exception as ex:messagebox.showerror("Update failed",str(ex))
 def add():
  p=simpledialog.askstring("New entry","Canonical lowercase path:",parent=root)
  if not p:return
  t=simpledialog.askstring("Type","u32, u64, bool, string or bytes",initialvalue="string",parent=root)
  if t not in ("u32","u64","bool","string","bytes"):return
  v=simpledialog.askstring("Value",p,parent=root)
  if v is None:return
  try:set_value(hive.get(),p,t,convert(t,v));refresh()
  except Exception as ex:messagebox.showerror("Add failed",str(ex))
 def remove():
  sel=tree.selection()
  if sel and messagebox.askyesno("Delete entry","Delete "+sel[0]+"?",parent=root):
   try:delete_value(hive.get(),sel[0]);refresh()
   except Exception as ex:messagebox.showerror("Delete failed",str(ex))
 bar=ttk.Frame(root,padding=8);bar.pack(fill="x")
 ttk.Button(bar,text="Add entry",command=add).pack(side="left")
 ttk.Button(bar,text="Edit value",command=edit).pack(side="left",padx=6)
 ttk.Button(bar,text="Delete entry",command=remove).pack(side="left")
 ttk.Button(bar,text="Reload",command=refresh).pack(side="right")
 tree.bind("<Double-1>",edit);combo.bind("<<ComboboxSelected>>",refresh);search.trace_add("write",refresh);refresh();root.mainloop()
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True);s.add_parser("gui")
 a=s.add_parser("list");a.add_argument("hive",choices=HIVES)
 a=s.add_parser("get");a.add_argument("hive",choices=HIVES);a.add_argument("path")
 a=s.add_parser("set");a.add_argument("hive",choices=HIVES);a.add_argument("path");a.add_argument("type",choices=("u32","u64","bool","string","bytes"));a.add_argument("value")
 a=s.add_parser("delete");a.add_argument("hive",choices=HIVES);a.add_argument("path")
 x=p.parse_args()
 try:
  if x.cmd=="gui":launch_gui()
  elif x.cmd=="list":print(json.dumps(load_hive(x.hive),ensure_ascii=False,indent=2))
  elif x.cmd=="get":
   for e in load_hive(x.hive)["entries"]:
    if e["path"]==x.path:print(json.dumps(e,ensure_ascii=False));return 0
   return 1
  elif x.cmd=="set":
   v=x.value
   if x.type in ("u32","u64"):v=int(v,0)
   elif x.type=="bool":
    if v.lower() not in ("true","false"):raise ValueError("bool must be true or false")
    v=v.lower()=="true"
   set_value(x.hive,x.path,x.type,v)
  elif x.cmd=="delete":delete_value(x.hive,x.path)
  return 0
 except Exception as e:print("registry-admin: "+str(e),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
