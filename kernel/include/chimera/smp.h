#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* Real-AP startup gate. The BSP sends INIT/SIPI, starts the secondary CPU in
 * long mode on its own stack, and measures simultaneous round progress from
 * both CPUs before parking the AP. */
int koronos_smp_selftest(void);
uint32_t koronos_smp_ap_online(void);
uint32_t koronos_smp_overlap_samples(void);

#ifdef __cplusplus
}
#endif
