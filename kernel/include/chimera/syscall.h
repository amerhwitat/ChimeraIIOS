#ifndef CHIMERA_SYSCALL_H
#define CHIMERA_SYSCALL_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_SYSCALL_ABI 1u
#define CHIMERA_SYSCALL_MAX_ARGS 6u
#define CHIMERA_ENOSYS 38u

/* Stable Chimera semantic syscall IDs. Compatibility ABIs translate into
 * these IDs rather than importing another OS's unstable internal table. */
enum chimera_native_syscall {
    CHM_SYS_EXIT = 1,
    CHM_SYS_GETPID = 2,
    CHM_SYS_YIELD = 3,
    CHM_SYS_TIME_TICKS = 4,
    CHM_SYS_READ = 8,
    CHM_SYS_WRITE = 9,
    CHM_SYS_MMAP = 10,
    CHM_SYS_MUNMAP = 11,
    CHM_SYS_IOCTL = 12,
    CHM_SYS_NANOSLEEP = 13,
    CHM_SYS_WAIT = 14,
    CHM_SYS_ARCH_PRCTL = 15,
    CHM_SYS_EXIT_GROUP = 16
};

typedef struct chimera_syscall_frame {
    uint64_t number;
    uint64_t args[CHIMERA_SYSCALL_MAX_ARGS];
    uint64_t return_value;
    uint32_t source_os;
    uint32_t source_entry;
    uint32_t source_bitness;
    uint32_t flags;
} chimera_syscall_frame;

typedef struct chimera_syscall_snapshot {
    uint32_t abi;
    uint32_t initialized;
    uint32_t dispatched;
    uint32_t translated;
    uint32_t rejected;
    uint32_t last_os;
    uint32_t last_entry;
    uint32_t last_number;
    uint32_t last_canonical;
} chimera_syscall_snapshot;

int chimera_syscall_init(void);
int chimera_syscall_dispatch(uint32_t entry, uint32_t bitness, uint32_t number,
                             const uint64_t *args, uint64_t *return_value);
int chimera_syscall_get_snapshot(chimera_syscall_snapshot *out);

#ifdef __cplusplus
}
#endif

#endif
