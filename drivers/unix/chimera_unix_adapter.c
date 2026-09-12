#include <stdint.h>
#include "../platform/chimera_driver_adapter.h"

static int chm_unix_probe(uint16_t vendor, uint16_t device) { (void)vendor; (void)device; return 0; }
static int chm_unix_start(void* ctx) { (void)ctx; return 0; }
static int chm_unix_stop(void* ctx) { (void)ctx; return 0; }
static int chm_unix_ioctl(void* ctx, uint32_t request, void* buffer, size_t size) { (void)ctx; (void)request; (void)buffer; (void)size; return -1; }

const chm_driver_ops_t chm_unix_adapter = {
    chm_unix_probe, chm_unix_start, chm_unix_stop, chm_unix_ioctl
};
