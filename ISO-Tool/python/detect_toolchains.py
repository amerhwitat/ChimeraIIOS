"""CLI for detecting/configuring compiler and assembler toolchains."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from iso_tool.toolchain_detector import detect_tools, apply_user_environment, write_report

def main(argv=None):
    ap=argparse.ArgumentParser(description="Detect ISO-Tool compiler/assembler dependencies before dependency resolution")
    ap.add_argument("--output", type=Path, help="JSON report path")
    ap.add_argument("--apply-user-env", action="store_true", help="Persist discovered HOME variables/PATH to the Windows user environment")
    args=ap.parse_args(argv)
    report=detect_tools()
    if args.apply_user_env:
        report["environment"] = apply_user_environment(report, persist=True)
    if args.output: write_report(report, args.output)
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__": raise SystemExit(main())
