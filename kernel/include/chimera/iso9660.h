#pragma once
#include "chimera/block_device.h"
#include "chimera/vfs.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_ISO9660_ABI 1u
#define CHIMERA_ISO9660_SECTOR_SIZE 2048u

typedef struct chimera_iso9660 chimera_iso9660;

/* Read-only ISO9660 Level 1/2 primary-volume-descriptor backend.
   Rock Ridge, Joliet, multi-extent files and writes are intentionally rejected
   or unsupported until separately implemented and tested. */
int chimera_iso9660_mount(const chimera_block_device *device, chimera_iso9660 **out);
void chimera_iso9660_unmount(chimera_iso9660 *fs);
const chimera_vfs_ops *chimera_iso9660_vfs_ops(void);

#ifdef __cplusplus
}
#endif
