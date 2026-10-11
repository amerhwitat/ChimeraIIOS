#!/usr/bin/env python3
"""Select a Chimera N-bit execution profile for the installer/runtime handoff.

This writes policy only; the kernel must validate the selected profile against
its probed hardware profile and resource limits before admitting a process.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "nbit-mode.json"
COMPATIBILITY = {"native", "windows", "linux", "bsd", "darwin", "android", "ios"}
BACKENDS = {"auto", "chimera-virtual", "physical-native", "compatibility"}


def build_profile(bits: int, backend: str, compatibility: str | None) -> dict:
    if not 1 <= bits <= 0xFFFFFFFF:
        raise ValueError("bit width must be an integer in the range 1..4294967295")
    if backend not in BACKENDS:
        raise ValueError(f"backend must be one of: {', '.join(sorted(BACKENDS))}")
    if compatibility is not None and compatibility not in COMPATIBILITY:
        raise ValueError(f"compatibility must be one of: {', '.join(sorted(COMPATIBILITY))}")
    if backend == "compatibility" and compatibility is None:
        raise ValueError("compatibility backend requires --compatibility")
    if backend != "compatibility" and compatibility is not None:
        raise ValueError("--compatibility is only valid with --backend compatibility")
    if backend == "physical-native" and bits not in (8, 16, 32, 64, 128):
        # This is only a conservative request shape check; hardware identity is
        # unknown here and the kernel must enforce the exact physical native width.
        raise ValueError("physical-native requires a conventional candidate width; kernel verifies the exact CPU width")
    return {
        "schema": "CHIMERA-NBIT-USER-PROFILE-1",
        "selected_width_bits": bits,
        "backend": backend,
        "compatibility_personality": compatibility,
        "physical_native_width_is_hardware_defined": True,
        "arbitrary_width_virtual_abi": True,
        "validation_required_at_kernel_admission": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bits", type=int, help="selected process width, any positive integer up to 4294967295")
    parser.add_argument("--backend", choices=sorted(BACKENDS), default="auto")
    parser.add_argument("--compatibility", choices=sorted(COMPATIBILITY))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--show", action="store_true", help="show current selection")
    args = parser.parse_args()
    if args.show and args.bits is None:
        if not args.config.exists():
            print(json.dumps({"schema": "CHIMERA-NBIT-USER-PROFILE-1", "selected_width_bits": 64, "backend": "auto"}, indent=2))
            return 0
        print(args.config.read_text(encoding="utf-8"))
        return 0
    if args.bits is None:
        try:
            raw = input("Choose Chimera N-bit width (any positive integer, default 64): ").strip()
            bits = int(raw or "64", 10)
            backend = input("Backend [auto/chimera-virtual/physical-native/compatibility] (default auto): ").strip() or "auto"
            compatibility = None
            if backend == "compatibility":
                compatibility = input("Compatibility [native/windows/linux/bsd/darwin/android/ios]: ").strip().lower()
        except (EOFError, ValueError):
            parser.error("interactive selection failed; pass --bits and --backend")
    else:
        bits, backend, compatibility = args.bits, args.backend, args.compatibility
    try:
        profile = build_profile(bits, backend, compatibility)
    except ValueError as exc:
        parser.error(str(exc))
    args.config.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.config.with_suffix(args.config.suffix + ".tmp")
    temporary.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.config)
    print(json.dumps(profile, indent=2))
    print(f"Saved selection to {args.config}")
    print("The kernel must validate this profile; a virtual width is not a claim of physical CPU-native instructions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
