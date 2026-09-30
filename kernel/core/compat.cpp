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
                1u << CHM_ENTRY_X86_SYSCALL, CHM_MEM_NATIVE, user64,
                0, USER64, KERNEL64, 0x43484D2D48414C31ULL, 0x43484D2D44525631ULL,
                "Chimera Native");
    add_profile(CHM_OS_LINUX, 6, 11, ARCH_X86_64 | ARCH_X86_32 | ARCH_ARM64,
                (1u << CHM_ENTRY_X86_SYSCALL) | (1u << CHM_ENTRY_X86_INT80) |
                (1u << CHM_ENTRY_X86_SYSENTER), CHM_MEM_64BIT_USER_KERNEL, user64,
                0, USER64, KERNEL64, 0x4C4E582D48414C31ULL, 0x4C4E582D44525631ULL,
                "Linux/POSIX");
    add_profile(CHM_OS_WINDOWS_NT, 10, 0, ARCH_X86_64 | ARCH_X86_32 | ARCH_ARM64,
                (1u << CHM_ENTRY_X86_SYSCALL) | (1u << CHM_ENTRY_X86_SYSENTER) |
                (1u << CHM_ENTRY_X86_INT2E), CHM_MEM_64BIT_USER_KERNEL, user64,
                0, USER64, KERNEL64, 0x4E542D48414C2D31ULL, 0x4E542D4452562D31ULL,
                "Windows NT/Win32");
    add_profile(CHM_OS_WINDOWS_9X, 4, 9, ARCH_X86_32,
                (1u << CHM_ENTRY_X86_INT2E) | (1u << CHM_ENTRY_X86_SYSENTER),
                CHM_MEM_WIN9X_VMM, user32,
                0, USER32, KERNEL32, 0x57394E482D564D4DULL, 0x57394E442D445256ULL,
                "Windows 9x/Me");
    add_profile(CHM_OS_DOS, 6, 22, ARCH_X86_32,
                (1u << CHM_ENTRY_X86_INT21), CHM_MEM_DOS_REAL_MODE,
                CHM_COMPAT_USERSPACE | CHM_COMPAT_32BIT | CHM_COMPAT_INTERRUPT_TRANSLATION |
                CHM_COMPAT_EMULATION_REQUIRED, 0, USER32, 0, KERNEL32,
                0x444F532D48414C31ULL, 0x444F532D44525631ULL, "DOS");
    add_profile(CHM_OS_DARWIN, 23, 0, ARCH_X86_64 | ARCH_X86_32 | ARCH_ARM64,
                (1u << CHM_ENTRY_X86_SYSCALL) | (1u << CHM_ENTRY_X86_INT80),
                CHM_MEM_64BIT_USER_KERNEL, user64,
                0, USER64, KERNEL64, 0x4441522D48414C31ULL, 0x4441522D44525631ULL,
                "Darwin/Unix");
    add_profile(CHM_OS_MACH, 3, 0, ARCH_X86_64 | ARCH_ARM64,
                (1u << CHM_ENTRY_MACH_TRAP) | (1u << CHM_ENTRY_X86_SYSCALL),
                CHM_MEM_64BIT_USER_KERNEL, user64,
                0, USER64, KERNEL64, 0x4D41434848414C31ULL, 0x4D41434844525631ULL,
                "Mach");
    add_profile(CHM_OS_BSD, 1, 0, ARCH_X86_64 | ARCH_X86_32 | ARCH_ARM64,
                (1u << CHM_ENTRY_BSD_SYSCALL) | (1u << CHM_ENTRY_X86_SYSCALL) |
                (1u << CHM_ENTRY_X86_INT80), CHM_MEM_64BIT_USER_KERNEL, user64,
                0, USER64, KERNEL64, 0x4253442D48414C31ULL, 0x4253442D44525631ULL,
                "BSD/POSIX");
    add_profile(CHM_OS_ANDROID, 14, 0, ARCH_ARM64 | ARCH_X86_64,
                (1u << CHM_ENTRY_X86_SYSCALL), CHM_MEM_64BIT_USER_KERNEL, user64,
                0, USER64, KERNEL64, 0x414E442D48414C31ULL, 0x414E442D44525631ULL,
                "Android/Linux");
    add_profile(CHM_OS_IOS, 17, 0, ARCH_ARM64 | ARCH_X86_64,
                (1u << CHM_ENTRY_X86_SYSCALL), CHM_MEM_64BIT_USER_KERNEL, user64,
                0, USER64, KERNEL64, 0x494F532D48414C31ULL, 0x494F532D44525631ULL,
                "iOS/Darwin");
}

static uint32_t linux_canonical(uint32_t n, uint32_t bits) {
    if (bits == 32u) {
        switch (n) {
            case 1: return 1;   /* exit */
            case 3: return 8;   /* read */
            case 4: return 9;   /* write */
            case 5: return 5;   /* open */
            case 6: return 6;   /* close */
            case 20: return 2;  /* getpid */
            case 45: return 12; /* brk */
            case 90: return 10; /* mmap */
            case 91: return 11; /* munmap */
            case 162: return 13;/* nanosleep */
            default: return 0xFFFFFFFFu;
        }
    }
    switch (n) {
        case 0: return 8;   /* read */
        case 1: return 9;   /* write */
        case 2: return 5;   /* open */
        case 3: return 6;   /* close */
        case 9: return 10;  /* mmap */
        case 11: return 11; /* munmap */
        case 12: return 12; /* brk */
        case 16: return 11; /* ioctl */
        case 35: return 13; /* nanosleep */
        case 39: return 2;  /* getpid */
        case 60: return 1;  /* exit */
        case 61: return 14; /* wait */
        case 158: return 15;/* arch_prctl */
        case 231: return 16;/* exit_group */
        default: return 0xFFFFFFFFu;
    }
}

} // namespace

extern "C" int chimera_compat_init(uint32_t architecture, uint32_t bitness) {
    g_arch = architecture;
    g_bits = bitness;
    g_syscalls = 0;
    g_interrupts = 0;
    build_profiles();
    g_initialized = 1;
    return 0;
}

extern "C" int chimera_compat_probe(void) {
    if (!g_initialized) return -1;
    g_syscalls = CHIMERA_COMPAT_MAX_SYSCALLS;
    g_interrupts = 256u;
    return 0;
}

extern "C" int chimera_compat_get_snapshot(chimera_compat_snapshot *out) {
    if (!out) return -1;
    out->abi = CHIMERA_COMPAT_ABI;
    out->profile_count = g_profile_count;
    out->syscall_count = g_syscalls;
    out->interrupt_count = g_interrupts;
    out->initialized = g_initialized;
    out->current_arch = g_arch;
    out->current_bitness = g_bits;
    out->supported_os_mask = (1ULL << CHIMERA_COMPAT_MAX) - 1ULL;
    return 0;
}

extern "C" const chimera_compat_profile *chimera_compat_profile_at(uint32_t index) {
    return index < g_profile_count ? &g_profiles[index] : 0;
}

extern "C" int chimera_compat_recognize_syscall(uint32_t entry, uint32_t bitness,
                                                  uint32_t number, chimera_syscall_identity *out) {
    if (!out) return -1;
    out->os = CHM_OS_NATIVE; out->entry = entry; out->bitness = bitness;
    out->number = number; out->canonical = 0xFFFFFFFFu; out->flags = 0;

    if (entry == CHM_ENTRY_X86_INT21) {
        out->os = CHM_OS_DOS; out->canonical = 0x100u | (number & 0xFFu);
        out->flags = CHM_COMPAT_INTERRUPT_TRANSLATION | CHM_COMPAT_EMULATION_REQUIRED;
        return 0;
    }
    if (entry == CHM_ENTRY_X86_INT2E || entry == CHM_ENTRY_X86_SYSENTER) {
        out->os = CHM_OS_WINDOWS_NT;
        out->flags = CHM_COMPAT_SYSCALL_TRANSLATION | CHM_COMPAT_HAL_TRANSLATION |
                     CHM_COMPAT_DRIVER_TRANSLATION;
        return 0;
    }
    if (entry == CHM_ENTRY_MACH_TRAP) {
        out->os = CHM_OS_MACH;
        out->canonical = number;
        out->flags = CHM_COMPAT_SYSCALL_TRANSLATION | CHM_COMPAT_POINTER_TRANSLATION;
        return 0;
    }
    if (entry == CHM_ENTRY_BSD_SYSCALL) {
        out->os = CHM_OS_BSD; out->canonical = number;
        out->flags = CHM_COMPAT_SYSCALL_TRANSLATION;
        return 0;
    }
    if (entry == CHM_ENTRY_X86_INT80 || entry == CHM_ENTRY_X86_SYSCALL) {
        out->os = CHM_OS_LINUX;
        out->canonical = linux_canonical(number, bitness);
        out->flags = CHM_COMPAT_SYSCALL_TRANSLATION;
        if (bitness == 32u) out->flags |= CHM_COMPAT_32BIT | CHM_COMPAT_POINTER_TRANSLATION;
        else out->flags |= CHM_COMPAT_64BIT;
        return 0;
    }
    return 0;
}

extern "C" int chimera_compat_recognize_interrupt(uint32_t vector, chimera_interrupt_identity *out) {
    if (!out || vector > 255u) return -1;
    out->os = CHM_OS_NATIVE; out->vector = vector; out->entry = CHM_ENTRY_NATIVE; out->flags = 0;
    if (vector == 0x80u) { out->os = CHM_OS_LINUX; out->entry = CHM_ENTRY_X86_INT80; out->flags = CHM_COMPAT_SYSCALL_TRANSLATION; }
    else if (vector == 0x2Eu) { out->os = CHM_OS_WINDOWS_NT; out->entry = CHM_ENTRY_X86_INT2E; out->flags = CHM_COMPAT_SYSCALL_TRANSLATION; }
    else if (vector == 0x21u) { out->os = CHM_OS_DOS; out->entry = CHM_ENTRY_X86_INT21; out->flags = CHM_COMPAT_EMULATION_REQUIRED; }
    else if (vector >= 32u) { out->flags = CHM_COMPAT_INTERRUPT_TRANSLATION; }
    return 0;
}

extern "C" int chimera_compat_memory_profile(uint32_t os, chimera_memory_model *model,
                                               uint64_t *user_high, uint64_t *kernel_low) {
    if (!model || !user_high || !kernel_low) return -1;
    for (uint32_t i = 0; i < g_profile_count; ++i) {
        if (g_profiles[i].os == os) {
            *model = (chimera_memory_model)g_profiles[i].memory_model;
            *user_high = g_profiles[i].user_high;
            *kernel_low = g_profiles[i].kernel_low;
            return 0;
        }
    }
    return -1;
}

extern "C" int chimera_compat_hal_profile(uint32_t os, uint64_t *hal_abi, uint64_t *driver_abi) {
    if (!hal_abi || !driver_abi) return -1;
    for (uint32_t i = 0; i < g_profile_count; ++i) {
        if (g_profiles[i].os == os) {
            *hal_abi = g_profiles[i].hal_abi;
            *driver_abi = g_profiles[i].driver_abi;
            return 0;
        }
    }
    return -1;
}

extern "C" const char *chimera_compat_os_name(uint32_t os) {
    switch (os) {
        case CHM_OS_NATIVE: return "Chimera Native";
        case CHM_OS_LINUX: return "Linux/POSIX";
        case CHM_OS_WINDOWS_NT: return "Windows NT/Win32";
        case CHM_OS_WINDOWS_9X: return "Windows 9x/Me";
        case CHM_OS_DOS: return "DOS";
        case CHM_OS_DARWIN: return "Darwin/Unix";
        case CHM_OS_MACH: return "Mach";
        case CHM_OS_BSD: return "BSD/POSIX";
        case CHM_OS_ANDROID: return "Android/Linux";
        case CHM_OS_IOS: return "iOS/Darwin";
        default: return "Unknown OS";
    }
}

extern "C" const char *chimera_compat_entry_name(uint32_t entry) {
    switch (entry) {
        case CHM_ENTRY_NATIVE: return "native";
        case CHM_ENTRY_X86_SYSCALL: return "x86-64 SYSCALL";
        case CHM_ENTRY_X86_SYSENTER: return "x86 SYSENTER";
        case CHM_ENTRY_X86_INT80: return "x86 INT 0x80";
        case CHM_ENTRY_X86_INT2E: return "x86 INT 0x2E";
        case CHM_ENTRY_X86_INT21: return "x86 INT 0x21";
        case CHM_ENTRY_MACH_TRAP: return "Mach trap";
        case CHM_ENTRY_BSD_SYSCALL: return "BSD syscall";
        default: return "unknown entry";
    }
}
