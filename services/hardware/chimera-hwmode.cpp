#include "chimera/hardware.h"
#include "chimera/nbit.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fstream>

static const char *policy_path() {
    if (const char *p = getenv("CHIMERA_NBIT_POLICY"); p && *p) return p;
    return "/etc/chimera/nbit-policy.conf";
}

static const char *arch_name(chimera_architecture a) {
    switch (a) {
        case CHIMERA_ARCH_X86_64: return "x86-64";
        case CHIMERA_ARCH_AARCH64: return "aarch64";
        case CHIMERA_ARCH_RISCV64: return "riscv64";
        default: return "unknown";
    }
}

int main(int argc, char **argv) {
    chimera_nbit_init();
    chimera_hardware_profile p{};
    chimera_hardware_probe(&p);

    if (argc == 1 || !strcmp(argv[1], "show")) {
        uint32_t def = 0;
        chimera_nbit_get_default(&def);
        printf("architecture=%s\nlogical_cpus=%u\nnative_bits=%u\nbest_bits=%u\nmax_emulated_bits=%u\nfeatures=0x%llx\ncompatibility=0x%x\ndefault_bits=%u\n",
               arch_name(p.architecture), p.logical_cpus, p.native_nbit_mode, p.best_nbit_mode,
               p.maximum_emulated_nbit, (unsigned long long)p.feature_bits, p.compatibility_mask, def);
        return 0;
    }

    if (!strcmp(argv[1], "best")) {
        printf("%u\n", p.best_nbit_mode);
        return 0;
    }

    if (!strcmp(argv[1], "set") && argc >= 3) {
        uint32_t bits = 0;
        const bool automatic = !strcmp(argv[2], "auto");
        bits = automatic ? p.best_nbit_mode : (uint32_t)strtoul(argv[2], nullptr, 10);
        int rc = chimera_nbit_set_default(bits);
        if (!rc) {
            std::ofstream f(policy_path());
            if (!f) {
                fprintf(stderr, "warning: runtime mode applied but policy file could not be written: %s\n", policy_path());
            } else {
                f << "mode=" << bits << "\n";
                f << "selection=" << (automatic ? "auto" : "manual") << "\n";
            }
        }
        printf("set-default=%u rc=%d policy=%s\n", bits, rc, policy_path());
        return rc ? 1 : 0;
    }

    fprintf(stderr, "usage: %s [show|best|set N|set auto]\n", argv[0]);
    return 2;
}
