#pragma once
#include <cstddef>
namespace chimera::performance {
enum class WorkloadClass { General, Compute, IO, Memory, AI, Database, Network };
struct HostProfile { unsigned hardware_threads{1}; unsigned recommended_workers{1}; bool native_build_target{true}; };
struct OptimizationHints { unsigned workers{1}; bool prefer_async_io{false}; bool prefer_zero_copy{false}; bool enable_host_cpu_target{true}; bool enable_bounded_telemetry{true}; const char* rationale{"conservative defaults"}; };
class Advisor { public: static HostProfile host_profile(unsigned hardware_threads) noexcept; static OptimizationHints suggest(WorkloadClass workload, unsigned hardware_threads) noexcept; static const char* workload_name(WorkloadClass workload) noexcept; };
} // namespace chimera::performance
