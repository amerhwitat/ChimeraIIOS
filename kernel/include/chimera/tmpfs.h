#pragma once
#include "chimera/ramfs.h"
#include "chimera/vfs.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct chimera_tmpfs chimera_tmpfs;
typedef struct chimera_tmpfs_limits {
    uint32_t max_entries;
    uint32_t max_path_bytes;
    uint64_t max_file_bytes;
    uint64_t max_total_bytes;
} chimera_tmpfs_limits;

/* Mutable RAM filesystem. Writes and truncates use copy-then-commit allocation:
   allocation/limit failure leaves the previous file contents unchanged. */
int chimera_tmpfs_create(const chimera_ramfs_allocator *allocator,
                         const chimera_tmpfs_limits *limits,
                         chimera_tmpfs **out);
void chimera_tmpfs_destroy(chimera_tmpfs *fs);
const chimera_vfs_ops *chimera_tmpfs_vfs_ops(void);

#ifdef __cplusplus
}
#endif
