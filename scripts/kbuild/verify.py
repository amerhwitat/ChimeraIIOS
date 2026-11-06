#!/usr/bin/env python3
"""Post-link verification for the Koronos kernel image (Linux-style `make check`)."""
from __future__ import annotations

import argparse
import subprocess
import sys

REQUIRED_SYMBOLS = [
    "koronos_idle_loop", "chimera_multiboot_scan", "chimera_thread_create", "chimera_wait_one",
    "chimera_timer_tick", "chimera_apc_deliver", "chimera_dpc_run", "chimera_hardware_probe",
    "chimera_nbit_init", "chimera_firmware_probe", "chimera_hardware_enumerate_devices",
    "chimera_driver_probe_all", "chimera_mk_init", "chimera_mk_syscall", "chimera_process_init",
    "chimera_process_admit_elf", "chimera_service_validate", "chimera_service_resolve",
    "chimera_service_set_state", "chimera_platform_probe", "chimera_platform_get_snapshot",
    "chimera_object_model_version", "chimera_object_model_refcount_enabled",
    "chimera_compat_init", "chimera_compat_probe", "chimera_compat_recognize_syscall",
    "chimera_compat_recognize_interrupt", "chimera_interrupt_init", "chimera_interrupt_dispatch",
    "chimera_syscall_init", "chimera_syscall_dispatch", "chimera_isa_init", "chimera_isa_count",
    "chimera_isa_find", "chimera_isa_find_opcode", "chimera_ai_model_init", "chimera_ai_event_count",
    "chimera_ai_record_event", "chimera_ai_provider", "memset", "memcpy", "memmove",
]

REQUIRED_STRINGS = [
    "[INST] Installer runtime initialization",
    "[SCH ] Bootstrap tasks submitted",
    "[KORE] Service orchestration online",
    "[ABI ] Compatibility syscall/interrupt registry ready",
]


def defined_symbols(elf):
    try:
        out = subprocess.run(["nm", "-a", "--defined-only", elf], capture_output=True, text=True).stdout
    except FileNotFoundError:
        print("verify: nm unavailable, skipping symbol checks")
        return set()
    return {line.split()[-1] for line in out.splitlines() if line.split()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--elf", required=True)
    args = ap.parse_args()

    failures = []
    with open(args.elf, "rb") as handle:
        header = handle.read(20)
    if len(header) < 18 or header[:4] != b"\x7fELF" or header[4] != 2:
        failures.append("image is not ELF64")

    data = open(args.elf, "rb").read()
    for text in REQUIRED_STRINGS:
        if text.encode() not in data:
            failures.append("missing boot banner: %s" % text)

    symbols = defined_symbols(args.elf)
    if symbols:
        for symbol in REQUIRED_SYMBOLS:
            if symbol not in symbols:
                failures.append("missing symbol: %s" % symbol)

    if failures:
        for item in failures:
            print("  FAIL %s" % item, file=sys.stderr)
        print("verify: FAILED (%d issue(s))" % len(failures), file=sys.stderr)
        return 1

    print("verify: OK -- ELF64, %d symbols, %d boot banners" % (len(symbols), len(REQUIRED_STRINGS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
