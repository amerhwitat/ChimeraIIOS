#!/usr/bin/env python3
import subprocess,tkinter as tk
from tkinter import ttk,messagebox

def run(args,root=False):
    cmd=(["pkexec"] if root else [])+args
    try:return subprocess.check_output(cmd,text=True,stderr=subprocess.STDOUT,timeout=180)
    except Exception as e:return str(e)

root=tk.Tk(); root.title("Chimera II OS — Drivers / التعريفات"); root.geometry("820x620")
ttk.Label(root,text="Drivers & Hardware / التعريفات والأجهزة",font=("TkDefaultFont",18,"bold")).pack(pady=12)
status=tk.Text(root,wrap="word",height=27); status.pack(fill="both",expand=True,padx=14,pady=8)
def scan(): status.delete("1.0","end"); status.insert("end",run(["/usr/bin/chimera-hardware-drivers","scan"]))
def repair():
    if messagebox.askyesno("Chimera II OS","Install/repair supported drivers and firmware from signed repositories?\nتثبيت/إصلاح التعريفات والبرامج الثابتة من المستودعات الموثوقة؟"):
        status.delete("1.0","end"); status.insert("end",run(["/usr/bin/chimera-hardware-drivers","repair"],True))
        messagebox.showinfo("Chimera II OS","Driver repair finished. A reboot may be required.")
def sound():
    status.delete("1.0","end"); status.insert("end",run(["/usr/bin/chimera-hardware-drivers","audio"],True))
bar=ttk.Frame(root); bar.pack(fill="x",padx=14,pady=10)
for txt,fn in [("Scan / فحص",scan),("Audio / الصوت",sound),("Repair / إصلاح",repair)]:
    ttk.Button(bar,text=txt,command=fn).pack(side="left",padx=5)
scan(); root.mainloop()
