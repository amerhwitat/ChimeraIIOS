#include "../include/chimera/koronos_abi.h"
static volatile uint32_t arch_state;
static struct koronos_cpu_features cpu = {};
#if defined(__x86_64__) || defined(__i386__)
static inline void cpuid(uint32_t leaf,uint32_t subleaf,uint32_t& a,uint32_t& b,uint32_t& c,uint32_t& d) {
 __asm__ volatile("cpuid" : "=a"(a),"=b"(b),"=c"(c),"=d"(d) : "a"(leaf),"c"(subleaf));
}
#endif
extern "C" void koronos_arch_init(const koronos_boot_context* ctx) {
 if(!ctx)return;
 arch_state=(ctx->cpu_class<<16)|(ctx->cpu_mode&0xffffu);
#if defined(__x86_64__) || defined(__i386__)
 uint32_t a=0,b=0,c=0,d=0;
 cpuid(0,0,a,b,c,d); cpu.max_basic_leaf=a;
 __builtin_memcpy(cpu.vendor+0,&b,4); __builtin_memcpy(cpu.vendor+4,&d,4); __builtin_memcpy(cpu.vendor+8,&c,4); cpu.vendor[12]=0;
 cpuid(0x80000000u,0,a,b,c,d); cpu.max_extended_leaf=a;
 if(cpu.max_basic_leaf>=1) { cpuid(1,0,a,b,c,d); cpu.family_model_stepping=a; cpu.logical_cpus=(b>>16)&0xffu; cpu.apic=(d>>9)&1u; cpu.sse2=(d>>26)&1u; cpu.vmx=(c>>5)&1u; cpu.hypervisor=(c>>31)&1u; cpu.x2apic=(c>>21)&1u; }
 if(cpu.max_extended_leaf>=0x80000001u) { cpuid(0x80000001u,0,a,b,c,d); cpu.long_mode=(d>>29)&1u; cpu.nx=(d>>20)&1u; cpu.svm=(c>>2)&1u; }
 if(cpu.max_extended_leaf>=0x80000007u) { cpuid(0x80000007u,0,a,b,c,d); cpu.invariant_tsc=(d>>8)&1u; }
#else
 cpu.logical_cpus=1;
#if defined(__aarch64__)
 __builtin_memcpy(cpu.vendor,"AArch64",8);
#elif defined(__riscv)
 __builtin_memcpy(cpu.vendor,"RISC-V",7);
#else
 __builtin_memcpy(cpu.vendor,"generic",7);
#endif
 cpu.vendor[12]=0;
#endif
 if(cpu.logical_cpus==0) cpu.logical_cpus=1;
}
extern "C" const struct koronos_cpu_features* koronos_get_cpu_features(){ return &cpu; }
extern "C" void koronos_idle_loop(void) {
 for(;;) {
#if defined(__x86_64__) || defined(__i386__)
  __asm__ volatile("pause" ::: "memory");
#elif defined(__aarch64__)
  __asm__ volatile("yield" ::: "memory");
#elif defined(__riscv)
  __asm__ volatile("nop" ::: "memory");
#else
  __asm__ volatile("" ::: "memory");
#endif
 }
}
