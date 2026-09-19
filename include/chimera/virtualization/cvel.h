#pragma once
#include <string>
#include <vector>
#include <cstdint>

namespace chimera::virtualization {

enum class Provider { Qemu, VirtualBox, VMware, Native };
enum class ExecutionMode { Interpreter, Jit, HardwareAssisted, Native };

struct MachineProfile {
    std::string name;
    std::string architecture;
    std::string cpu;
    uint64_t memory_mib{1024};
    std::string disk_image;
    std::string firmware{"uefi"};
    bool graphics{true};
    bool networking{true};
    std::string firmware_path;
};

struct Capability {
    Provider provider;
    bool installed{false};
    std::string executable;
    std::string version;
    std::vector<std::string> architectures;
};

struct CommandLine {
    std::string executable;
    std::vector<std::string> arguments;
};

class Backend {
public:
    virtual ~Backend() = default;
    virtual Capability detect() const = 0;
    virtual CommandLine build_run_command(const MachineProfile&, ExecutionMode) const = 0;
    virtual const char* name() const = 0;
};

class QemuBackend final : public Backend {
public:
    Capability detect() const override;
    CommandLine build_run_command(const MachineProfile&, ExecutionMode) const override;
    const char* name() const override { return "qemu"; }
};

class VirtualBoxBackend final : public Backend {
public:
    Capability detect() const override;
    CommandLine build_run_command(const MachineProfile&, ExecutionMode) const override;
    const char* name() const override { return "virtualbox"; }
};

class VMwareBackend final : public Backend {
public:
    Capability detect() const override;
    CommandLine build_run_command(const MachineProfile&, ExecutionMode) const override;
    const char* name() const override { return "vmware"; }
};

class Manager {
public:
    std::vector<Capability> detect_all() const;
    static bool supports_architecture(const Capability&, const std::string& architecture);
};

std::string qemu_executable_for_architecture(const std::string& architecture);
std::string command_to_string(const CommandLine&);

} // namespace chimera::virtualization
