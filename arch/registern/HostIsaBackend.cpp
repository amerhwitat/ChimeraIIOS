#include "HostIsaBackend.h"
#include <thread>
#if defined(__x86_64__) || defined(_M_X64)
#define CH_X86 1
#elif defined(__aarch64__) || defined(_M_ARM64)
#define CH_ARM64 1
#elif defined(__riscv)
#define CH_RISCV 1
#endif
namespace chimera::arch {
HostCapabilities detect_host_isa(){
 HostCapabilities c{}; c.hardware_threads=std::thread::hardware_concurrency();
#if CH_X86
 c.isa=HostISA::X86_64_CISC;c.simd=true;c.vector=true;c.crypto=true;
#elif CH_ARM64
 c.isa=HostISA::ARM64_RISC;c.simd=true;c.vector=true;c.crypto=true;
#elif CH_RISCV
 c.isa=HostISA::RISCV64_RISC;c.vector=true;
#endif
 return c;
}
}
