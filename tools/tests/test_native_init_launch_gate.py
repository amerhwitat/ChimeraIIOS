#!/usr/bin/env python3
"""Regression guard for fail-closed native init ELF dispatch.

This source-contract test prevents production payloads from being reported as
successfully handled when no native USER_INIT_ELF module is supplied. It is
not a runtime boot test and does not establish production readiness.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
LAUNCH = ROOT / "kernel/core/target_launch.cpp"
BOOTSTRAP = ROOT / "kernel/core/koronos.cpp"


def fail(message: str) -> int:
    print(f"NATIVE INIT LAUNCH GATE FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    launch = LAUNCH.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    native_init_path = ROOT / "kernel/userspace/native_init.c"
    if not native_init_path.is_file():
        return fail("native init bootstrap source is missing")
    native_init = native_init_path.read_text(encoding="utf-8")
    if "call0(2)" not in native_init or "NATIVE INIT PID: target=" not in native_init:
        return fail("native init must report the actual GETPID syscall result")
    if "USERSPACE READY:" in native_init:
        return fail("fail-closed bootstrap must not fabricate readiness")

    service_source = (ROOT / "kernel/core/service.cpp").read_text(encoding="utf-8")
    if 'chimera_service_set_state("chimera.storage",CHM_SVC_RUNNING)' in service_source:
        return fail("service registry must not mark storage RUNNING without an implementation health check")
    if 'chimera_service_set_state("chimera.device",CHM_SVC_RUNNING)' in service_source:
        return fail("service registry must not mark device services RUNNING without an implementation health check")
    if "Registration is not a health check" not in service_source:
        return fail("service readiness versus registry initialization contract is missing")

    syscall_header = (ROOT / "kernel/include/chimera/syscall.h").read_text(encoding="utf-8")
    mmap_id = re.search(r"CHM_SYS_MMAP\s*=\s*(\d+)", syscall_header)
    if not mmap_id or int(mmap_id.group(1)) != 10:
        return fail("native syscall ABI no longer identifies syscall 10 as MMAP; review ABI changes explicitly")
    if "CHM_SYS_MOUNT" in syscall_header:
        return fail("mount syscall was added; require an implementation and runtime tests before changing fail-closed init")
    if re.search(r"call[0-6]\(10\)", native_init):
        return fail("native init must not treat syscall 10 (MMAP) as a mount operation")
    if "call1(1, 78)" not in native_init or "NATIVE INIT BLOCKED:" not in native_init:
        return fail("bootstrap must retain its explicit unavailable-service exit")

    archive_guard = launch.split(
        "if (payload_count==1u && (target==TARGET_LIVE || target==TARGET_RECOVERY))", 1
    )
    if len(archive_guard) != 2:
        return fail("missing Live/Recovery rootfs archive validation block")
    archive_guard = archive_guard[1].split("if (!koronos_address_space_ready())", 1)[0]
    if "summary.has_init" in archive_guard:
        return fail("rootfs archive validation must not require executable /init when a separately staged target-matched native ELF is the entry point")
    if "cpio_rc != CHIMERA_CPIO_OK" not in archive_guard:
        return fail("Live/Recovery rootfs must still fail closed on invalid CPIO")
    if "separately staged" not in archive_guard:
        return fail("rootfs/entry-point separation rationale and regression guard are missing")

    if '#include "chimera/ramfs.h"' not in launch or "chimera_ramfs_extract_newc" not in (ROOT / "kernel/core/ramfs.cpp").read_text(encoding="utf-8"):
        return fail("production launch must compile against the bounded transactional RAMFS extractor")
    if "stage_rootfs(archive_bytes, archive->size)" not in launch:
        return fail("raw CPIO path must stage a complete unpublished RAMFS tree")
    if "stage_rootfs(" not in launch or "decoded_size" not in launch:
        return fail("gzip CPIO path must stage the decoded archive into RAMFS")
    if "Rootfs archive extracted into bounded unpublished RAMFS staging tree" not in launch:
        return fail("the archive must be fully extracted before publication")
    if "transactional RAMFS staging failed; no rootfs was published" not in launch:
        return fail("RAMFS extraction errors must fail closed before userspace dispatch")
    if "__atomic_store_n(&published_rootfs, staged_rootfs, __ATOMIC_RELEASE)" not in launch:
        return fail("complete RAMFS tree must be atomically published only after successful extraction")
    for operation in ("koronos_target_fs_open", "koronos_target_fs_read", "koronos_target_fs_close"):
        if operation not in launch:
            return fail(f"process-bound read-only filesystem operation missing: {operation}")
    if "koronos_address_space_validate_user_range(active_root" not in launch:
        return fail("filesystem syscalls must validate user buffers against the active process address space")
    if "if (flags != 0u) return -22" not in launch:
        return fail("open must remain read-only until transactional RAMFS writes exist")
    syscall_source = (ROOT / "kernel/core/syscall.cpp").read_text(encoding="utf-8")
    for syscall in ("case CHM_SYS_OPEN:", "case CHM_SYS_READ:", "case CHM_SYS_CLOSE:"):
        if syscall not in syscall_source:
            return fail(f"native dispatcher missing filesystem syscall route: {syscall}")

    ramfs_source = (ROOT / "kernel/core/ramfs.cpp").read_text(encoding="utf-8")
    if "Normalize only" not in ramfs_source or "normalized_name[0]=='.'&&normalized_name[1]=='/'" not in ramfs_source:
        return fail("RAMFS must normalize common leading ./ paths from relative newc archives")
    if "absolute paths and interior dot/dot-dot" not in ramfs_source:
        return fail("RAMFS path normalization must preserve traversal rejection")

    if "if (count==0)" not in launch:
        return fail("missing explicit zero-USER_INIT_ELF branch")
    zero_branch = launch.split("if (count==0)", 1)[1].split(
        "if (count!=1", 1
    )[0]
    for required in (
        "CHIMERA_MODULE_LIVE_INITRAMFS",
        "CHIMERA_MODULE_RECOVERY_INITRAMFS",
        "CHIMERA_MODULE_INSTALL_IMAGE",
        "if (!has_target_payload) return 0;",
        "no USER_INIT_ELF module was supplied",
        "return -12;",
    ):
        if required not in zero_branch:
            return fail(f"zero-module production failure contract missing: {required}")

    for target, marker in (
        ("live", "CHIMERA_MODULE_LIVE_INITRAMFS"),
        ("recovery", "CHIMERA_MODULE_RECOVERY_INITRAMFS"),
        ("installer", "CHIMERA_MODULE_INSTALL_IMAGE"),
    ):
        if marker not in bootstrap:
            return fail(f"{target} payload recognition is missing")
        diagnostic = target.capitalize() + " target init failed before readiness"
        if diagnostic not in bootstrap:
            return fail(f"{target} missing-init failure diagnostic is missing")

    build_path = ROOT / "kernel/build-koronos.sh"
    build = build_path.read_text(encoding="utf-8")
    if "user-init-${target}.elf" in build and not ("acceptance probes" in build and "not production shells" in build):
        return fail("smoke probe artifacts are not explicitly isolated from production")

    print("NATIVE INIT LAUNCH GATE PASS: missing ELF fails closed; mount ABI is not faked; probes remain isolated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
