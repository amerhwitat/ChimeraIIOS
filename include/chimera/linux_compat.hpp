#pragma once
#include <cstdint>
#include <string_view>
namespace chimera::linux_compat {
enum class Feature : std::uint16_t { Process,Scheduler,Signals,Futex,Rcu,Workqueues,Timers,MemoryManagement,Vm,HugePages,Swap,SlabAllocator,PageCache,Vfs,Filesystems,BlockIO,Dma,DeviceModel,Pci,Usb,Tty,Input,Sound,Graphics,Media,Networking,IPv4,IPv6,Tcp,Udp,Netfilter,Routing,Sockets,ZeroCopy,Ipc,Pipes,Epoll,IoUring,Syscalls,Elf,Modules,Namespaces,Cgroups,Seccomp,Lsm,Crypto,Random,Keyrings,Tracing,Ftrace,Perf,Bpf,Debugfs,Procfs,Sysfs,Firmware,Acpi,Devicetree,Uefi,PowerManagement,Suspend,CpuHotplug,Virtualization,Kvm,Kexec,KernelCompression,Livepatch,FaultInjection,Lockdep,Sanitizers,AtomicOps,MemoryBarriers,RiscV,Arm,Arm64,X86,X86_64,Power,Mips,Sparc,S390,Sh,M68k,Parisc,Alpha,Arc,Csky,Hexagon,LoongArch,Microblaze,Nios2,OpenRisc,Xtensa,Um };
struct FeatureDescriptor { Feature id; std::string_view name; std::string_view subsystem; bool kernel_api; bool arch_sensitive; };
struct ArchitectureProfile { std::string_view name; std::string_view family; bool risc; bool cisc; std::uint16_t pointer_bits; std::string_view linux_arch; };
struct CompatibilityReport { std::uint32_t abi_version{1}; std::uint64_t feature_count{},supported_count{},arch_count{}; bool syscall_layer{},elf_loader{},vfs_layer{},network_layer{},driver_model{},security_layer{},tracing_layer{},virtualization_layer{}; };
const FeatureDescriptor* feature_table(std::size_t& count) noexcept;
const ArchitectureProfile* architecture_table(std::size_t& count) noexcept;
bool supports(Feature feature) noexcept;
CompatibilityReport identify() noexcept;
std::string_view feature_name(Feature feature) noexcept;
}