#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_CPIO_NEWC_ABI 0x00010000u
#define CHIMERA_CPIO_NEWC_MAX_NAME 4096u

typedef struct chimera_cpio_newc_ops {
    /*
     * Called once for each non-trailer entry. The path is normalized to omit
     * a leading "./". The path/data pointers refer to the archive and remain
     * valid only for the duration of this callback.
     *
     * The VFS publisher must reject duplicate paths, enforce parent-directory
     * policy, and validate symlink targets before publishing the entry.
     */
    int (*entry)(void *context, const char *path, uint32_t mode,
                 uint32_t uid, uint32_t gid, const void *data,
                 uint32_t data_size);
} chimera_cpio_newc_ops;

typedef struct chimera_cpio_newc_summary {
    uint32_t abi;
    uint32_t entries;
    uint32_t regular_files;
    uint32_t directories;
    uint32_t symlinks;
    uint64_t data_bytes;
} chimera_cpio_newc_summary;

/*
 * Walk one bounded CPIO newc archive without allocation or writes.
 * Supports regular files, directories and symlinks only. Device nodes,
 * FIFOs and sockets are refused; devices belong to devtmpfs/driver policy.
 * Accepts 070701 and checksum-verified 070702, requires TRAILER!!!, and
 * permits only zero padding after the trailer.
 */
int chimera_cpio_newc_walk(const void *archive, uint64_t archive_size,
                           const chimera_cpio_newc_ops *ops, void *context,
                           chimera_cpio_newc_summary *summary);

#ifdef __cplusplus
}
#endif
