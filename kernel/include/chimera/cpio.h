#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_CPIO_ABI 1u
#define CHIMERA_CPIO_PATH_MAX 256u
typedef struct chimera_cpio_entry {
    const uint8_t* data;
    uint32_t size;
    uint32_t mode;
    uint32_t uid;
    uint32_t gid;
} chimera_cpio_entry;
/* Bounded newc (070701/070702) exact relative-path lookup.
 * 0=found, -1=malformed input, -2=not found before TRAILER!!!.
 * The entry data remains owned by the caller's archive buffer. */
int chimera_cpio_find(const void* archive, uint64_t archive_size,
                      const char* path, chimera_cpio_entry* out);
#ifdef __cplusplus
}
#endif
