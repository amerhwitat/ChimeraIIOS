#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* Native block/VFS/PID 1 acceptance stack.
 *
 * The block backend is a real legacy virtio-blk PCI device driven through
 * virtqueue descriptors. The mount layer validates an on-disk superblock, and
 * the supervisor table tracks PID 1, its child, exit status, and reaping. */
int koronos_native_stack_selftest(void);
uint32_t koronos_native_stack_block_sectors(void);
uint32_t koronos_native_stack_mounted(void);
uint32_t koronos_native_stack_reaped_pid(void);
uint32_t koronos_native_stack_reaped_status(void);
uint32_t koronos_native_stack_zombies_after_reap(void);

#ifdef __cplusplus
}
#endif
