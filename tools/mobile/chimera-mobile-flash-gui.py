#!/usr/bin/env python3
"""Chimera II OS Mobile Flash Tool GUI.

Cross-platform Tkinter front end for the owner-authorized mobile tooling.
It discovers Android/iOS devices, validates Chimera artifacts and invokes
existing CLI operations. It deliberately does not bypass FRP, Activation
Lock, MDM, carrier restrictions, or OEM security controls.
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parents[2]
CLI = Path(__file__).with_name("chimera-mobile-flash.sh")


def run_cmd(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except FileNotFoundError:
        return 127, f"Missing dependency: {cmd[0]}"
    except Exception as exc:
        return 1, str(exc)


def find_iso():
    roots = [ROOT / "build", ROOT / "output", ROOT / "dist",
             Path("/mnt/c/chimera-output"), ROOT / "artifacts"]
    candidates = []
    for root in roots:
        if root.exists():
            candidates.extend(root.rglob("*.iso"))
    candidates = [p for p in candidates if p.is_file()]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chimera II OS — Mobile Flash Tool")
        self.geometry("1120x720")
        self.minsize(900, 600)
        self.q = queue.Queue()
        self.iso = tk.StringVar(value="")
        self.device = tk.StringVar(value="auto")
        self.status = tk.StringVar(value="Ready — no device operation has been performed.")
        self._style()
        self._build()
        self.after(100, self._drain)
        self.after(250, self.detect)

    def _style(self):
        s = ttk.Style(self)
        try: s.theme_use("clam")
        except tk.TclError: pass
        s.configure("Title.TLabel", font=("TkDefaultFont", 20, "bold"))
        s.configure("Card.TLabelframe", padding=12)
        s.configure("Danger.TButton", padding=8)
        s.configure("Action.TButton", padding=8)

    def _build(self):
        top = ttk.Frame(self, padding=18); top.pack(fill="x")
        ttk.Label(top, text="Chimera II OS Mobile Flash Tool", style="Title.TLabel").pack(anchor="w")
        ttk.Label(top, text="Detection • compatibility • recovery • authorized deployment").pack(anchor="w", pady=(4, 0))

        paths = ttk.LabelFrame(self, text="Target", style="Card.TLabelframe"); paths.pack(fill="x", padx=18, pady=8)
        ttk.Label(paths, text="Chimera ISO:").grid(row=0, column=0, sticky="w")
        ttk.Entry(paths, textvariable=self.iso, width=82).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(paths, text="Auto", command=self.auto_iso).grid(row=0, column=2)
        ttk.Button(paths, text="Browse…", command=self.browse_iso).grid(row=0, column=3, padx=(6, 0))
        ttk.Label(paths, text="Device:").grid(row=1, column=0, sticky="w", pady=8)
        ttk.Entry(paths, textvariable=self.device, width=30).grid(row=1, column=1, sticky="w", padx=8)
        ttk.Button(paths, text="Detect device", command=self.detect).grid(row=1, column=2, columnspan=2, sticky="w")
        paths.columnconfigure(1, weight=1)

        actions = ttk.LabelFrame(self, text="Operations", style="Card.TLabelframe"); actions.pack(fill="x", padx=18, pady=8)
        buttons = [
            ("Detect", self.detect), ("Validate ISO", self.validate_iso),
            ("Android information", self.android_info),
            ("OEM unlock preparation", self.android_unlock),
            ("Recovery / reboot", self.recovery),
            ("Dry-run deployment", self.dry_run),
            ("Flash explicitly mapped image…", self.flash),
            ("iOS information", self.ios_info),
        ]
        for i, (label, fn) in enumerate(buttons):
            ttk.Button(actions, text=label, command=fn, style="Action.TButton").grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
        for i in range(4): actions.columnconfigure(i, weight=1)

        body = ttk.Panedwindow(self, orient="horizontal"); body.pack(fill="both", expand=True, padx=18, pady=8)
        info = ttk.LabelFrame(body, text="Device / artifact report", style="Card.TLabelframe")
        log = ttk.LabelFrame(body, text="Operation log", style="Card.TLabelframe")
        body.add(info, weight=1); body.add(log, weight=2)
        self.info_text = tk.Text(info, wrap="word", state="disabled", height=20)
        self.info_text.pack(fill="both", expand=True)
        self.log_text = tk.Text(log, wrap="word", state="disabled", height=20)
        self.log_text.pack(fill="both", expand=True)
        bottom = ttk.Frame(self, padding=(18, 4, 18, 14)); bottom.pack(fill="x")
        ttk.Label(bottom, textvariable=self.status).pack(side="left")
        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=240); self.progress.pack(side="right")

    def log(self, text): self.q.put(("log", text))
    def info(self, text): self.q.put(("info", text))

    def _drain(self):
        try:
            while True:
                typ, text = self.q.get_nowait()
                widget = self.log_text if typ == "log" else self.info_text
                widget.configure(state="normal"); widget.insert("end", text + "\n"); widget.see("end"); widget.configure(state="disabled")
        except queue.Empty: pass
        self.after(100, self._drain)

    def worker(self, fn):
        self.progress.start(10); self.status.set("Working…")
        def go():
            try: fn()
            finally: self.q.put(("status", ""))
        threading.Thread(target=go, daemon=True).start()
        self.after(150, self._status_tick)

    def _status_tick(self):
        try:
            item = self.q.queue[0] if self.q.queue else None
            if item and item[0] == "status":
                self.q.get_nowait(); self.progress.stop(); self.status.set("Ready")
            else: self.after(150, self._status_tick)
        except Exception: self.after(150, self._status_tick)

    def auto_iso(self):
        p = find_iso()
        self.iso.set(str(p) if p else "")
        self.log(f"ISO auto-discovery: {p or 'none found'}")

    def browse_iso(self):
        p = filedialog.askopenfilename(title="Select Chimera II OS ISO", filetypes=[("ISO images", "*.iso"), ("All files", "*.*")])
        if p: self.iso.set(p)

    def detect(self):
        def work():
            data = {}
            code, out = run_cmd(["adb", "devices", "-l"])
            data["ADB"] = out or f"unavailable (exit {code})"
            code, out = run_cmd(["fastboot", "devices"])
            data["Fastboot"] = out or f"unavailable (exit {code})"
            self.info(json.dumps(data, indent=2))
            self.log("Device detection completed.")
        self.worker(work)

    def validate_iso(self):
        p = Path(self.iso.get()) if self.iso.get() else find_iso()
        if not p or not p.is_file(): messagebox.showerror("ISO", "No Chimera ISO found or selected."); return
        self.iso.set(str(p))
        self.info(f"ISO: {p}\nSize: {p.stat().st_size:,} bytes\nSHA-256: {sha256(p)}")
        self.log("ISO validation: file exists and SHA-256 calculated.")

    def android_info(self):
        def work():
            props = ["ro.product.manufacturer", "ro.product.model", "ro.product.device", "ro.product.cpu.abi", "ro.board.platform", "ro.bootloader", "ro.boot.verifiedbootstate"]
            rows=[]
            for prop in props:
                c,o=run_cmd(["adb","shell","getprop",prop]); rows.append(f"{prop}: {o if c==0 else 'unavailable'}")
            self.info("\n".join(rows)); self.log("Android information queried through adb.")
        self.worker(work)

    def android_unlock(self):
        if not messagebox.askyesno("OEM unlock", "Continue to the device's OEM-supported bootloader unlock preparation?\n\nThis does not bypass security controls. OEM unlocking may erase user data."): return
        def work():
            c,o=run_cmd(["adb","reboot","bootloader"]); self.log(o or f"adb exit {c}"); self.log("Complete any OEM unlock confirmation shown on the device.")
        self.worker(work)

    def recovery(self):
        def work():
            c,o=run_cmd(["adb","reboot","bootloader"]); self.log(o or f"adb exit {c}")
        self.worker(work)

    def dry_run(self):
        self.auto_iso()
        self.validate_iso()
        self.detect()
        self.log("DRY RUN: no partition write will be performed.")

    def flash(self):
        messagebox.showinfo("Explicit flash required", "Select a device-specific image and partition mapping. The GUI will not guess a partition or perform ambiguous flashing.")

    def ios_info(self):
        def work():
            c,o=run_cmd(["idevice_id","-l"]); self.info(o or f"libimobiledevice unavailable (exit {c})"); self.log("iOS detection completed; no security bypass attempted.")
        self.worker(work)


if __name__ == "__main__":
    App().mainloop()
