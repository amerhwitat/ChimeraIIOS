#!/usr/bin/env python3
"""Run pinned ISA import + universal catalog build + command candidate import."""
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def run(*args): subprocess.run([sys.executable, *map(str,args)], cwd=ROOT, check=True)
def main():
 run("tools/isa/import_riscv_opcodes.py")
 run("tools/isa/build_universal_catalog.py", "--input", "isa/sources/imports/riscv-opcodes.json")
 run("tools/commands/import_command_candidates.py")
 run("-m","unittest","tools.commands.test_import_command_candidates","tools.commands.test_command_candidate_router","-v")
if __name__ == "__main__": main()
