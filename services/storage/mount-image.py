#!/usr/bin/env python3
"""Mount ISO/UDF images through udisks2 as read-only loop devices."""
import argparse
import json
import pathlib
import re
import subprocess
import sys

LOOP = re.compile(r"(/dev/loop[0-9]+)")

def run(argv, timeout=45):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mount")
    m.add_argument("image", type=pathlib.Path)
    u = sub.add_parser("unmount")
    u.add_argument("device")
    a = p.parse_args()
    try:
        if a.cmd == "mount":
            image = a.image.resolve(strict=True)
            if not image.is_file() or image.stat().st_size < 17 * 2048:
                raise ValueError("image is not a plausible optical-disc image")
            with image.open("rb") as stream:
                stream.seek(16 * 2048 + 1)
                if stream.read(5) != b"CD001":
                    raise ValueError("ISO-9660 primary volume descriptor not found")
            setup = run(["udisksctl", "loop-setup", "--file", str(image), "--read-only"])
            if setup.returncode:
                raise RuntimeError(setup.stderr.strip() or "loop setup failed")
            match = LOOP.search(setup.stdout)
            if not match:
                raise RuntimeError("udisks2 did not return a loop device")
            device = match.group(1)
            mounted = run(["udisksctl", "mount", "--block-device", device])
            if mounted.returncode:
                run(["udisksctl", "loop-delete", "--block-device", device])
                raise RuntimeError(mounted.stderr.strip() or "mount failed")
            print(json.dumps({"device": device, "read_only": True,
                              "mount": mounted.stdout.strip()}))
        else:
            if not LOOP.fullmatch(a.device):
                raise ValueError("invalid loop device")
            result = run(["udisksctl", "unmount", "--block-device", a.device])
            if result.returncode:
                raise RuntimeError(result.stderr.strip())
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
