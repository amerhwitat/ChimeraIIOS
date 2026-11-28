#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

enum koronos_gate_result { KORONOS_GATE_FAILED = -1, KORONOS_GATE_PASS = 0, KORONOS_GATE_SKIPPED = 1 };

/* Native block/VFS/PID 1 acceptance stack.
 *
 * The block backend is a real legacy virtio-blk PCI device driven through
 * virtqueue descriptors. The mount layer validates an on-disk superblock, and
 * the supervisor table tracks PID 1, its child, exit status, and reaping. */
int koronos_native_stack_selftest(void);
int koronos_install_recovery_selftest(void);
int koronos_native_block_init(void);
int koronos_native_block_read(uint32_t sector, uint8_t *buffer);
int koronos_native_block_write(uint32_t sector, const uint8_t *buffer);
void koronos_native_machine_reset(void);
uint32_t koronos_native_stack_block_sectors(void);
uint32_t koronos_native_stack_mounted(void);
uint32_t koronos_native_stack_reaped_pid(void);
uint32_t koronos_native_stack_reaped_status(void);
uint32_t koronos_native_stack_zombies_after_reap(void);

#ifdef __cplusplus
}
#endif
