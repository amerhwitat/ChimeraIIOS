#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_SWAP_ABI 1u
#define KORONOS_SWAP_PAGE_SIZE 4096u
#define KORONOS_SWAP_MAX_SLOTS 4096u
#define KORONOS_SWAP_SLOT_INVALID UINT32_MAX

typedef int (*koronos_swap_read_fn)(void *context, uint64_t offset, void *buffer, uint32_t length);
typedef int (*koronos_swap_write_fn)(void *context, uint64_t offset, const void *buffer, uint32_t length);

typedef struct koronos_swap_backend {
    uint32_t abi;
    uint32_t page_size;
    uint64_t capacity_bytes;
    koronos_swap_read_fn read;
    koronos_swap_write_fn write;
    void *context;
} koronos_swap_backend;

typedef struct koronos_swap_snapshot {
    uint32_t abi;
    uint32_t initialized;
    uint32_t slot_count;
    uint32_t used_slots;
    uint32_t page_size;
    uint32_t reserved;
    uint64_t capacity_bytes;
    uint64_t writes;
    uint64_t reads;
    uint64_t checksum_failures;
    uint64_t io_failures;
} koronos_swap_snapshot;

/* Swap is disabled until a validated block/file backend is supplied. Backend
   callbacks must perform exact-length I/O and must not call back into swap. */
int koronos_swap_init(const koronos_swap_backend *backend);
int koronos_swap_store(const void *page, uint32_t *slot_out);
int koronos_swap_load(uint32_t slot, void *page_out);
int koronos_swap_release(uint32_t slot);
int koronos_swap_get_snapshot(koronos_swap_snapshot *out);
int koronos_swap_self_test(void);

#ifdef __cplusplus
}
#endif
