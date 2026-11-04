#include "chimera/arch_backend.h"

namespace {
static const koronos_arch_backend k_backends[] = {
 {KORONOS_ARCH_X86_64,KORONOS_CPU_CISC,KORONOS_BACKEND_PARTIAL,1,1,1,0,"x86_64","IDT + legacy PIC/PIT; APIC routing incomplete","DPL3 INT 0x80 acknowledgement; native SYSCALL path partial"},
 {KORONOS_ARCH_X86,KORONOS_CPU_CISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"i386","IDT + PIC/APIC (not ported)","int 0x80/SYSENTER (not ported)"},
 {KORONOS_ARCH_M68K,KORONOS_CPU_CISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"m68k","vector table/autovectors (not ported)","trap #0 (not ported)"},
 {KORONOS_ARCH_S390,KORONOS_CPU_CISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"s390x","lowcore interruption classes (not ported)","SVC (not ported)"},
 {KORONOS_ARCH_ALPHA,KORONOS_CPU_CISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"Alpha","PALcode vectors (not ported)","callsys (not ported)"},
 {KORONOS_ARCH_AARCH64,KORONOS_CPU_RISC,KORONOS_BACKEND_PORT_SKELETON,1,0,0,0,"arm64","EL vectors/GIC not implemented","SVC not implemented"},
 {KORONOS_ARCH_ARM,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"arm","IRQ/FIQ controller not ported","SVC (not ported)"},
 {KORONOS_ARCH_RISCV64,KORONOS_CPU_RISC,KORONOS_BACKEND_PORT_SKELETON,1,0,0,0,"riscv64","stvec/PLIC or APLIC+IMSIC not implemented","ECALL/SRET not implemented"},
 {KORONOS_ARCH_RISCV32,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"riscv32","stvec/PLIC not ported","ECALL/SRET not ported"},
 {KORONOS_ARCH_POWERPC,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"powerpc64","exception vectors/XICS/XIVE not ported","sc (not ported)"},
 {KORONOS_ARCH_MIPS,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"mips","CP0 vectors (not ported)","syscall (not ported)"},
 {KORONOS_ARCH_SPARC,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"sparc64","trap table (not ported)","ta (not ported)"},
 {KORONOS_ARCH_LOONGARCH,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"loongarch64","EENTRY/ESTAT (not ported)","SYSCALL (not ported)"},
 {KORONOS_ARCH_ARC,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"ARC","exception vectors/IRQ controller not ported","trap0 (not ported)"},
 {KORONOS_ARCH_OPENRISC,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"OpenRISC","exception vectors/PIC not ported","l.sys (not ported)"},
 {KORONOS_ARCH_PARISC,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"PA-RISC","processor vectors (not ported)","gateway (not ported)"},
 {KORONOS_ARCH_NIOS2,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"Nios II","exception vector/controller not ported","trap (not ported)"},
 {KORONOS_ARCH_MICROBLAZE,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"MicroBlaze","exception vector/controller not ported","brki (not ported)"},
 {KORONOS_ARCH_XTENSA,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"Xtensa","configurable interrupt levels not ported","syscall (not ported)"},
 {KORONOS_ARCH_SUPERH,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"SuperH","exception vectors/priority IRQs not ported","trapa #31 (not ported)"},
 {KORONOS_ARCH_CSKY,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"C-SKY","exception vectors/controller not ported","TRAP0 (not ported)"},
 {KORONOS_ARCH_HEXAGON,KORONOS_CPU_RISC,KORONOS_BACKEND_REFERENCE_ONLY,0,0,0,0,"Hexagon","vectored exceptions/interrupts not ported","trap0 #1 (not ported)"}
};
}
extern "C" const koronos_arch_backend *koronos_arch_backend_lookup(uint32_t architecture) {
 for(const auto &backend:k_backends) if(backend.architecture==architecture) return &backend;
 return nullptr;
}
extern "C" uint32_t koronos_arch_backend_count(void) {
 return static_cast<uint32_t>(sizeof(k_backends)/sizeof(k_backends[0]));
}
extern "C" const koronos_arch_backend *koronos_arch_backend_at(uint32_t index) {
 return index<koronos_arch_backend_count()?&k_backends[index]:nullptr;
}
