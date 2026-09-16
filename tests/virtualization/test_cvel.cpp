#include "chimera/virtualization/cvel.h"
#include <cassert>
#include <iostream>

int main() {
    using namespace chimera::virtualization;
    Manager m;
    auto caps = m.detect_all();
    assert(caps.size() == 3);
    assert(Manager::supports_architecture(caps[0], "x86_64"));
    assert(Manager::supports_architecture(caps[0], "riscv64"));
    assert(!Manager::supports_architecture(caps[1], "riscv64"));

    assert(qemu_executable_for_architecture("x86_64") == "qemu-system-x86_64");
    assert(qemu_executable_for_architecture("x86") == "qemu-system-i386");
    assert(qemu_executable_for_architecture("arm") == "qemu-system-arm");
    assert(qemu_executable_for_architecture("aarch64") == "qemu-system-aarch64");
    assert(qemu_executable_for_architecture("riscv32") == "qemu-system-riscv32");
    assert(qemu_executable_for_architecture("riscv64") == "qemu-system-riscv64");
    assert(qemu_executable_for_architecture("mips") == "qemu-system-mips");
    assert(qemu_executable_for_architecture("mips64") == "qemu-system-mips64");
    assert(qemu_executable_for_architecture("ppc") == "qemu-system-ppc");
    assert(qemu_executable_for_architecture("ppc64") == "qemu-system-ppc64");
    assert(qemu_executable_for_architecture("sparc") == "qemu-system-sparc");
    assert(qemu_executable_for_architecture("chimera-c8192").empty());

    MachineProfile p{"chimera-test", "x86_64", "generic", 2048, "guest.img", "uefi", false, true};
    QemuBackend q;
    auto cmd = q.build_run_command(p, ExecutionMode::HardwareAssisted);
    assert(cmd.executable == "qemu-system-x86_64");
    assert(!cmd.arguments.empty());
    assert(cmd.arguments[cmd.arguments.size() - 2] == "-nic");
    assert(cmd.arguments.back() == "user");

    MachineProfile bios{"bios-test", "x86_64", "generic", 1024, "", "bios", true, false};
    auto bios_cmd = q.build_run_command(bios, ExecutionMode::Interpreter);
    for (const auto& arg : bios_cmd.arguments) assert(arg != "-bios");

    MachineProfile firmware{"firmware-test", "x86_64", "generic", 1024, "guest.img", "bios", true, false};
    firmware.firmware_path = "firmware.bin";
    auto firmware_cmd = q.build_run_command(firmware, ExecutionMode::Interpreter);
    bool found_bios = false;
    for (size_t i = 0; i + 1 < firmware_cmd.arguments.size(); ++i) {
        if (firmware_cmd.arguments[i] == "-bios") {
            found_bios = firmware_cmd.arguments[i + 1] == "firmware.bin";
        }
    }
    assert(found_bios);

    std::cout << "CVEL tests passed\n";
    return 0;
}
