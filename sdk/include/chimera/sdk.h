#pragma once
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_SDK_VERSION_MAJOR 1
#define CHIMERA_SDK_VERSION_MINOR 0
const char* chimera_sdk_version(void);
const char* chimera_target_triple(void);
int chimera_runtime_init(void);
void chimera_runtime_shutdown(void);
#ifdef __cplusplus
}
#endif
