#include "chimera/virtualization/cvel.h"
#include <algorithm>
#include <cstdlib>
#include <map>
#include <sstream>

namespace chimera::virtualization {
namespace {
bool command_exists(const char* cmd) {
#ifdef _WIN32
    std::string probe = "where "; probe += cmd;
#else
    std::string probe = "command -v "; probe += cmd;
#endif
    return std::system(probe.c_str()) == 0;
}
Capability capability(Provider p, const char* exe, std::vector<std::string> arch) {
    return Capability{p, command_exists(exe), exe, {}, std::move(arch)};
}
}

std::string qemu_executable_for_architecture(const std::string& architecture) {
    static const std::map<std::string, std::string> executables{
        {"x86", "qemu-system-i386"}, {"x86_64", "qemu-system-x86_64"},
        {"arm", "qemu-system-arm"}, {"aarch64", "qemu-system-aarch64"},
        {"riscv32", "qemu-system-riscv32"}, {"riscv64", "qemu-system-riscv64"},
        {"mips", "qemu-system-mips"}, {"mips64", "qemu-system-mips64"},
        {"ppc", "qemu-system-ppc"}, {"ppc64", "qemu-system-ppc64"},
        {"sparc", "qemu-system-sparc"}
    };
    const auto it = executables.find(architecture);
    return it == executables.end() ? std::string{} : it->second;
}

Capability QemuBackend::detect() const {
    return capability(Provider::Qemu, "qemu-system-x86_64", {"x86","x86_64","arm","aarch64","riscv32","riscv64","mips","mips64","ppc","ppc64","sparc"});
}
CommandLine QemuBackend::build_run_command(const MachineProfile& p, ExecutionMode) const {
    const std::string executable = qemu_executable_for_architecture(p.architecture);
    if (executable.empty()) return {"", {}};
    CommandLine c{executable, {"-m", std::to_string(p.memory_mib), "-name", p.name}};
    if (!p.disk_image.empty()) c.arguments.insert(c.arguments.end(), {"-drive", "file=" + p.disk_image + ",format=raw"});
    if (p.firmware == "bios" && !p.firmware_path.empty()) c.arguments.insert(c.arguments.end(), {"-bios", p.firmware_path});
    if (!p.graphics) c.arguments.push_back("-nographic");
    if (p.networking) c.arguments.insert(c.arguments.end(), {"-nic", "user"});
    return c;
}

Capability VirtualBoxBackend::detect() const { return capability(Provider::VirtualBox, "VBoxManage", {"x86","x86_64"}); }
CommandLine VirtualBoxBackend::build_run_command(const MachineProfile& p, ExecutionMode) const { return {"VBoxManage", {"startvm", p.name, "--type", p.graphics ? "gui" : "headless"}}; }
Capability VMwareBackend::detect() const { const char* exe = command_exists("vmrun") ? "vmrun" : "vmware-vmx"; return capability(Provider::VMware, exe, {"x86","x86_64"}); }
CommandLine VMwareBackend::build_run_command(const MachineProfile& p, ExecutionMode) const { if (p.disk_image.empty()) return {"vmrun", {"list"}}; return {"vmrun", {"start", p.disk_image, p.graphics ? "gui" : "nogui"}}; }
std::vector<Capability> Manager::detect_all() const { QemuBackend q; VirtualBoxBackend v; VMwareBackend w; return {q.detect(), v.detect(), w.detect()}; }
bool Manager::supports_architecture(const Capability& c, const std::string& architecture) { return std::find(c.architectures.begin(), c.architectures.end(), architecture) != c.architectures.end(); }
std::string command_to_string(const CommandLine& c) { std::ostringstream out; out << c.executable; for (const auto& a : c.arguments) out << ' ' << a; return out.str(); }
} // namespace chimera::virtualization
