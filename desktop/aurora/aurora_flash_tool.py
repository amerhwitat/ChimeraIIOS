#!/usr/bin/env python3
"""Aurora Flash Tool: safe Chimera image/media writer front end."""
import argparse, hashlib, os, shutil, subprocess, sys, tempfile

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def devices():
    try:
        out=subprocess.check_output(["lsblk","-J","-o","NAME,PATH,TYPE,SIZE,RM,MODEL,TRAN"],text=True)
        return out
    except Exception as e:
        return '{"error":%r}'%str(e)

def flash(image, device, expected_sha256=None):
    if not os.path.isfile(image): raise SystemExit("Image not found")
    if not os.path.exists(device): raise SystemExit("Target device not found")
    if expected_sha256 and sha256(image).lower()!=expected_sha256.lower(): raise SystemExit("SHA-256 mismatch")
    if os.path.realpath(device)==os.path.realpath(os.sep): raise SystemExit("Refusing root filesystem target")
    if not os.environ.get("CHIMERA_FLASH_CONFIRM")=="YES":
        raise SystemExit("Set CHIMERA_FLASH_CONFIRM=YES only after verifying the selected removable target.")
    subprocess.run(["sync"],check=False)
    with open(image,"rb") as src, open(device,"wb",buffering=0) as dst:
        shutil.copyfileobj(src,dst,length=4*1024*1024)
        dst.flush(); os.fsync(dst.fileno())
    subprocess.run(["sync"],check=False)

p=argparse.ArgumentParser(description="Aurora Flash Tool")
p.add_argument("--list",action="store_true")
p.add_argument("--image"); p.add_argument("--device"); p.add_argument("--sha256")
a=p.parse_args()
if a.list: print(devices()); raise SystemExit(0)
if not a.image or not a.device: p.error("--image and --device are required")
flash(a.image,a.device,a.sha256)
print("Flash completed. Re-read/verify the target before rebooting.")
