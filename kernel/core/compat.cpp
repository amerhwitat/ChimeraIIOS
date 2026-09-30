#include "chimera/compat.h"

namespace {

static chimera_compat_profile g_profiles[CHIMERA_COMPAT_MAX];
static uint32_t g_profile_count = 0;
static uint32_t g_initialized = 0;
static uint32_t g_arch = 0;
static uint32_t g_bits = 0;
static uint32_t g_syscalls = 0;
static uint32_t g_interrupts = 0;

static void add_profile(uint32_t os, uint32_t major, uint32_t minor,
                        uint32_t arch, uint32_t entry, uint32_t mem,
                        uint32_t flags, uint64_t user_low, uint64_t user_high,
                        uint64_t kernel_low, uint64_t kernel_high,
                        uint64_t hal, uint64_t driver, const char *name) {
    if (g_profile_count >= CHIMERA_COMPAT_MAX) return;
    chimera_compat_profile &p = g_profiles[g_profile_count++];
    p.os = os; p.version_major = major; p.version_minor = minor;
    p.architecture_mask = arch; p.entry_mask = entry; p.memory_model = mem;
    p.flags = flags; p.user_low = user_low; p.user_high = user_high;
    p.kernel_low = kernel_low; p.kernel_high = kernel_high;
    p.hal_abi = hal; p.driver_abi = driver; p.name = name;
}

static const uint64_t USER64 = 0x00007FFFFFFFFFFFULL;
static const uint64_t KERNEL64 = 0xFFFF800000000000ULL;
static const uint64_t USER32 = 0x000000007FFFFFFFULL;
static const uint64_t KERNEL32 = 0x0000000080000000ULL;
static const uint32_t ARCH_X86_64 = 1u;
static const uint32_t ARCH_X86_32 = 4u;
static const uint32_t ARCH_ARM64 = 2u;

static void build_profiles() {
    g_profile_count = 0;
    const uint32_t user64 = CHM_COMPAT_USERSPACE | CHM_COMPAT_KERNELSPACE |
        CHM_COMPAT_64BIT | CHM_COMPAT_MEMORY_MAP | CHM_COMPAT_HAL_TRANSLATION |
        CHM_COMPAT_DRIVER_TRANSLATION | CHM_COMPAT_SYSCALL_TRANSLATION |
        CHM_COMPAT_INTERRUPT_TRANSLATION;
    const uint32_t user32 = CHM_COMPAT_USERSPACE | CHM_COMPAT_KERNELSPACE |
        CHM_COMPAT_32BIT | CHM_COMPAT_POINTER_TRANSLATION | CHM_COMPAT_MEMORY_MAP |
        CHM_COMPAT_HAL_TRANSLATION | CHM_COMPAT_DRIVER_TRANSLATION |
        CHM_COMPAT_SYSCALL_TRANSLATION | CHM_COMPAT_INTERRUPT_TRANSLATION;

    add_profile(CHM_OS_NATIVE, 1, 0, ARCH_X86_64 | ARCH_ARM64,
                1u << CHM_ENTRY_X86_SYSCALL, CHM_MEM_NATIVE, 0, user64,
                0, USER64, KERNEL64, 0x43484D2D48414C31ULL, 0x43484D2D44525631ULL,
                "Chimera Native");
    add_profile(CHM_OS_LINUX, 6, 11, ARCH_X86_64 | ARCH_X86_32 | ARCH_ARM64,
                (1u << CHM_ENTRY_X86_SYSCALL) | (1u << CHM_ENTRY_X86_INT80) |
                (1u << CHM_ENTRY_X86_SYSENTER), CHM_MEM_64BIT_USER_KERNEL, 0, user64,
                0, USER64, KERNEL64, 0x4C4E582D48414C31ULL, 0x4C4E582D44525631ULL,
                "Linux/POSIX");
    add_profile(CHM_OS_WINDOWS_NT, 10, 0, ARCH_X86_64 | ARCH_X86_32 | ARCH_ARM64,
                (1u << CHM_ENTRY_X86_SYSCALL) | (1u << CHM_ENTRY_X86_SYSENTER) |
                (1u << CHM_ENTRY_X86_INT2E), CHM_MEM_64BIT_USER_KERNEL, 0, user64,
                0, USER64, KERNEL64, 0x4E542D48414C2D31ULL, 0x4E542D4452562D31ULL,
                "Windows NT/Win32");
    add_profile(CHM_OS_WINDOWS_9X, 4, 9, ARCH_X86_32,
                (1u << CHM_ENTRY_X86_INT2E) | (1u << CHM_ENTRY_X86_SYSENTER),
                CHM_MEM_WIN9X_VMM, 0, user32,
                0, USER32, KERNEL32, 0x57394E482D564D4DULL, 0x57394E442D445256ULL,
                "Windows 9x/Me");
    add_profile(CHM_OS_DOS, 6, 22, ARCH_X86_32,
                (1u << CHM_ENTRY_X86_INT21), CHM_MEM_DOS_REAL_MODE,
                CHM_COMPAT_USERSPACE | CHM_COMPAT_32BIT | CHM_COMPAT_INTERRUPT_TRANSLATION |
                CHM_COMPAT_EMULATION_REQUIRED, 0, USER32, 0, KERNEL32,
                0x444F532D48414C31ULL, 0x444F532D44525631ULL, "DOS");
    add_profile(CHM_OS_DARWIN, 23, 0, ARCH_X86_64 | ARCH_X86_32 | ARCH_ARM64,
                (1u << CHM_ENTRY_X86_SYSCALL) | (1u << CHM_ENTRY_X86_INT80),
                CHM_MEM_64BIT_USER_KERNEL, 0, user64,
                0, USER64, KERNEL64, 0x4441522D48414C31ULL, 0x4441522D44525631ULL,
                "Darwin/Unix");
    add_profile(CHM_OS_MACH, 3, 0, ARCH_X86_64 | ARCH_ARM64,
                (1u << CHM_ENTRY_MACH_TRAP) | (1u << CHM_ENTRY_X86_SYSCALL),
                CHM_MEM_64BIT_USER_KERNEL, 0, user64,
                0, USER64, KERNEL64, 0x4D41434848414C31ULL, 0x4D41434844525631ULL,
                "Mach");
    add_profile(CHM_OS_BSD, 1, 0, ARCH_X86_64 | ARCH_X86_32 | ARCH_ARM64,
                (1u << CHM_ENTRY_BSD_SYSCALL) | (1u << CHM_ENTRY_X86_SYSCALL) |
                (1u << CHM_ENTRY_X86_INT80), CHM_MEM_64BIT_USER_KERNEL, 0, user64,
                0, USER64, KERNEL64, 0x4253442D48414C31ULL, 0x4253442D44525631ULL,
                "BSD/POSIX");
    add_profile(CHM_OS_ANDROID, 14, 0, ARCH_ARM64 | ARCH_X86_64,
                (1u << CHM_ENTRY_X86_SYSCALL), CHM_MEM_64BIT_USER_KERNEL, 0, user64,
                0, USER64, KERNEL64, 0x414E442D48414C31ULL, 0x414E442D44525631ULL,
                "Android/Linux");
    add_profile(CHM_OS_IOS, 17, 0, ARCH_ARM64 | ARCH_X86_64,
                (1u << CHM_ENTRY_X86_SYSCALL), CHM_MEM_64BIT_USER_KERNEL, 0, user64,
                0, USER64, KERNEL64, 0x494F532D48414C31ULL, 0x494F532D44525631ULL,
                "iOS/Darwin");
}

static uint32_t linux_canonical(uint32_t n, uint32_t bits) {
    if (bits == 32u) {
        switch (n) {
            case 1: return 1;
            case 3: return 8;
            case 4: return 9;
            case 5: return 5;
            case 6: return 6;
            case 20: return 2;
            case 45: return 12;
            case 90: return 10;
            case 91: return 11;
            case 162: return 13;
            default: return 0xFFFFFFFFu;
        }
    }
    switch (n) {
        case 0: return 8;
        case 1: return 9;
        case 2: return 5;
        case 3: return 6;
