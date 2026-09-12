#include "../c/chm_driver_acquisition.h"
#include <string.h>

chm_acquisition_state_t chm_windows_validate_package(
    const chm_driver_artifact_t *artifact,
    const chm_acquisition_policy_t *policy) {
    if (!artifact || !policy || artifact->platform != CHM_DRIVER_WINDOWS) return CHM_ACQUIRE_REJECTED;
    if (!artifact->url || strncmp(artifact->url, "https://", 8) != 0) return CHM_ACQUIRE_REJECTED;
    if (!artifact->sha256_hex || strlen(artifact->sha256_hex) != 64) return CHM_ACQUIRE_REJECTED;
    if (policy->require_signature && !artifact->signed_artifact) return CHM_ACQUIRE_REJECTED;
    return CHM_ACQUIRE_VERIFIED;
}

/*
 * Installation is intentionally not performed here. On Windows, a verified
 * package should be handed to the platform Driver Store / SetupAPI path.
 * Chimera never disables signature enforcement to force a package to load.
 */
