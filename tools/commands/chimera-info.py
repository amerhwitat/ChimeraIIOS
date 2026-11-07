#!/usr/bin/env python3
"""Report measured Chimera host, kernel, architecture and boot information."""
import os, platform
from pathlib import Path

def read_first(path):
    try: return Path(path).read_text(encoding="utf-8",errors="replace").strip().splitlines()[0]
    except (OSError,IndexError): return "unavailable"

def main():
    print("Chimera II OS system information")
    print(f"Hostname: {platform.node() or 'unknown'}")
    print(f"Kernel: {platform.system()} {platform.release()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor() or 'not reported'}")
    print(f"Logical CPUs: {os.cpu_count() or 'unknown'}")
    print(f"OS release: {read_first('/etc/os-release')}")
    print(f"Boot mode: {'UEFI' if Path('/sys/firmware/efi').exists() else 'BIOS/legacy or unavailable'}")
    print(f"Memory: {read_first('/proc/meminfo')}")
    print(f"Koronos marker: {'present' if Path('/sys/kernel/koronos').exists() else 'not exposed by this running kernel'}")
    return 0
if __name__ == "__main__": raise SystemExit(main())
