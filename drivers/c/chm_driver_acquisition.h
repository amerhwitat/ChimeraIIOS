#ifndef CHM_DRIVER_ACQUISITION_H
#define CHM_DRIVER_ACQUISITION_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    CHM_DRIVER_LINUX = 1,
    CHM_DRIVER_WINDOWS = 2
} chm_driver_platform_t;

typedef enum {
    CHM_ACQUIRE_REJECTED = 0,
    CHM_ACQUIRE_VERIFIED = 1,
    CHM_ACQUIRE_STAGED = 2
} chm_acquisition_state_t;

typedef struct {
    const char *bus;
    const char *vendor;
    const char *device;
    const char *subsystem;
} chm_hardware_id_t;

typedef struct {
    const char *name;
    const char *url;
    const char *sha256_hex;
    const char *license_spdx;
    const char *kernel_abi;
    chm_driver_platform_t platform;
    uint8_t signed_artifact;
} chm_driver_artifact_t;

typedef struct {
    const char *kernel_abi;
    uint8_t require_signature;
} chm_acquisition_policy_t;

chm_acquisition_state_t chm_validate_driver_artifact(
    const chm_driver_artifact_t *artifact,
    const chm_acquisition_policy_t *policy);

#ifdef __cplusplus
}
#endif

#endif
