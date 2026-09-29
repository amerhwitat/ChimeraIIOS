#include "chimera/hardware.h"
#include <stddef.h>

#if defined(__x86_64__) || defined(__i386__)
static void cpuid(uint32_t leaf, uint32_t subleaf, uint32_t *a, uint32_t *b, uint32_t *c, uint32_t *d) {
    uint32_t aa, bb, cc, dd;
    __asm__ volatile("cpuid" : "=a"(aa), "=b"(bb), "=c"(cc), "=d"(dd)
                     : "a"(leaf), "c"(subleaf));
    *a = aa; *b = bb; *c = cc; *d = dd;
}
#endif

extern "C" int chimera_hardware_probe(chimera_hardware_profile *out) {
    if (!out) return -1;
    for (size_t i = 0; i < sizeof(*out); ++i) ((unsigned char*)out)[i] = 0;
    out->version = CHIMERA_HW_PROFILE_VERSION;
    out->maximum_emulated_nbit = CHIMERA_NBIT_8192;

#if defined(__x86_64__) || defined(__i386__)
    out->architecture = CHIMERA_ARCH_X86_64;
    out->native_pointer_bits = sizeof(void*) * 8u;
    out->native_nbit_mode = (sizeof(void*) == 8) ? CHIMERA_NBIT_64 : CHIMERA_NBIT_32;
    out->physical_address_bits = 36;
    out->virtual_address_bits = 48;
    uint32_t a,b,c,d;
    cpuid(0,0,&a,&b,&c,&d);
    uint32_t vendor_words[3] = {b, d, c};
    for (size_t word = 0; word < 3; ++word) {
        for (size_t byte = 0; byte < 4; ++byte) {
            size_t i = word * 4 + byte;
            out->vendor[i] = (char)((vendor_words[word] >> (byte * 8)) & 0xffu);
        }
    }
    cpuid(1,0,&a,&b,&c,&d);
    out->logical_cpus = (b >> 16) & 0xffu;
    if (!out->logical_cpus) out->logical_cpus = 1;
    if (d & (1u<<26)) out->feature_bits |= CHIMERA_HW_SSE2;
    if (c & (1u<<25)) out->feature_bits |= CHIMERA_HW_AES;
    if (c & (1u<<30)) out->feature_bits |= CHIMERA_HW_RDRAND;
    if (c & (1u<<5)) out->feature_bits |= CHIMERA_HW_VMX;
    if (c & (1u<<28)) out->feature_bits |= CHIMERA_HW_AVX;
    uint32_t max_leaf=a;
    if(max_leaf>=0x80000008u){
        cpuid(0x80000008u,0,&a,&b,&c,&d);
        out->physical_address_bits=a&0xffu;
        out->virtual_address_bits=(a>>8)&0xffu;
    }
    cpuid(0x80000000u,0,&a,&b,&c,&d);
    if(a>=0x80000004u){
        uint32_t *m=(uint32_t*)out->model;
        cpuid(0x80000002u,0,&m[0],&m[1],&m[2],&m[3]);
        cpuid(0x80000003u,0,&m[4],&m[5],&m[6],&m[7]);
        cpuid(0x80000004u,0,&m[8],&m[9],&m[10],&m[11]);
        out->model[95]=0;
    }
    if (max_leaf >= 7) {
        cpuid(7,0,&a,&b,&c,&d);
        if (b & (1u<<5)) out->feature_bits |= CHIMERA_HW_AVX2;
        if (b & (1u<<16)) out->feature_bits |= CHIMERA_HW_AVX512;
    }
#elif defined(__aarch64__)
    out->architecture = CHIMERA_ARCH_AARCH64;
    out->native_pointer_bits = 64;
    out->native_nbit_mode = CHIMERA_NBIT_64;
    out->physical_address_bits = 48;
    out->virtual_address_bits = 48;
    out->logical_cpus = 1;
    out->feature_bits |= CHIMERA_HW_NEON;
#elif defined(__riscv) && (__riscv_xlen == 64)
    out->architecture = CHIMERA_ARCH_RISCV64;
    out->native_pointer_bits = 64;
    out->native_nbit_mode = CHIMERA_NBIT_64;
    out->physical_address_bits = 56;
    out->virtual_address_bits = 39;
    out->logical_cpus = 1;
#else
    out->architecture = CHIMERA_ARCH_UNKNOWN;
    out->native_pointer_bits = sizeof(void*) * 8u;
    out->native_nbit_mode = out->native_pointer_bits;
    out->logical_cpus = 1;
#endif

    out->best_nbit_mode = (out->native_nbit_mode >= 64) ? CHIMERA_NBIT_64 : out->native_nbit_mode;
    out->compatibility_mask = CHIMERA_COMPAT_NATIVE |
        CHIMERA_COMPAT_WINDOWS | CHIMERA_COMPAT_LINUX | CHIMERA_COMPAT_BSD |
        CHIMERA_COMPAT_DARWIN | CHIMERA_COMPAT_ANDROID | CHIMERA_COMPAT_IOS;
    return 0;
}

extern "C" int chimera_hardware_best_mode(const chimera_hardware_profile *profile) {
    return profile ? (int)profile->best_nbit_mode : -1;
}

extern "C" int chimera_hardware_supports_mode(const chimera_hardware_profile *profile, uint32_t bits) {
    if (!profile || bits == 0) return 0;
    if (bits <= profile->native_nbit_mode) return 1;
    return bits <= profile->maximum_emulated_nbit;
}

extern "C" uint32_t chimera_hardware_compatibility_mask(const chimera_hardware_profile *profile) {
    return profile ? profile->compatibility_mask : 0;
}
