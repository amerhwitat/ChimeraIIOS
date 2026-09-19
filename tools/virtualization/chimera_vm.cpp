#include "chimera/virtualization/cvel.h"
#include <iostream>
#include <string>

using namespace chimera::virtualization;

int main(int argc, char** argv) {
    Manager manager;
    if (argc < 2 || std::string(argv[1]) == "detect") {
        for (const auto& c : manager.detect_all()) {
            std::cout << c.executable << ": " << (c.installed ? "installed" : "not-found") << '\n';
        }
        return 0;
    }
    if (std::string(argv[1]) == "run" && argc >= 3) {
        MachineProfile p;
        p.name = argv[2];
        if (argc >= 4) p.disk_image = argv[3];
        QemuBackend q;
        auto cap = q.detect();
        if (!cap.installed) {
            std::cerr << "QEMU backend is not installed; command generation remains available.\n";
            return 2;
        }
        std::cout << command_to_string(q.build_run_command(p, ExecutionMode::HardwareAssisted)) << '\n';
        return 0;
    }
    std::cerr << "Usage: chimera_vm [detect | run <name> [disk-image]]\n";
    return 1;
}
