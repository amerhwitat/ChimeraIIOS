#pragma once
#include <stdint.h>
#include "chimera/initramfs_cpio.h"
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_INITRAMFS_MAX_INPUT_BYTES (64ull * 1024ull * 1024ull)
/* Copy raw CPIO or bounded-decompress one gzip member into caller-owned storage,
   then validate the complete CPIO archive. Input/output buffers must not overlap.
   No archive is accepted unless decompression integrity and CPIO validation pass. */
int chimera_initramfs_prepare_newc(const void *input, uint64_t input_size,
                                   void *workspace, uint64_t workspace_capacity,
                                   uint64_t *archive_size,
                                   chimera_cpio_summary *summary);
#ifdef __cplusplus
}
#endif
