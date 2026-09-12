#include "../c/chm_driver_acquisition.h"
#include <string.h>

static int hex_sha256_metadata(const char *s) {
    size_t i;
    if (!s || strlen(s) != 64) return 0;
    for (i = 0; i < 64; ++i) {
        const char c = s[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'))) return 0;
    }
    return 1;
}

chm_acquisition_state_t chm_validate_driver_artifact(
    const chm_driver_artifact_t *artifact,
    const chm_acquisition_policy_t *policy) {
    if (!artifact || !policy || !artifact->url || strncmp(artifact->url, "https://", 8) != 0) return CHM_ACQUIRE_REJECTED;
    if (!hex_sha256_metadata(artifact->sha256_hex)) return CHM_ACQUIRE_REJECTED;
    if (policy->require_signature && !artifact->signed_artifact) return CHM_ACQUIRE_REJECTED;
    if (artifact->platform == CHM_DRIVER_LINUX && artifact->kernel_abi) {
        if (!policy->kernel_abi || strcmp(artifact->kernel_abi, policy->kernel_abi) != 0) return CHM_ACQUIRE_REJECTED;
    }
    return CHM_ACQUIRE_VERIFIED;
}
