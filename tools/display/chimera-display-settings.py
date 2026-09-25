#!/usr/bin/env python3
import os,re,shutil,subprocess,tkinter as tk
from tkinter import ttk,messagebox

def run(cmd):
    try: return subprocess.check_output(cmd,text=True,stderr=subprocess.STDOUT,timeout=15)
    except Exception as e: return str(e)

def parse():
    rows=[]
    if os.environ.get("WAYLAND_DISPLAY"):
        if shutil.which("wlr-randr"):
            out=run(["wlr-randr"]); current=None
            for line in out.splitlines():
                if line and not line[0].isspace(): current=line.split()[0]
                m=re.search(r"(\d+x\d+)(?:\s+|$)",line.strip())
                if current and m and m.group(1).split("x")[0].isdigit(): rows.append((current,m.group(1)))
            if rows: return rows,"wlr"
    if os.environ.get("DISPLAY") and shutil.which("xrandr"):
        out=run(["xrandr","--query"]); current=None
        for line in out.splitlines():
            m=re.match(r"^(\S+) connected",line)
            if m: current=m.group(1)
            m=re.match(r"^\s+(\d+x\d+)(?:\s|$)",line)
            if current and m: rows.append((current,m.group(1)))
        if rows: return rows,"xrandr"
    return [],"none"

def apply(output,mode):
    try:
        subprocess.check_call(["chimera-display","set",output,mode],timeout=20)
        return True
    except Exception as e:
        messagebox.showerror("Chimera II OS",f"Display change failed / فشل تغيير العرض:\n{e}")
        return False

root=tk.Tk(); root.title("Chimera II OS — Display / الشاشة"); root.geometry("560x360"); root.minsize(520,320)
rows,backend=parse()
ttk.Label(root,text="Display / الشاشة",font=("TkDefaultFont",16,"bold")).pack(pady=(18,8))
ttk.Label(root,text=f"Backend: {backend}").pack(pady=2)
if not rows:
    ttk.Label(root,text="No display modes were detected.\nInstall/enable the graphics driver first.",justify="center").pack(pady=35)
    ttk.Button(root,text="Close / إغلاق",command=root.destroy).pack(); root.mainloop(); raise SystemExit
outputs=sorted(dict.fromkeys(x[0] for x in rows))
modes=sorted(dict.fromkeys(x[1] for x in rows),key=lambda x:(int(x.split("x")[0]),int(x.split("x")[1])))
ov=tk.StringVar(value=outputs[0]); mv=tk.StringVar(value=modes[-1])
frame=ttk.Frame(root,padding=20); frame.pack(fill="both",expand=True); frame.columnconfigure(1,weight=1)
ttk.Label(frame,text="Output / الشاشة").grid(row=0,column=0,sticky="w",pady=8)
ttk.Combobox(frame,textvariable=ov,values=outputs,state="readonly").grid(row=0,column=1,sticky="ew",pady=8)
ttk.Label(frame,text="Resolution / الدقة").grid(row=1,column=0,sticky="w",pady=8)
ttk.Combobox(frame,textvariable=mv,values=modes,state="readonly").grid(row=1,column=1,sticky="ew",pady=8)
ttk.Label(frame,text="Changes are saved for the current user and restored at Aurora session start.").grid(row=2,column=0,columnspan=2,pady=18)
def do_apply():
    if apply(ov.get(),mv.get()): messagebox.showinfo("Chimera II OS","Resolution applied. / تم تطبيق الدقة.")
ttk.Button(frame,text="Apply / تطبيق",command=do_apply).grid(row=3,column=0,columnspan=2,pady=8)
ttk.Button(frame,text="Close / إغلاق",command=root.destroy).grid(row=4,column=0,columnspan=2,pady=4)
root.mainloop()
