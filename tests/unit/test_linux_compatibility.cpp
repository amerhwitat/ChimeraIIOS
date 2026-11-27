#include "chimera/linux_compat.hpp"

#include <cassert>
#include <cstddef>

int main() {
    using chimera::linux_compat::Feature;
    using chimera::linux_compat::feature_table;
    using chimera::linux_compat::architecture_table;
    using chimera::linux_compat::identify;
    using chimera::linux_compat::supports;

    std::size_t feature_count = 0;
    std::size_t architecture_count = 0;
    assert(feature_table(feature_count) != nullptr);
    assert(architecture_table(architecture_count) != nullptr);
    assert(feature_count >= 80);
    assert(architecture_count >= 20);

    const auto report = identify();
    assert(report.abi_version == 1);
    assert(report.feature_count == feature_count);
    assert(report.arch_count == architecture_count);
    assert(report.supported_count == 0);

    // The Linux compatibility implementation is not complete. Architecture
    // catalogue entries and feature names must not be mistaken for support.
    assert(!report.syscall_layer);
    assert(!report.elf_loader);
    assert(!report.vfs_layer);
    assert(!report.network_layer);
    assert(!report.driver_model);
    assert(!report.security_layer);
    assert(!report.tracing_layer);
    assert(!report.virtualization_layer);

    assert(!supports(Feature::MemoryManagement));
    assert(!supports(Feature::X86_64));
    assert(!supports(Feature::RiscV));
    return 0;
}
