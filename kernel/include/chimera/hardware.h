#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_HW_PROFILE_VERSION 1u
#define CHIMERA_NBIT_MODE_COUNT 11u

typedef enum chimera_architecture {
    CHIMERA_ARCH_UNKNOWN = 0,
    CHIMERA_ARCH_X86_64 = 1,
    CHIMERA_ARCH_AARCH64 = 2,
    CHIMERA_ARCH_RISCV64 = 3
} chimera_architecture;

typedef enum chimera_nbit_mode {
    CHIMERA_NBIT_8 = 8,
    CHIMERA_NBIT_16 = 16,
    CHIMERA_NBIT_32 = 32,
    CHIMERA_NBIT_64 = 64,
    CHIMERA_NBIT_128 = 128,
    CHIMERA_NBIT_256 = 256,
    CHIMERA_NBIT_512 = 512,
    CHIMERA_NBIT_1024 = 1024,
    CHIMERA_NBIT_2048 = 2048,
    CHIMERA_NBIT_4096 = 4096,
    CHIMERA_NBIT_8192 = 8192
} chimera_nbit_mode;

enum {
    CHIMERA_HW_SSE2 = 1u << 0,
    CHIMERA_HW_AVX = 1u << 1,
    CHIMERA_HW_AVX2 = 1u << 2,
    CHIMERA_HW_AVX512 = 1u << 3,
    CHIMERA_HW_AES = 1u << 4,
    CHIMERA_HW_RDRAND = 1u << 5,
    CHIMERA_HW_VMX = 1u << 6,
    CHIMERA_HW_SVM = 1u << 7,
    CHIMERA_HW_NEON = 1u << 8,
    CHIMERA_HW_SVE = 1u << 9
};

typedef struct chimera_hardware_profile {
    uint32_t version;
    chimera_architecture architecture;
    uint32_t logical_cpus;
    uint32_t physical_address_bits;
    uint32_t virtual_address_bits;
    uint32_t native_pointer_bits;
    uint32_t native_nbit_mode;
    uint32_t best_nbit_mode;
    uint32_t maximum_emulated_nbit;
    uint64_t feature_bits;
    uint32_t compatibility_mask;
    char vendor[32];
    char model[96];
} chimera_hardware_profile;

typedef enum chimera_compatibility_target {
    CHIMERA_COMPAT_NATIVE = 1u << 0,
    CHIMERA_COMPAT_WINDOWS = 1u << 1,
    CHIMERA_COMPAT_LINUX = 1u << 2,
    CHIMERA_COMPAT_BSD = 1u << 3,
    CHIMERA_COMPAT_DARWIN = 1u << 4,
    CHIMERA_COMPAT_ANDROID = 1u << 5,
    CHIMERA_COMPAT_IOS = 1u << 6
} chimera_compatibility_target;

int chimera_hardware_probe(chimera_hardware_profile *out);
int chimera_hardware_best_mode(const chimera_hardware_profile *profile);
int chimera_hardware_supports_mode(const chimera_hardware_profile *profile, uint32_t bits);
uint32_t chimera_hardware_compatibility_mask(const chimera_hardware_profile *profile);

#ifdef __cplusplus
}
#endif
