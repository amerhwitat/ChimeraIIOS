#include <stdint.h>
#include "../platform/chimera_driver_adapter.h"

/* Portable Linux adapter boundary. Native kernel integration belongs in a
   GPL-compatible kernel module or user-space subsystem adapter built against
   the target kernel/API; this file contains no copied kernel source. */
static int chm_linux_probe(uint16_t vendor, uint16_t device) { (void)vendor; (void)device; return 0; }
static int chm_linux_start(void* ctx) { (void)ctx; return 0; }
static int chm_linux_stop(void* ctx) { (void)ctx; return 0; }
static int chm_linux_ioctl(void* ctx, uint32_t request, void* buffer, size_t size) { (void)ctx; (void)request; (void)buffer; (void)size; return -1; }

const chm_driver_ops_t chm_linux_adapter = {
    chm_linux_probe, chm_linux_start, chm_linux_stop, chm_linux_ioctl
};
