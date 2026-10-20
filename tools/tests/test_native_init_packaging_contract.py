#!/usr/bin/env python3
"""Guard the target-specific native-init ELF packaging and GRUB dispatch contract.

The current native init is deliberately fail-closed while service backends are
missing. This test verifies packaging/dispatch only; it does not assert that
userspace is ready or that production acceptance passed.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> int:
    print(f"NATIVE INIT PACKAGING CONTRACT FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    builder = ROOT / "tools/build-production-init-elfs.sh"
    source = ROOT / "kernel/userspace/native_init.c"
    linker = ROOT / "kernel/userspace/native_init.ld"
    prepare = ROOT / "boot/iso/prepare-layout.sh"
    grub = ROOT / "boot/iso/grub.cfg"
    live_cfg = ROOT / "boot/jasper/live.cfg"
    recovery_cfg = ROOT / "boot/jasper/recovery.cfg"
    install_cfg = ROOT / "boot/jasper/install.cfg"
    launch = ROOT / "kernel/core/target_launch.cpp"

    for path in (builder, source, linker, prepare, grub, live_cfg, recovery_cfg, install_cfg, launch):
        if not path.is_file():
            return fail(f"required source/config missing: {path.relative_to(ROOT)}")

    build_text = builder.read_text(encoding="utf-8")
    init_text = source.read_text(encoding="utf-8")
    prepare_text = prepare.read_text(encoding="utf-8")
    grub_text = grub.read_text(encoding="utf-8")
    live_text = live_cfg.read_text(encoding="utf-8")
    recovery_text = recovery_cfg.read_text(encoding="utf-8")
    install_text = install_cfg.read_text(encoding="utf-8")
    launch_text = launch.read_text(encoding="utf-8")

    routes = (
        ("live", "boot/live/user-init-live.elf", "/boot/live/user-init-live.elf", live_text),
        ("installer", "boot/installer/user-init-installer.elf", "/boot/installer/user-init-installer.elf", install_text),
        ("recovery", "boot/recovery/user-init-recovery.elf", "/boot/recovery/user-init-recovery.elf", recovery_text),
    )
    for target, staged_path, grub_path, jasper_text in routes:
        module = f"module2 {grub_path} chimera-user-init-elf target={target}"
        if staged_path not in build_text:
            return fail(f"builder does not stage {staged_path}")
        if module not in grub_text:
            return fail(f"canonical GRUB does not dispatch the matching {target} ELF")
        if module not in jasper_text:
            return fail(f"Jasper {target} route does not dispatch its matching ELF")

    if "payload_count != 1" not in launch_text or "elf_count != 1" not in launch_text:
        return fail("kernel launch must require exactly one production payload and one native init ELF")
    if "if (elf_target != target)" not in launch_text:
        return fail("kernel launch must reject a target-mismatched init ELF")
    if 'bash "$ROOT/tools/build-production-init-elfs.sh"' not in prepare_text:
        return fail("ISO preparation does not invoke target init ELF builder")
    if "chimera-user-init-elf target=live" not in live_text:
        return fail("Jasper Live config does not dispatch the Live init ELF")
    if "chimera-user-init-elf target=recovery" not in recovery_text:
        return fail("Jasper Recovery config does not dispatch the Recovery init ELF")
    if "chimera-user-init-elf target=installer" not in install_text:
        return fail("Jasper Installer config does not dispatch the Installer init ELF")

    if "call0(2)" not in init_text or "NATIVE INIT PID: target=" not in init_text:
        return fail("init must report the actual GETPID syscall result")
    if "NATIVE INIT BLOCKED:" not in init_text:
        return fail("init must report unavailable services honestly")
    if "USERSPACE READY:" in init_text:
        return fail("init must not fabricate a readiness marker before services exist")

    print("NATIVE INIT PACKAGING CONTRACT PASS: target ELFs built/staged and routed; readiness remains fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
