#!/usr/bin/env python3
"""Aurora package manager front end for Chimera's provider-neutral CLI."""
import os, shutil, subprocess, tkinter as tk
from tkinter import messagebox, simpledialog, ttk
BRIDGE = os.environ.get("CHIMERA_PKG_BRIDGE", "/usr/bin/chimera-pkg")
MANAGERS = ("auto", "apt", "dnf", "pacman", "zypper", "apk", "snap", "flatpak", "brew", "nix")
class PackageManagerPanel(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Aurora · Package Managers"); self.geometry("880x560"); self.minsize(700,440); self.configure(bg="#101827")
        header=tk.Frame(self,bg="#18263b",padx=18,pady=14); header.pack(fill="x")
        tk.Label(header,text="CHIMERA II  /  AURORA",bg="#18263b",fg="#8de4ff",font=("TkDefaultFont",10,"bold")).pack(anchor="w")
        tk.Label(header,text="Package Manager Center",bg="#18263b",fg="#f3f7ff",font=("TkDefaultFont",20,"bold")).pack(anchor="w",pady=(4,0))
        controls=ttk.Frame(self,padding=12); controls.pack(fill="x"); ttk.Label(controls,text="Provider").pack(side="left")
        self.provider=tk.StringVar(value=os.environ.get("CHIMERA_PKG_MANAGER","auto"))
        ttk.Combobox(controls,textvariable=self.provider,values=MANAGERS,state="readonly",width=14).pack(side="left",padx=8)
        ttk.Button(controls,text="Detect",command=self.status).pack(side="left",padx=3)
        ttk.Button(controls,text="Installed",command=lambda:self.run_action("list")).pack(side="left",padx=3)
        ttk.Button(controls,text="Refresh / Update",command=lambda:self.run_action("update",confirm=True)).pack(side="left",padx=3)
        ttk.Button(controls,text="Search",command=self.search).pack(side="left",padx=3)
        ttk.Button(controls,text="Install",command=lambda:self.run_action("install",prompt=True,confirm=True)).pack(side="left",padx=3)
        ttk.Button(controls,text="Remove",command=lambda:self.run_action("remove",prompt=True,confirm=True)).pack(side="left",padx=3)
        body=ttk.Frame(self,padding=(12,0,12,12)); body.pack(fill="both",expand=True)
        self.output=tk.Text(body,wrap="word",bg="#0b1220",fg="#dce8f8",insertbackground="white",relief="flat",padx=12,pady=12)
        scroll=ttk.Scrollbar(body,command=self.output.yview); self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(side="left",fill="both",expand=True); scroll.pack(side="right",fill="y")
        self.status_line=tk.StringVar(value="Ready · providers are optional and detected at runtime")
        ttk.Label(self,textvariable=self.status_line,anchor="w",padding=8).pack(fill="x"); self.status()
    def bridge(self):
        if os.path.isfile(BRIDGE) and os.access(BRIDGE,os.X_OK): return BRIDGE
        return shutil.which("chimera-pkg") or BRIDGE
    def write(self,text):
        self.output.delete("1.0","end"); self.output.insert("end",text); self.output.see("end")
    def invoke(self,args):
        bridge=self.bridge()
        if not os.path.exists(bridge) and not shutil.which(bridge):
            self.write("Package manager bridge is missing. Rebuild the ISO or install tools/chimera-package-manager.sh as /usr/bin/chimera-pkg."); return
        try:
            result=subprocess.run([bridge]+args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180,check=False)
            self.write(result.stdout or ("Completed." if result.returncode==0 else "Command failed."))
            self.status_line.set("Completed" if result.returncode==0 else f"Command exited with status {result.returncode}")
        except subprocess.TimeoutExpired:
            self.write("The operation exceeded 180 seconds. Check the package manager or retry from a terminal."); self.status_line.set("Timed out")
    def status(self): self.invoke(["status"])
    def run_action(self,action,prompt=False,confirm=False):
        args=[action]
        if prompt:
            package=simpledialog.askstring(action.title(),f"Package name to {action}:",parent=self)
            if not package:return
            package=package.strip()
            if not package or package.startswith("-") or "\n" in package or "\r" in package:
                messagebox.showerror("Invalid package","Enter a single package identifier.",parent=self); return
            args.append(package)
        if confirm:
            desc=f"{action.title()} using {self.provider.get()}?"
            if prompt: desc=f"{action.title()} package '{args[1]}' using {self.provider.get()}?"
            if not messagebox.askyesno("Confirm package operation",desc,parent=self):return
        args.append(self.provider.get()); self.invoke(args)
    def search(self):
        query=simpledialog.askstring("Search packages","Search for:",parent=self)
        if query and query.strip():self.invoke(["search",query.strip(),self.provider.get()])
if __name__=="__main__": PackageManagerPanel().mainloop()
