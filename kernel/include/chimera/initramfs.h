#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_INITRAMFS_ABI 0x00010000u
#define CHIMERA_INITRAMFS_PATH_MAX 255u
#define CHIMERA_INITRAMFS_MAX_ENTRIES 4096u

enum chimera_initramfs_entry_type {
    CHM_INITRAMFS_REGULAR = 1,
    CHM_INITRAMFS_DIRECTORY = 2,
    CHM_INITRAMFS_SYMLINK = 3
};

struct chimera_initramfs_entry {
    const char* path;             /* normalized relative path; empty for root */
    const uint8_t* data;          /* points into the immutable archive */
    uint32_t path_length;
    uint32_t size;
    uint32_t mode;
    uint32_t inode;
    uint32_t type;
};

struct chimera_initramfs_report {
    uint32_t entries;
    uint32_t regular_files;
    uint32_t directories;
    uint32_t symlinks;
    uint64_t payload_bytes;
};

typedef int (*chimera_initramfs_visit_fn)(
    const struct chimera_initramfs_entry* entry, void* context);

/* Validates a complete uncompressed CPIO-newc archive before invoking visitor.
 * Rejects malformed/truncated headers, path traversal, duplicate normalized
 * paths, unsupported file types, bad CRC archives, and missing trailers.
 * Visitor paths are valid only for the duration of the callback. */
int chimera_initramfs_scan(const void* archive, uint64_t archive_size,
                           chimera_initramfs_visit_fn visitor, void* context,
                           struct chimera_initramfs_report* report);

#ifdef __cplusplus
}
#endif
