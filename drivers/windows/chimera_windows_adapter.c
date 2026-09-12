#include <stdint.h>
#include "../platform/chimera_driver_adapter.h"

/* User/kernel boundary only. A real Windows KMDF/UMDF adapter is implemented
   in a Windows build using the WDK; this file intentionally has no WDK dependency. */
static int chm_windows_probe(uint16_t vendor, uint16_t device) { (void)vendor; (void)device; return 0; }
static int chm_windows_start(void* ctx) { (void)ctx; return 0; }
static int chm_windows_stop(void* ctx) { (void)ctx; return 0; }
static int chm_windows_ioctl(void* ctx, uint32_t request, void* buffer, size_t size) { (void)ctx; (void)request; (void)buffer; (void)size; return -1; }

const chm_driver_ops_t chm_windows_adapter = {
    chm_windows_probe, chm_windows_start, chm_windows_stop, chm_windows_ioctl
};
