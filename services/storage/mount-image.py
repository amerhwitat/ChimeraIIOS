#!/usr/bin/env python3
"""Mount ISO/UDF images through udisks2 as read-only loop devices."""
import argparse
import json
import pathlib
import re
import subprocess
import sys

LOOP = re.compile(r"(/dev/loop[0-9]+)")
OPTICAL = re.compile(r"^/dev/sr[0-9]+$")

def run(argv, timeout=45):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)

def validate_image(path):
    image = pathlib.Path(path).resolve(strict=True)
    if not image.is_file() or image.stat().st_size < 17 * 2048:
        raise ValueError("image is not a plausible optical-disc image")
    with image.open("rb") as stream:
        stream.seek(16 * 2048 + 1)
        signature = stream.read(5)
        if signature == b"CD001":
            stream.seek(16 * 2048)
            if stream.read(1) != b"\x01":
                raise ValueError("invalid ISO-9660 primary volume descriptor type")
        if signature == b"BEA01":
            found_udf = False
            for sector in range(17, 33):
                stream.seek(sector * 2048 + 1)
                descriptor = stream.read(5)
                if descriptor in (b"NSR02", b"NSR03"):
                    found_udf = True
                    break
                if descriptor == b"TEA01":
                    break
            if not found_udf:
                raise ValueError("UDF recognition sequence is incomplete")
        elif signature != b"CD001":
            raise ValueError("ISO-9660/UDF volume descriptor not found")
    return image

def valid_optical_device(device):
    return bool(OPTICAL.fullmatch(device))

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mount")
    m.add_argument("image", type=pathlib.Path)
    d = sub.add_parser("mount-device")
    d.add_argument("device")
    u = sub.add_parser("unmount")
    u.add_argument("device")
    a = p.parse_args()
    try:
        if a.cmd == "mount":
            image = validate_image(a.image)
            setup = run(["udisksctl", "loop-setup", "--file", str(image), "--read-only"])
            if setup.returncode:
                raise RuntimeError(setup.stderr.strip() or "loop setup failed")
            match = LOOP.search(setup.stdout)
            if not match:
                raise RuntimeError("udisks2 did not return a loop device")
            device = match.group(1)
            mounted = run(["udisksctl", "mount", "--options", "ro,nodev,nosuid", "--block-device", device])
            if mounted.returncode:
                run(["udisksctl", "loop-delete", "--block-device", device])
                raise RuntimeError(mounted.stderr.strip() or "mount failed")
            print(json.dumps({"device": device, "read_only": True,
                              "mount": mounted.stdout.strip()}))
        elif a.cmd == "mount-device":
            if not valid_optical_device(a.device):
                raise ValueError("only optical /dev/srN devices are accepted")
            probe = run(["blkid", "-p", "-s", "TYPE", "-o", "value", a.device], timeout=10)
            if probe.returncode or probe.stdout.strip().lower() not in ("iso9660", "udf"):
                raise ValueError("device does not contain a recognized optical filesystem")
            mounted = run(["udisksctl", "mount", "--options", "ro,nodev,nosuid", "--block-device", a.device])
            if mounted.returncode:
                raise RuntimeError(mounted.stderr.strip() or "optical mount failed")
            print(json.dumps({"device": a.device, "read_only": True, "mount": mounted.stdout.strip()}))
        else:
            if not (LOOP.fullmatch(a.device) or valid_optical_device(a.device)):
                raise ValueError("invalid loop or optical device")
            result = run(["udisksctl", "unmount", "--block-device", a.device])
            if result.returncode:
                raise RuntimeError(result.stderr.strip())
            if LOOP.fullmatch(a.device):
                deleted = run(["udisksctl", "loop-delete", "--block-device", a.device])
                if deleted.returncode:
                    raise RuntimeError(deleted.stderr.strip())
            print(json.dumps({"device": a.device, "unmounted": True}))
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
