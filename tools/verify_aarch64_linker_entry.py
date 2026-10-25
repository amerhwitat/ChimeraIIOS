#!/usr/bin/env python3
"""Verify an AArch64 linker script's entry contract and a linked ELF's entry symbol."""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path

class ContractError(ValueError):
    pass

def validate_linker_script(script: str) -> None:
    required = {
        "OUTPUT_FORMAT": r"\bOUTPUT_FORMAT\s*\(\s*elf64-littleaarch64\s*\)",
        "OUTPUT_ARCH": r"\bOUTPUT_ARCH\s*\(\s*aarch64\s*\)",
        "ENTRY": r"\bENTRY\s*\(\s*kernel_entry\s*\)",
        "PHDRS": r"\bPHDRS\s*\{",
        "PT_LOAD": r"\bPT_LOAD\b",
    }
    for label, pattern in required.items():
        if not re.search(pattern, script):
            raise ContractError(f"linker script is missing required {label} contract")
    if not re.search(r"\bkernel_entry\b", script):
        raise ContractError("kernel_entry symbol is not referenced by the linker script")

def parse_nm_symbols(output: str) -> set[str]:
    symbols = set()
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 3 and re.fullmatch(r"[A-Za-z?]", fields[-2]):
            symbols.add(fields[-1].split("@", 1)[0])
    return symbols

def validate_entry_symbol(script: str, nm_output: str) -> None:
    validate_linker_script(script)
    if "kernel_entry" not in parse_nm_symbols(nm_output):
        raise ContractError("linked ELF does not define kernel_entry (nm -g --defined-only)")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--elf", required=True, type=Path)
    args = parser.parse_args()
    try:
        script = args.script.read_text(encoding="utf-8")
        if not args.elf.is_file() or args.elf.stat().st_size == 0:
            raise ContractError(f"linked ELF is missing or empty: {args.elf}")
        validator = Path(__file__).with_name("validate_elf_image.py")
        subprocess.run([sys.executable, str(validator), "--target", "aarch64", str(args.elf)], check=True)
        nm = subprocess.run(["nm", "-g", "--defined-only", str(args.elf)], check=True,
                            capture_output=True, text=True)
        validate_entry_symbol(script, nm.stdout)
    except (OSError, subprocess.CalledProcessError, ContractError) as exc:
        print(f"[AARCH64 LINKER ENTRY REJECTED] {exc}", file=sys.stderr)
        return 1
    print(f"[AARCH64 LINKER ENTRY VALID] script={args.script} elf={args.elf} symbol=kernel_entry")
    print("NOTE: this verifies script/symbol structure, not firmware boot or runtime acceptance.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
