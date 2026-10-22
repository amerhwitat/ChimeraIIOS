#!/usr/bin/env python3
"""Aurora Flash Tool: safe Chimera image/media writer front end."""
import argparse, hashlib, os, re, shutil, stat, subprocess, sys, tempfile

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
    if not os.path.isfile(image):
        raise SystemExit("Image not found")
    if not device.startswith("/dev/"):
        raise SystemExit("Target must be an explicit /dev/... device path")
    if not os.path.exists(device):
        raise SystemExit("Target device not found")
    if not stat.S_ISBLK(os.stat(device).st_mode):
        raise SystemExit("Refusing non-block-device target")
    if not expected_sha256 or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise SystemExit("A 64-character expected SHA-256 is required")
    expected_sha256 = expected_sha256.lower()
    actual = sha256(image).lower()
    if actual != expected_sha256:
        raise SystemExit("SHA-256 mismatch; refusing to flash")
    if not os.environ.get("CHIMERA_FLASH_CONFIRM") == "YES":
        raise SystemExit("Set CHIMERA_FLASH_CONFIRM=YES only after verifying the selected removable target.")
    image_size = os.path.getsize(image)
    subprocess.run(["sync"], check=False)
    with open(image, "rb") as src, open(device, "r+b", buffering=0) as dst:
        shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)
        dst.flush()
        os.fsync(dst.fileno())
    subprocess.run(["sync"], check=False)
    # Read back exactly the image-length prefix and verify the bytes written.
    h = hashlib.sha256()
    remaining = image_size
    with open(device, "rb", buffering=0) as dst:
        while remaining:
            chunk = dst.read(min(1024 * 1024, remaining))
            if not chunk:
                raise SystemExit("Post-write verification failed: short read from target")
            h.update(chunk)
            remaining -= len(chunk)
    if h.hexdigest().lower() != expected_sha256:
        raise SystemExit("Post-write verification failed: target SHA-256 mismatch")

p=argparse.ArgumentParser(description="Aurora Flash Tool")
p.add_argument("--list",action="store_true")
p.add_argument("--image"); p.add_argument("--device"); p.add_argument("--sha256", required=False)
a=p.parse_args()
if a.list: print(devices()); raise SystemExit(0)
if not a.image or not a.device: p.error("--image and --device are required")
flash(a.image,a.device,a.sha256)
print("Flash completed. Re-read/verify the target before rebooting.")
