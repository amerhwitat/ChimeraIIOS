#!/usr/bin/env python3
"""Aurora Microsoft Network browser: DNS-SD discovery and SMB share navigation."""
import json,os,re,shutil,subprocess,tkinter as tk
from tkinter import ttk,messagebox
HELPER=os.environ.get("CHIMERA_SMB_BROWSER") or next((p for p in ("/usr/lib/chimera/network/chimera-smb-browse.py","/usr/lib64/chimera/network/chimera-smb-browse.py") if os.path.isfile(p)), "/usr/lib/chimera/network/chimera-smb-browse.py")
HOST_RE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9.:-]{0,252}$")
class Browser:
 def __init__(self,root):
  self.root=root;root.title("Aurora · Microsoft Network");root.geometry("760x520")
  top=ttk.Frame(root,padding=10);top.pack(fill="x")
  ttk.Label(top,text="Windows / SMB network").pack(side="left")
  ttk.Button(top,text="Discover computers",command=self.discover).pack(side="right")
  body=ttk.Panedwindow(root,orient="horizontal");body.pack(fill="both",expand=True,padx=10,pady=6)
  left=ttk.Frame(body);right=ttk.Frame(body);body.add(left,weight=1);body.add(right,weight=2)
  ttk.Label(left,text="Computers").pack(anchor="w")
  self.hosts=ttk.Treeview(left,columns=("host",),show="tree headings");self.hosts.heading("#0",text="Computer");self.hosts.heading("host",text="Address");self.hosts.pack(fill="both",expand=True)
  ttk.Label(right,text="Shared folders").pack(anchor="w")
  self.shares=ttk.Treeview(right,columns=("kind","comment"),show="tree headings");self.shares.heading("#0",text="Share");self.shares.heading("kind",text="Type");self.shares.heading("comment",text="Description");self.shares.pack(fill="both",expand=True)
  ttk.Button(right,text="Open selected share",command=self.open_share).pack(anchor="e",pady=8)
  self.status=tk.StringVar(value="Discovery uses Avahi DNS-SD. Share access uses Samba/GVFS and the desktop credential manager.")
  ttk.Label(root,textvariable=self.status,padding=8,wraplength=730).pack(fill="x")
  self.hosts.bind("<<TreeviewSelect>>",self.select_host);self.shares.bind("<Double-1>",lambda _:self.open_share())
  self.host_data={};self.share_data={}
 def invoke(self,args):
  return subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45,check=False)
 def discover(self):
  if not shutil.which("avahi-browse"):messagebox.showerror("Missing component","Install Avahi to discover SMB computers.");return
  try:
   p=self.invoke(["/usr/bin/python3",HELPER,"--discover"])
   if p.returncode:raise RuntimeError(p.stderr.strip() or "Discovery failed")
   data=json.loads(p.stdout);self.hosts.delete(*self.hosts.get_children());self.host_data={}
   for n,h in enumerate(data):
    address=h.get("host","")
    if not HOST_RE.fullmatch(address):continue
    iid=str(n);self.host_data[iid]=h
    self.hosts.insert("","end",iid=iid,text=h.get("name",address),values=(address,))
   self.status.set(f"Found {len(self.host_data)} SMB advertisements.")
  except Exception as e:messagebox.showerror("Network discovery failed",str(e))
 def select_host(self,_=None):
  sel=self.hosts.selection()
  if not sel:return
  h=self.host_data[sel[0]]["host"]
  self.shares.delete(*self.shares.get_children());self.share_data={}
  if not shutil.which("smbclient"):
   self.status.set("Install Samba client tools to enumerate shares. Double-click a computer to open it through GVFS.")
   return
  try:
   p=self.invoke(["/usr/bin/python3",HELPER,"--host",h,"--kerberos"])
   if p.returncode:raise RuntimeError(p.stderr.strip() or "SMB share enumeration failed; sign in to the domain or open the host to authenticate.")
   result=json.loads(p.stdout)
   for n,s in enumerate(result.get("shares",[])):
    iid=str(n);self.share_data[iid]=s
    self.shares.insert("","end",iid=iid,text=s["name"],values=(s["kind"],s.get("comment","")))
   self.status.set(f"{h}: {len(self.share_data)} shares. SMB access uses your Kerberos ticket or GVFS credential prompt.")
  except Exception as e:self.status.set(str(e))
 def open_share(self):
  hs=self.hosts.selection()
  if not hs:return
  host=self.host_data[hs[0]]["host"]
  ss=self.shares.selection()
  target=self.share_data[ss[0]]["name"] if ss else ""
  uri="smb://"+host+("/"+target if target else "")
  if not shutil.which("gio"):messagebox.showerror("Missing component","Install GIO/GVFS SMB support to open network shares.");return
  p=self.invoke(["gio","open",uri])
  if p.returncode:messagebox.showerror("Could not open SMB location",p.stderr.strip() or uri)
def main():
 root=tk.Tk();Browser(root);root.mainloop()
if __name__=="__main__":main()
