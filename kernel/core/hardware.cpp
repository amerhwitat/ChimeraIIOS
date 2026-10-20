#include "chimera/hardware.h"
#include <stddef.h>

#if defined(__x86_64__) || defined(__i386__)
static void cpuid(uint32_t leaf, uint32_t subleaf, uint32_t *a, uint32_t *b, uint32_t *c, uint32_t *d) {
    uint32_t aa, bb, cc, dd;
    __asm__ volatile("cpuid" : "=a"(aa), "=b"(bb), "=c"(cc), "=d"(dd)
                     : "a"(leaf), "c"(subleaf));
    *a = aa; *b = bb; *c = cc; *d = dd;
}
static int vendor_is(const char *vendor, const char *expected) {
    for (uint32_t i = 0; i < 12; ++i) if (vendor[i] != expected[i]) return 0;
    return 1;
}
#endif

extern "C" int chimera_hardware_probe(chimera_hardware_profile *out) {
    if (!out) return -1;
    for (size_t i = 0; i < sizeof(*out); ++i) ((unsigned char*)out)[i] = 0;
    out->version = CHIMERA_HW_PROFILE_VERSION;
    /* This is a supported emulation ceiling, not evidence of an emulator. */
    out->maximum_emulated_nbit = CHIMERA_NBIT_8192;

#if defined(__x86_64__) || defined(__i386__)
    out->architecture = CHIMERA_ARCH_X86_64;
    out->native_pointer_bits = sizeof(void*) * 8u;
    out->native_nbit_mode = (sizeof(void*) == 8) ? CHIMERA_NBIT_64 : CHIMERA_NBIT_32;
    uint32_t a=0,b=0,c=0,d=0;
    cpuid(0,0,&a,&b,&c,&d);
    const uint32_t max_basic_leaf = a;
    uint32_t vendor_words[3] = {b, d, c};
    for (size_t word = 0; word < 3; ++word) for (size_t byte = 0; byte < 4; ++byte) {
        const size_t i = word * 4 + byte;
        out->vendor[i] = (char)((vendor_words[word] >> (byte * 8)) & 0xffu);
    }
    out->vendor[12] = 0;
    if (vendor_is(out->vendor, "GenuineIntel")) out->cpu_vendor_id = CHIMERA_CPU_VENDOR_INTEL;
    else if (vendor_is(out->vendor, "AuthenticAMD")) out->cpu_vendor_id = CHIMERA_CPU_VENDOR_AMD;
    else if (vendor_is(out->vendor, "HygonGenuine")) out->cpu_vendor_id = CHIMERA_CPU_VENDOR_HYGON;
    else if (vendor_is(out->vendor, "CentaurHauls")) out->cpu_vendor_id = CHIMERA_CPU_VENDOR_VIA;

    if (max_basic_leaf >= 1) {
        cpuid(1,0,&a,&b,&c,&d);
        const uint32_t signature = a;
        const uint32_t base_family = (signature >> 8) & 0xFu;
        const uint32_t base_model = (signature >> 4) & 0xFu;
        out->cpu_family = base_family == 0xFu ? base_family + ((signature >> 20) & 0xFFu) : base_family;
        out->cpu_model = (base_family == 0x6u || base_family == 0xFu)
            ? base_model | (((signature >> 16) & 0xFu) << 4) : base_model;
        out->cpu_stepping = signature & 0xFu;
        out->logical_cpus = (b >> 16) & 0xFFu;
        if (!out->logical_cpus) out->logical_cpus = 1;
        if (d & (1u<<26)) out->feature_bits |= CHIMERA_HW_SSE2;
        if (c & (1u<<25)) out->feature_bits |= CHIMERA_HW_AES;
        if (c & (1u<<30)) out->feature_bits |= CHIMERA_HW_RDRAND;
        if (c & (1u<<5)) out->feature_bits |= CHIMERA_HW_VMX;
        if ((c & (1u<<28)) && (c & (1u<<27))) out->feature_bits |= CHIMERA_HW_AVX;
    } else {
        out->logical_cpus = 1;
    }

    uint32_t ext_max=0;
    cpuid(0x80000000u,0,&ext_max,&b,&c,&d);
    if (ext_max >= 0x80000001u) {
        cpuid(0x80000001u,0,&a,&b,&c,&d);
        if (c & (1u<<2)) out->feature_bits |= CHIMERA_HW_SVM;
    }
    if (ext_max >= 0x80000008u) {
        cpuid(0x80000008u,0,&a,&b,&c,&d);
        out->physical_address_bits = a & 0xFFu;
        out->virtual_address_bits = (a >> 8) & 0xFFu;
    }
    if (ext_max >= 0x80000004u) {
        uint32_t *m=(uint32_t*)out->model;
        cpuid(0x80000002u,0,&m[0],&m[1],&m[2],&m[3]);
        cpuid(0x80000003u,0,&m[4],&m[5],&m[6],&m[7]);
        cpuid(0x80000004u,0,&m[8],&m[9],&m[10],&m[11]);
        out->model[95]=0;
    }

    /* Prefer architectural topology (SMT and core levels) when exposed. */
    uint32_t topology_leaf = max_basic_leaf >= 0x1Fu ? 0x1Fu :
                             (max_basic_leaf >= 0x0Bu ? 0x0Bu : 0u);
    uint32_t smt_threads = 1, package_logical = out->logical_cpus, core_count = 0;
    if (topology_leaf) {
        for (uint32_t level = 0; level < 8; ++level) {
            cpuid(topology_leaf, level, &a, &b, &c, &d);
            if ((b & 0xFFFFu) == 0 || ((c >> 8) & 0xFFu) == 0) break;
            const uint32_t type = (c >> 8) & 0xFFu;
            if (type == 1u) smt_threads = b & 0xFFFFu;
            if (type == 2u) package_logical = b & 0xFFFFu;
        }
    }
    if (!core_count && topology_leaf && package_logical >= smt_threads) core_count = package_logical / smt_threads;
    if (!core_count && max_basic_leaf >= 4u) {
        cpuid(4,0,&a,&b,&c,&d);
        if ((a & 0x1Fu) != 0) core_count = ((a >> 26) & 0x3Fu) + 1u;
    }
    if (!core_count && out->cpu_vendor_id == CHIMERA_CPU_VENDOR_AMD && ext_max >= 0x80000008u) {
        cpuid(0x80000008u,0,&a,&b,&c,&d);
        core_count = (c & 0xFFu) + 1u;
    }
    if (!core_count) core_count = package_logical;
    if (!package_logical) package_logical = 1;
    if (!smt_threads) smt_threads = 1;
    out->logical_cpus = package_logical;
    out->physical_cores = core_count;
    out->logical_per_core = (package_logical >= core_count && core_count) ? package_logical / core_count : 1u;

    if (max_basic_leaf >= 7u) {
        cpuid(7,0,&a,&b,&c,&d);
        if (b & (1u<<5)) out->feature_bits |= CHIMERA_HW_AVX2;
        if (b & (1u<<16)) out->feature_bits |= CHIMERA_HW_AVX512;
    }
    if (!out->physical_address_bits) out->physical_address_bits = 36;
    if (!out->virtual_address_bits) out->virtual_address_bits = 48;
#elif defined(__aarch64__)
    out->architecture = CHIMERA_ARCH_AARCH64;
    out->native_pointer_bits = 64;
    out->native_nbit_mode = CHIMERA_NBIT_64;
    out->physical_address_bits = 48;
    out->virtual_address_bits = 48;
    out->logical_cpus = out->physical_cores = out->logical_per_core = 1;
    out->cpu_vendor_id = CHIMERA_CPU_VENDOR_ARM;
    out->feature_bits |= CHIMERA_HW_NEON;
#elif defined(__riscv) && (__riscv_xlen == 64)
    out->architecture = CHIMERA_ARCH_RISCV64;
    out->native_pointer_bits = 64;
    out->native_nbit_mode = CHIMERA_NBIT_64;
    out->physical_address_bits = 56;
    out->virtual_address_bits = 39;
    out->logical_cpus = out->physical_cores = out->logical_per_core = 1;
    out->cpu_vendor_id = CHIMERA_CPU_VENDOR_RISCV;
#else
    out->architecture = CHIMERA_ARCH_UNKNOWN;
    out->native_pointer_bits = sizeof(void*) * 8u;
    out->native_nbit_mode = out->native_pointer_bits;
    out->logical_cpus = out->physical_cores = out->logical_per_core = 1;
#endif

    if (!out->logical_cpus) out->logical_cpus = 1;
    if (!out->physical_cores) out->physical_cores = 1;
    if (!out->logical_per_core) out->logical_per_core = 1;
    out->best_nbit_mode = (out->native_nbit_mode >= 64)
        ? static_cast<uint32_t>(CHIMERA_NBIT_64) : out->native_nbit_mode;
    /* OS compatibility requires ABI/runtime layers; hardware alone cannot
       certify Linux, Windows, Darwin, or mobile application support. */
    out->compatibility_mask = CHIMERA_COMPAT_NATIVE;
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
