#ifndef CHIMERA_COMPAT_H
#define CHIMERA_COMPAT_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_COMPAT_ABI 1u
#define CHIMERA_COMPAT_MAX 10u
#define CHIMERA_COMPAT_MAX_SYSCALLS 96u

typedef enum chimera_compat_os {
    CHM_OS_NATIVE = 0,
    CHM_OS_LINUX = 1,
    CHM_OS_WINDOWS_NT = 2,
    CHM_OS_WINDOWS_9X = 3,
    CHM_OS_DOS = 4,
    CHM_OS_DARWIN = 5,
    CHM_OS_MACH = 6,
    CHM_OS_BSD = 7,
    CHM_OS_ANDROID = 8,
    CHM_OS_IOS = 9
} chimera_compat_os;

typedef enum chimera_entry_kind {
    CHM_ENTRY_NATIVE = 0,
    CHM_ENTRY_X86_SYSCALL = 1,
    CHM_ENTRY_X86_SYSENTER = 2,
    CHM_ENTRY_X86_INT80 = 3,
    CHM_ENTRY_X86_INT2E = 4,
    CHM_ENTRY_X86_INT21 = 5,
    CHM_ENTRY_MACH_TRAP = 6,
    CHM_ENTRY_BSD_SYSCALL = 7
} chimera_entry_kind;

typedef enum chimera_memory_model {
    CHM_MEM_NATIVE = 0,
    CHM_MEM_32BIT_USER_KERNEL = 1,
    CHM_MEM_64BIT_USER_KERNEL = 2,
    CHM_MEM_PAE_COMPAT = 3,
    CHM_MEM_DOS_REAL_MODE = 4,
    CHM_MEM_DOS_PROTECTED_MODE = 5,
    CHM_MEM_WIN9X_VMM = 6
} chimera_memory_model;

enum chimera_compat_flags {
    CHM_COMPAT_USERSPACE = 1u << 0,
    CHM_COMPAT_KERNELSPACE = 1u << 1,
    CHM_COMPAT_32BIT = 1u << 2,
    CHM_COMPAT_64BIT = 1u << 3,
    CHM_COMPAT_POINTER_TRANSLATION = 1u << 4,
    CHM_COMPAT_MEMORY_MAP = 1u << 5,
    CHM_COMPAT_HAL_TRANSLATION = 1u << 6,
    CHM_COMPAT_DRIVER_TRANSLATION = 1u << 7,
    CHM_COMPAT_SYSCALL_TRANSLATION = 1u << 8,
    CHM_COMPAT_INTERRUPT_TRANSLATION = 1u << 9,
    CHM_COMPAT_EMULATION_REQUIRED = 1u << 10
};

typedef struct chimera_compat_profile {
    uint32_t os;
    uint32_t version_major;
    uint32_t version_minor;
    uint32_t architecture_mask;
    uint32_t entry_mask;
    uint32_t memory_model;
    uint32_t flags;
    uint64_t user_low;
    uint64_t user_high;
    uint64_t kernel_low;
    uint64_t kernel_high;
    uint64_t hal_abi;
    uint64_t driver_abi;
    const char *name;
} chimera_compat_profile;

typedef struct chimera_syscall_identity {
    uint32_t os;
    uint32_t entry;
    uint32_t bitness;
    uint32_t number;
    uint32_t canonical;
    uint32_t flags;
} chimera_syscall_identity;

typedef struct chimera_interrupt_identity {
    uint32_t os;
    uint32_t vector;
    uint32_t entry;
    uint32_t flags;
} chimera_interrupt_identity;

typedef struct chimera_compat_snapshot {
    uint32_t abi;
    uint32_t profile_count;
    uint32_t syscall_count;
    uint32_t interrupt_count;
    uint32_t initialized;
    uint32_t current_arch;
    uint32_t current_bitness;
    uint64_t supported_os_mask;
} chimera_compat_snapshot;

int chimera_compat_init(uint32_t architecture, uint32_t bitness);
int chimera_compat_probe(void);
int chimera_compat_get_snapshot(chimera_compat_snapshot *out);
const chimera_compat_profile *chimera_compat_profile_at(uint32_t index);
int chimera_compat_recognize_syscall(uint32_t entry, uint32_t bitness, uint32_t number, chimera_syscall_identity *out);
int chimera_compat_recognize_interrupt(uint32_t vector, chimera_interrupt_identity *out);
int chimera_compat_memory_profile(uint32_t os, chimera_memory_model *model, uint64_t *user_high, uint64_t *kernel_low);
int chimera_compat_hal_profile(uint32_t os, uint64_t *hal_abi, uint64_t *driver_abi);
const char *chimera_compat_os_name(uint32_t os);
const char *chimera_compat_entry_name(uint32_t entry);

#ifdef __cplusplus
}
#endif

#endif
