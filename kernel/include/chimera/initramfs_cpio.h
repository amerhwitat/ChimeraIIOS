#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_CPIO_ABI 1u
#define CHIMERA_CPIO_MAX_ARCHIVE_BYTES (64u * 1024u * 1024u)
#define CHIMERA_CPIO_MAX_ENTRIES 4096u
#define CHIMERA_CPIO_MAX_PATH 255u
typedef enum chimera_cpio_status {
  CHIMERA_CPIO_OK=0, CHIMERA_CPIO_E_ARGUMENT=-1, CHIMERA_CPIO_E_LIMIT=-2,
  CHIMERA_CPIO_E_HEADER=-3, CHIMERA_CPIO_E_BOUNDS=-4, CHIMERA_CPIO_E_PATH=-5,
  CHIMERA_CPIO_E_TYPE=-6, CHIMERA_CPIO_E_CHECKSUM=-7, CHIMERA_CPIO_E_TRAILER=-8,
  CHIMERA_CPIO_E_COMPRESSION=-9
} chimera_cpio_status;
typedef struct chimera_cpio_summary {
  uint32_t entries;
  uint32_t regular_files;
  uint32_t directories;
  uint64_t payload_bytes;
  uint64_t archive_bytes;
  uint32_t has_init;
} chimera_cpio_summary;
/* Validate a raw newc/crc CPIO archive without allocating or extracting it.
   Compressed archives are rejected explicitly; callers must decompress with a
   separately bounded decoder before calling this function. */
int chimera_cpio_validate_newc(const void *archive, uint64_t archive_size,
                               chimera_cpio_summary *summary);
#ifdef __cplusplus
}
#endif
