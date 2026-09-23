#pragma once
#include <cstdint>
#include <string>
#include <vector>
namespace chimera::arch {
enum class HostISA { X86_64_CISC, ARM64_RISC, RISCV64_RISC, Unknown };
struct HostCapabilities { HostISA isa{HostISA::Unknown}; unsigned hardware_threads{}; bool simd{}; bool vector{}; bool crypto{}; };
HostCapabilities detect_host_isa();
class CanonicalExecutor {
public:
 virtual ~CanonicalExecutor()=default;
 virtual HostISA isa() const noexcept=0;
 virtual void execute(const std::vector<std::uint8_t>& canonical_uops)=0;
};
}
