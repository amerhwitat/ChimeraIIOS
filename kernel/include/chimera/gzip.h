#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Decode one complete RFC 1952 gzip member containing RFC 1951 DEFLATE.
   The caller owns the output buffer. No allocation, exceptions, or libc calls.
   Returns 0 on success; negative values distinguish invalid/truncated input,
   unsupported options, output exhaustion, and integrity-check failures. */
int chimera_gzip_decompress_bounded(const void *input, uint64_t input_size,
                                    void *output, uint64_t output_capacity,
                                    uint64_t *output_size);
#ifdef __cplusplus
}
#endif
