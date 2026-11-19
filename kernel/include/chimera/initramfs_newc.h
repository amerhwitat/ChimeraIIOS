#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_NEWC_ABI 1u
#define KORONOS_NEWC_MAX_NAME 4096u
#define KORONOS_NEWC_TYPE_MASK 0170000u
#define KORONOS_NEWC_REG 0100000u
#define KORONOS_NEWC_DIR 0040000u
#define KORONOS_NEWC_SYMLINK 0120000u

typedef struct koronos_newc_entry {
    const char *name;
    const uint8_t *data;
    uint32_t name_size;
    uint32_t mode;
    uint32_t uid;
    uint32_t gid;
    uint32_t links;
    uint32_t mtime;
    uint32_t file_size;
    uint32_t device_major;
    uint32_t device_minor;
} koronos_newc_entry;

typedef int (*koronos_newc_visit_fn)(void *context, const koronos_newc_entry *entry);

typedef struct koronos_newc_result {
    uint32_t entries;
    uint32_t regular_files;
    uint32_t directories;
    uint32_t symlinks;
    uint64_t payload_bytes;
    uint64_t archive_bytes;
} koronos_newc_result;

/* Walks a bounded SVR4 newc archive without allocating memory. Rejects
   malformed headers, path traversal, truncated payloads and bad CRC archives.
   The visitor must copy any data it needs after the callback returns. */
int koronos_newc_walk(const void *archive, uint64_t archive_size,
                      koronos_newc_visit_fn visitor, void *context,
                      koronos_newc_result *result);

#ifdef __cplusplus
}
#endif
