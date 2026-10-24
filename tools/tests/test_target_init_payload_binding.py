#!/usr/bin/env python3
"""Regression guard for binding a native init ELF to its production payload.

This is a source-contract test only. It does not replace the six-case ISO
acceptance matrix or prove that the selected target is operational.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / "kernel/core/target_launch.cpp").read_text(encoding="utf-8")
required = (
    "uint32_t payload_count=0;",
    "Target payload_target=TARGET_NONE;",
    "case CHIMERA_MODULE_LIVE_INITRAMFS:",
    "case CHIMERA_MODULE_INSTALL_IMAGE:",
    "case CHIMERA_MODULE_RECOVERY_INITRAMFS:",
    "if (payload_count>1u)",
    "if (payload_count==1u && payload_target!=target)",
    "native init target does not match the selected production payload",
    "stage_rootfs(archive_bytes, archive->size)",
    "chimera_vfs_mount(\"/\", &ramfs_vfs_ops, staged_rootfs, CHIMERA_VFS_MOUNT_RDONLY)",
    "chimera_vfs_mount(\"/tmp\", chimera_tmpfs_vfs_ops(), tmpfs_candidate, 0u)",
    "transactional RAMFS staging failed; no rootfs was published",
    "VFS root mount failed; refusing userspace launch",
    "bounded writable /tmp filesystem mount failed; refusing userspace launch",
    "__atomic_store_n(&published_rootfs, staged_rootfs, __ATOMIC_RELEASE)",
    "if (!staged_rootfs_ready || !staged_rootfs)",
    "static void discard_staged_rootfs()",
    "discard_staged_rootfs();",
    "CHIMERA_MODULE_USER_INIT_ELF",
    "const void *init_image = reinterpret_cast<const void *>(static_cast<uintptr_t>(selected->base));",
    "const uint64_t init_image_size = selected->size;",
    "chimera_process_admit_elf(init_image, init_image_size",
    "chimera_elf_load_user_image(init_image, init_image_size",
)
missing = [part for part in required if part not in source]
if missing:
    raise SystemExit("native init payload-binding contract missing: " + "; ".join(missing))
# The root pointer must not become visible until both mounts succeeded.
root_mount = source.find('chimera_vfs_mount("/", &ramfs_vfs_ops, staged_rootfs, CHIMERA_VFS_MOUNT_RDONLY)')
tmp_mount = source.find('chimera_vfs_mount("/tmp", chimera_tmpfs_vfs_ops(), tmpfs_candidate, 0u)')
publish_root = source.find("__atomic_store_n(&published_rootfs, staged_rootfs, __ATOMIC_RELEASE)")
if min(root_mount, tmp_mount, publish_root) < 0 or not (root_mount < publish_root and tmp_mount < publish_root):
    raise SystemExit("rootfs publication must follow successful root and /tmp mounts")
# Failed publication must reclaim the unpublished rootfs. For the /tmp
# failure, unmount the root before freeing its backing RAMFS tree.
root_fail = source.find('VFS root mount failed; refusing userspace launch')
root_fail_cleanup = source.rfind('discard_staged_rootfs();', 0, root_fail)
tmp_fail = source.find('bounded writable /tmp filesystem mount failed; refusing userspace launch')
tmp_fail_cleanup = source.rfind('discard_staged_rootfs();', 0, tmp_fail)
tmp_unmount = source.rfind('chimera_vfs_unmount("/")', 0, tmp_fail)
if min(root_fail, root_fail_cleanup, tmp_fail, tmp_fail_cleanup, tmp_unmount) < 0:
    raise SystemExit("VFS publication failure must reclaim staged RAMFS")
if not (root_fail_cleanup < root_fail and tmp_unmount < tmp_fail_cleanup < tmp_fail):
    raise SystemExit("rootfs cleanup must follow unmount and precede failure return")
for forbidden in (
    "stage_archive_init_elf",
    "staged_archive_init",
    'chimera_cpio_lookup_executable_newc(archive, archive_size, "/init", &entry)',
    "interpreter/argv exec and script FD support are not implemented",
):
    if forbidden in source:
        raise SystemExit("archive /init must not override the tagged native ELF: " + forbidden)
if "production root filesystem is not mounted" in source:
    raise SystemExit("stale rootfs-not-mounted source contract remains; use the current fail-closed mount path")
print("native init payload-binding contract: PASS (tagged native ELF selected; source-level only)")
