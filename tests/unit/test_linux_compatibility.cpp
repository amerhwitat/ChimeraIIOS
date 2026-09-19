#include "chimera/linux_compat.hpp"
#include <cassert>
#include <cstddef>
int main(){std::size_t f=0,a=0;const auto*ft=chimera::linux_compat::feature_table(f);const auto*at=chimera::linux_compat::architecture_table(a);assert(ft&&f>=80);assert(at&&a>=20);auto r=chimera::linux_compat::identify();assert(r.feature_count==f&&r.arch_count==a);assert(r.syscall_layer&&r.elf_loader&&r.vfs_layer&&r.network_layer);assert(r.driver_model&&r.security_layer&&r.tracing_layer&&r.virtualization_layer);assert(chimera::linux_compat::supports(chimera::linux_compat::Feature::MemoryManagement));assert(chimera::linux_compat::supports(chimera::linux_compat::Feature::X86_64));assert(chimera::linux_compat::supports(chimera::linux_compat::Feature::RiscV));return 0;}
