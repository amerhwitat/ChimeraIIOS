#ifndef CHIMERA_CPU_PROFILE_H
#define CHIMERA_CPU_PROFILE_H
#include <stdint.h>

typedef enum { CHM_ARCH_UNKNOWN=0, CHM_ARCH_X86_64, CHM_ARCH_ARM64, CHM_ARCH_RISCV64, CHM_ARCH_CORTEX_M, CHM_ARCH_CHIMERA_R8192, CHM_ARCH_CHIMERA_C8192 } chm_arch_t;
typedef enum { CHM_ENC_FIXED=0, CHM_ENC_VARIABLE=1, CHM_ENC_HYBRID=2 } chm_encoding_t;
typedef struct {
    uint32_t arch;
    uint32_t encoding;
    uint16_t gpr_bits;
    uint16_t vector_bits;
    uint32_t lanes;
    uint64_t features;
    uint8_t endian;
    uint8_t firmware_mode;
    uint16_t reserved;
} chm_cpu_profile_t;
#endif
