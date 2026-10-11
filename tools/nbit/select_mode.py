#!/usr/bin/env python3
"""Select a Chimera N-bit execution profile for installer/runtime handoff.

This writes policy only; the kernel validates the selected profile against
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
BACKEND_IDS = {"auto": 0, "chimera-virtual": 1, "physical-native": 2, "compatibility": 3}
ISA_IDS = {"auto":0,"chimera-nbit":1,"x86-16":2,"x86-32":3,"x86-64":4,"aarch64":5,
           "arm32":6,"arm32-thumb":7,"riscv32":8,"riscv64":9,"riscv128":10,"mips32":11,
           "mips64":12,"powerpc":13,"ppc64":14,"loongarch32":15,"loongarch64":16,
           "s390x":17,"sparc-v9":18,"wasm32":19,"wasm64":20}
COMPATIBILITY_MASKS = {"native":1,"windows":2,"linux":4,"bsd":8,"darwin":16,"android":32,"ios":64}
ISA_TARGETS = {
    "auto", "chimera-nbit", "x86-16", "x86-32", "x86-64", "aarch64",
    "arm32", "arm32-thumb", "riscv32", "riscv64", "riscv128", "mips32",
    "mips64", "powerpc", "ppc64", "loongarch32", "loongarch64", "s390x",
    "sparc-v9", "wasm32", "wasm64"
}


def build_profile(bits: int, backend: str, compatibility: str | None,
                  isa: str = "auto") -> dict:
    if not 1 <= bits <= 0xFFFFFFFF:
        raise ValueError("bit width must be an integer in the range 1..4294967295")
    if backend not in BACKENDS:
        raise ValueError(f"backend must be one of: {', '.join(sorted(BACKENDS))}")
    if isa not in ISA_TARGETS:
        raise ValueError(f"ISA must be one of: {', '.join(sorted(ISA_TARGETS))}")
    if compatibility is not None and compatibility not in COMPATIBILITY:
        raise ValueError(f"compatibility must be one of: {', '.join(sorted(COMPATIBILITY))}")
    if backend == "compatibility" and compatibility is None:
        raise ValueError("compatibility backend requires --compatibility")
    if backend != "compatibility" and compatibility is not None:
        raise ValueError("--compatibility is only valid with --backend compatibility")
    guest_isa = "chimera-nbit" if backend == "chimera-virtual" and isa == "auto" else isa
    return {
        "schema": "CHIMERA-NBIT-USER-PROFILE-1",
        "selected_width_bits": bits,
        "width_policy": "explicit",
        "backend": backend,
        "backend_id": BACKEND_IDS[backend],
        "guest_isa": guest_isa,
        "guest_isa_id": ISA_IDS[guest_isa],
        "compatibility_personality": compatibility,
        "compatibility_target_mask": COMPATIBILITY_MASKS.get(compatibility, 0) if backend == "compatibility" else 0,
        "physical_native_width_is_hardware_defined": True,
        "arbitrary_width_virtual_abi": True,
        "validation_required_at_kernel_admission": True,
        "isa_catalog_does_not_imply_executable_backend": True
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bits", type=int, help="selected process width, any positive integer up to 4294967295")
    parser.add_argument("--backend", choices=sorted(BACKENDS), default="auto")
    parser.add_argument("--compatibility", choices=sorted(COMPATIBILITY))
    parser.add_argument("--isa", choices=sorted(ISA_TARGETS), default="auto",
                        help="guest ISA target; catalog presence does not imply executable translation support")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--show", action="store_true", help="show current selection")
    args = parser.parse_args()
    if args.show and args.bits is None:
        if not args.config.exists():
            print(json.dumps({"schema": "CHIMERA-NBIT-USER-PROFILE-1",
                              "selected_width_bits": 64, "backend": "auto", "backend_id": 0,
                              "guest_isa": "auto", "guest_isa_id": 0,
                              "compatibility_target_mask": 0}, indent=2))
            return 0
        print(args.config.read_text(encoding="utf-8"))
        return 0
    if args.bits is None:
        try:
            raw = input("Choose Chimera N-bit width (any positive integer, default 64): ").strip()
            bits = int(raw or "64", 10)
            backend = input("Backend [auto/chimera-virtual/physical-native/compatibility] (default auto): ").strip() or "auto"
            isa = input("Guest ISA [auto/chimera-nbit/x86-64/aarch64/riscv64/...](default auto): ").strip() or "auto"
            compatibility = None
            if backend == "compatibility":
                compatibility = input("Compatibility [native/windows/linux/bsd/darwin/android/ios]: ").strip().lower()
        except (EOFError, ValueError):
            parser.error("interactive selection failed; pass --bits and --backend")
    else:
        bits, backend, compatibility, isa = args.bits, args.backend, args.compatibility, args.isa
    try:
        profile = build_profile(bits, backend, compatibility, isa)
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
