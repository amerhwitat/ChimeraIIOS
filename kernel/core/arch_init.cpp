#include "../include/chimera/koronos_abi.h"
#include "chimera/arch_backend.h"

static volatile uint32_t arch_state;
static struct koronos_cpu_features cpu = {};

#if defined(__x86_64__) || defined(__i386__)
struct cpuid_regs { uint32_t a,b,c,d; };
static inline cpuid_regs cpuid(uint32_t leaf,uint32_t subleaf) {
    cpuid_regs r{};
    __asm__ volatile("cpuid" : "=a"(r.a),"=b"(r.b),"=c"(r.c),"=d"(r.d) : "a"(leaf),"c"(subleaf));
    return r;
}
static inline uint64_t read_xcr0() {
    uint32_t lo=0,hi=0;
    __asm__ volatile("xgetbv" : "=a"(lo),"=d"(hi) : "c"(0));
    return (static_cast<uint64_t>(hi)<<32)|lo;
}
static void identify_x86() {
    const cpuid_regs basic=cpuid(0,0);
    cpu.max_basic_leaf=basic.a;
    __builtin_memcpy(cpu.vendor+0,&basic.b,4);
    __builtin_memcpy(cpu.vendor+4,&basic.d,4);
    __builtin_memcpy(cpu.vendor+8,&basic.c,4);
    cpu.vendor[12]=0;
    const cpuid_regs ext=cpuid(0x80000000u,0);
    cpu.max_extended_leaf=ext.a;

    if(cpu.max_basic_leaf>=1) {
        const cpuid_regs one=cpuid(1,0);
        const uint32_t eax=one.a;
        const uint32_t base_family=(eax>>8)&0xfu;
        const uint32_t base_model=(eax>>4)&0xfu;
        cpu.stepping=eax&0xfu;
        cpu.family=base_family;
        if(base_family==0xfu) cpu.family+=((eax>>20)&0xffu);
        cpu.model=base_model;
        if(base_family==0x6u || base_family==0xfu) cpu.model|=((eax>>16)&0xfu)<<4;
        cpu.family_model_stepping=eax;
        cpu.logical_cpus=(one.b>>16)&0xffu;
        cpu.processor_id=(one.b>>24)&0xffu;
        cpu.apic=(one.d>>9)&1u;
        cpu.sse2=(one.d>>26)&1u;
        cpu.vmx=(one.c>>5)&1u;
        cpu.hypervisor=(one.c>>31)&1u;
        cpu.x2apic=(one.c>>21)&1u;
        if(one.d&1u) cpu.feature_flags|=KORONOS_CPU_FEAT_FPU;
        if(one.d&(1u<<4)) cpu.feature_flags|=KORONOS_CPU_FEAT_TSC;
        if(cpu.apic) cpu.feature_flags|=KORONOS_CPU_FEAT_APIC;
        if(cpu.x2apic) cpu.feature_flags|=KORONOS_CPU_FEAT_X2APIC;
        if(cpu.sse2) cpu.feature_flags|=KORONOS_CPU_FEAT_SSE2;
        if(cpu.vmx) cpu.feature_flags|=KORONOS_CPU_FEAT_VMX;
        if(cpu.hypervisor) cpu.feature_flags|=KORONOS_CPU_FEAT_HYPERVISOR;
        if(one.c&(1u<<19)) cpu.feature_flags|=KORONOS_CPU_FEAT_SSE41;
        if(one.c&(1u<<20)) cpu.feature_flags|=KORONOS_CPU_FEAT_SSE42;
        if(one.c&(1u<<25)) cpu.feature_flags|=KORONOS_CPU_FEAT_AES;
        if(one.c&(1u<<26)) cpu.feature_flags|=KORONOS_CPU_FEAT_XSAVE;
        if(one.c&(1u<<27)) cpu.feature_flags|=KORONOS_CPU_FEAT_OSXSAVE;
        if(one.c&(1u<<28)) cpu.feature_flags|=KORONOS_CPU_FEAT_AVX;
        if((one.c&(1u<<26)) && (one.c&(1u<<27))) cpu.xcr0=read_xcr0();
        if((cpu.feature_flags&KORONOS_CPU_FEAT_AVX) && (cpu.xcr0&0x6u)!=0x6u)
            cpu.feature_flags&=~KORONOS_CPU_FEAT_AVX;
    }
    if(cpu.max_basic_leaf>=7) {
        const cpuid_regs seven=cpuid(7,0);
        if(seven.b&(1u<<5)) cpu.feature_flags|=KORONOS_CPU_FEAT_AVX2;
        if(seven.b&(1u<<7)) cpu.feature_flags|=KORONOS_CPU_FEAT_SMEP;
        if(seven.b&(1u<<20)) cpu.feature_flags|=KORONOS_CPU_FEAT_SMAP;
        if(seven.b&(1u<<10)) cpu.feature_flags|=KORONOS_CPU_FEAT_INVPCID;
        if((cpu.feature_flags&KORONOS_CPU_FEAT_AVX)==0)
            cpu.feature_flags&=~KORONOS_CPU_FEAT_AVX2;
    }
    if(cpu.max_extended_leaf>=0x80000001u) {
        const cpuid_regs e1=cpuid(0x80000001u,0);
        cpu.long_mode=(e1.d>>29)&1u;
        cpu.nx=(e1.d>>20)&1u;
        cpu.svm=(e1.c>>2)&1u;
        if(cpu.long_mode) cpu.feature_flags|=KORONOS_CPU_FEAT_LONG_MODE;
        if(cpu.nx) cpu.feature_flags|=KORONOS_CPU_FEAT_NX;
        if(cpu.svm) cpu.feature_flags|=KORONOS_CPU_FEAT_SVM;
    }
    if(cpu.max_extended_leaf>=0x80000004u) {
        uint32_t *brand=reinterpret_cast<uint32_t*>(cpu.brand);
        for(uint32_t leaf=0;leaf<3;++leaf) {
            const cpuid_regs r=cpuid(0x80000002u+leaf,0);
            brand[leaf*4+0]=r.a; brand[leaf*4+1]=r.b;
            brand[leaf*4+2]=r.c; brand[leaf*4+3]=r.d;
        }
        cpu.brand[48]=0;
    }
    if(cpu.max_extended_leaf>=0x80000007u) {
        const cpuid_regs e7=cpuid(0x80000007u,0);
        cpu.invariant_tsc=(e7.d>>8)&1u;
        if(cpu.invariant_tsc) cpu.feature_flags|=KORONOS_CPU_FEAT_INVARIANT_TSC;
    }
    if(cpu.max_extended_leaf>=0x80000008u) {
        const cpuid_regs e8=cpuid(0x80000008u,0);
        cpu.physical_address_bits=e8.a&0xffu;
        cpu.virtual_address_bits=(e8.a>>8)&0xffu;
    }
    /* Prefer architectural topology leaves over the legacy package count. */
    uint32_t topo_leaf=0;
    if(cpu.max_basic_leaf>=0x1fu) topo_leaf=0x1fu;
    else if(cpu.max_basic_leaf>=0x0bu) topo_leaf=0x0bu;
    if(topo_leaf) {
        uint32_t maximum_logical=0;
        uint32_t topology_id=cpu.processor_id;
        for(uint32_t subleaf=0;subleaf<8u;++subleaf) {
            const cpuid_regs topo=cpuid(topo_leaf,subleaf);
            const uint32_t level_type=(topo.c>>8)&0xffu;
            const uint32_t level_count=topo.b&0xffffu;
            if(level_count==0u || level_type==0u) break;
            if(level_count>maximum_logical) maximum_logical=level_count;
            topology_id=topo.d;
        }
        if(maximum_logical) cpu.logical_cpus=maximum_logical;
        cpu.processor_id=topology_id;
    }
    cpu.architecture=sizeof(void*)==8 ? KORONOS_ARCH_X86_64 : KORONOS_ARCH_X86;
}
#endif

extern "C" void koronos_arch_init(const koronos_boot_context* ctx) {
    if(!ctx) return;
    arch_state=(ctx->cpu_class<<16)|(ctx->cpu_mode&0xffffu);
    cpu={};
#if defined(__x86_64__) || defined(__i386__)
    identify_x86();
#elif defined(__aarch64__)
    uint64_t midr=0,mpidr=0,pfr0=0,mmfr0=0,isar0=0;
    __asm__ volatile("mrs %0, MIDR_EL1" : "=r"(midr));
    __asm__ volatile("mrs %0, MPIDR_EL1" : "=r"(mpidr));
    __asm__ volatile("mrs %0, ID_AA64PFR0_EL1" : "=r"(pfr0));
    __asm__ volatile("mrs %0, ID_AA64MMFR0_EL1" : "=r"(mmfr0));
    __asm__ volatile("mrs %0, ID_AA64ISAR0_EL1" : "=r"(isar0));
    cpu.architecture=KORONOS_ARCH_AARCH64;
    cpu.implementer=(uint32_t)((midr>>24)&0xffu);
    cpu.variant=(uint32_t)((midr>>20)&0xfu);
    cpu.family=(uint32_t)((midr>>16)&0xfu);
    cpu.model=(uint32_t)((midr>>4)&0xfffu);
    cpu.stepping=(uint32_t)(midr&0xfu);
    cpu.processor_id=(uint32_t)(mpidr&0xffffffu);
    /* ID_AA64MMFR0_EL1.PARange is an encoding, not a bit count. */
    static const uint8_t pa_bits[8]={32,36,40,42,44,48,52,56};
    const uint32_t pa_encoding=(uint32_t)(mmfr0&0xfu);
    if(pa_encoding<8u) cpu.physical_address_bits=pa_bits[pa_encoding];
    __builtin_memcpy(cpu.vendor,"ARM",4);
    /* Keep raw architectural ID registers separate from normalized feature
       flags. A raw register value must never be interpreted as an enabled
       instruction feature by the scheduler or context-switch path. */
    cpu.architecture_features[0]=pfr0;
    cpu.architecture_features[1]=mmfr0;
    cpu.architecture_features[2]=isar0;
#elif defined(__riscv)
# if __riscv_xlen == 64
    cpu.architecture=KORONOS_ARCH_RISCV64;
# else
    cpu.architecture=KORONOS_ARCH_RISCV32;
# endif
    cpu.logical_cpus=1; /* boot hart only; total topology remains unknown */
    __builtin_memcpy(cpu.vendor,"firmware",9);
    /* Koronos enters through OpenSBI in supervisor mode. M-mode-only CSRs
       (misa, mvendorid, marchid, mimpid, mhartid) are intentionally not read
       here: they can trap. A later FDT/ACPI+SBI probe supplies hart identity,
       ISA extensions and interrupt-controller topology. */
#elif defined(__arm__)
    cpu.architecture=KORONOS_ARCH_ARM;
    __builtin_memcpy(cpu.vendor,"ARM",4);
#else
    cpu.architecture=KORONOS_ARCH_UNKNOWN;
    __builtin_memcpy(cpu.vendor,"unknown",8);
#endif
    if(cpu.logical_cpus==0) cpu.logical_cpus=1;
    const koronos_arch_backend *backend=koronos_arch_backend_lookup(cpu.architecture);
    if(backend) {
        cpu.backend_status=backend->status;
        cpu.entry_backend_present=backend->entry_stub_present;
        cpu.interrupt_backend_present=backend->interrupt_backend_present;
        cpu.syscall_backend_present=backend->syscall_backend_present;
    }
    uint32_t compat=0;
#if defined(__x86_64__) || defined(__i386__)
    if(!cpu.long_mode || !cpu.sse2) compat=1;
#endif
    const_cast<koronos_boot_context*>(ctx)->detected_cores=cpu.logical_cpus;
    const_cast<koronos_boot_context*>(ctx)->compatibility_mode=compat;
}
extern "C" const struct koronos_cpu_features* koronos_get_cpu_features(){ return &cpu; }
