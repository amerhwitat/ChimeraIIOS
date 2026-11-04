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
    const uint32_t max_basic_leaf=a;
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
    out->physical_cores=out->logical_cpus;
    out->threads_per_core=1;
    out->current_apic_id=(b>>24)&0xffu;
    if(d&(1u<<9))out->feature_bits|=CHIMERA_HW_APIC;
    if(c&(1u<<21))out->feature_bits|=CHIMERA_HW_X2APIC;
    /* Prefer architectural topology leaves over the legacy leaf-1 logical
       processor count. These describe discoverable package topology, not CPUs
       that the kernel has actually brought online. */
    uint32_t topology_leaf=0,package_logical=0,smt_logical=0,core_logical=0,topology_apic=0;
    if(max_basic_leaf>=0x1Fu)topology_leaf=0x1Fu;
    else if(max_basic_leaf>=0x0Bu)topology_leaf=0x0Bu;
    if(topology_leaf){
        for(uint32_t sub=0;sub<8u;sub++){
            uint32_t ta=0,tb=0,tc=0,td=0;
            cpuid(topology_leaf,sub,&ta,&tb,&tc,&td);
            const uint32_t level_count=tb&0xFFFFu;
            const uint32_t level_type=(tc>>8)&0xFFu;
            if(!level_count||!level_type)break;
            if(level_count>package_logical)package_logical=level_count;
            if(level_type==1u)smt_logical=level_count;
            if(level_type==2u)core_logical=level_count;
            topology_apic=td;
        }
    }
    if(!package_logical && topology_leaf==0x1Fu){
        topology_leaf=0x0Bu;
        for(uint32_t sub=0;sub<8u;sub++){
            uint32_t ta=0,tb=0,tc=0,td=0;
            cpuid(topology_leaf,sub,&ta,&tb,&tc,&td);
            const uint32_t level_count=tb&0xFFFFu;
            const uint32_t level_type=(tc>>8)&0xFFu;
            if(!level_count||!level_type)break;
            if(level_count>package_logical)package_logical=level_count;
            if(level_type==1u)smt_logical=level_count;
            if(level_type==2u)core_logical=level_count;
            topology_apic=td;
        }
    }
    if(package_logical){
        out->logical_cpus=package_logical;
        out->threads_per_core=smt_logical?smt_logical:1u;
        out->physical_cores=core_logical
            ? (core_logical+out->threads_per_core-1u)/out->threads_per_core
            : (package_logical+out->threads_per_core-1u)/out->threads_per_core;
        out->current_apic_id=topology_apic;
        out->topology_leaf=topology_leaf;
        out->topology_valid=1u;
    }
    if (d & (1u<<26)) out->feature_bits |= CHIMERA_HW_SSE2;
    if (c & (1u<<25)) out->feature_bits |= CHIMERA_HW_AES;
    if (c & (1u<<30)) out->feature_bits |= CHIMERA_HW_RDRAND;
    if (c & (1u<<5)) out->feature_bits |= CHIMERA_HW_VMX;
    if (c & (1u<<28)) out->feature_bits |= CHIMERA_HW_AVX;
    uint32_t ext_max=0;
    cpuid(0x80000000u,0,&ext_max,&b,&c,&d);
    if(ext_max>=0x80000008u){
        cpuid(0x80000008u,0,&a,&b,&c,&d);
        out->physical_address_bits=a&0xffu;
        out->virtual_address_bits=(a>>8)&0xffu;
        /* AMD extended topology is the fallback when architectural leaf B/1F
           is unavailable. */
        if(!out->topology_valid&&ext_max>=0x8000001Eu){
            uint32_t ea=0,eb=0,ec=0,ed=0;
            cpuid(0x8000001Eu,0,&ea,&eb,&ec,&ed);
            const uint32_t threads=((eb>>8)&0xFFu)+1u;
            const uint32_t cores=(c&0xFFu)+1u;
            out->threads_per_core=threads;
            out->physical_cores=cores;
            out->logical_cpus=cores*threads;
            out->current_apic_id=ea;
            out->topology_leaf=0x8000001Eu;
            out->topology_valid=1u;
        }
    }
    if(ext_max>=0x80000004u){
        uint32_t *m=(uint32_t*)out->model;
        cpuid(0x80000002u,0,&m[0],&m[1],&m[2],&m[3]);
        cpuid(0x80000003u,0,&m[4],&m[5],&m[6],&m[7]);
        cpuid(0x80000004u,0,&m[8],&m[9],&m[10],&m[11]);
        out->model[95]=0;
    }
    if (max_basic_leaf >= 7) {
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

    if(!out->logical_cpus)out->logical_cpus=1u;
    if(!out->physical_cores)out->physical_cores=out->logical_cpus;
    if(!out->threads_per_core)out->threads_per_core=1u;
    out->best_nbit_mode = (out->native_nbit_mode >= 64)
        ? static_cast<uint32_t>(CHIMERA_NBIT_64)
        : out->native_nbit_mode;
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
