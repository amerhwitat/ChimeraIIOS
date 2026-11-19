#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_INITRAMFS_ABI 1u
#define KORONOS_INITRAMFS_MAX_NODES 4096u
#define KORONOS_INITRAMFS_NAME_MAX 63u

typedef struct koronos_initramfs_stat {
    uint32_t mode, uid, gid, type;
    uint64_t size;
} koronos_initramfs_stat;

/* Read-only in-memory namespace backed by the validated newc archive bytes.
   The caller must keep the archive module mapped for the mount lifetime. */
int koronos_initramfs_mount(const void *archive, uint64_t archive_size);
int koronos_initramfs_lookup(const char *path, uint32_t *node_id);
int koronos_initramfs_stat_node(uint32_t node_id, koronos_initramfs_stat *out);
int koronos_initramfs_read(uint32_t node_id, uint64_t offset, void *buffer,
                           uint64_t length, uint64_t *bytes_read);
uint32_t koronos_initramfs_node_count(void);
/* Bounded writable RAM tmpfs: masks archive /tmp contents; files are direct children only. */
int koronos_tmpfs_create(const char *path, uint32_t *node_id);
int koronos_tmpfs_write(uint32_t node_id, uint64_t offset, const void *buffer,
                        uint64_t length, uint64_t *bytes_written);
void koronos_initramfs_unmount(void);

#ifdef __cplusplus
}
#endif
