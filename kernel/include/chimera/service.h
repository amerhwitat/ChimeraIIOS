#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_SERVICE_ABI 0x00010000u

enum chimera_service_state : uint32_t {
  CHM_SVC_DECLARED=0, CHM_SVC_BLOCKED=1, CHM_SVC_STARTING=2, CHM_SVC_RUNNING=3,
  CHM_SVC_STOPPING=4, CHM_SVC_STOPPED=5, CHM_SVC_FAILED=6, CHM_SVC_RECOVERING=7
};
enum chimera_service_restart : uint32_t { CHM_RESTART_NEVER=0, CHM_RESTART_FAILURE=1 };
struct chimera_service_manifest {
  uint32_t abi_version; const char* id; uint32_t state; uint32_t restart;
  uint8_t critical; uint8_t dependency_count; const char* const* dependencies;
};
/* The array slots are writable; the strings they point to remain immutable. */
struct chimera_service_plan { uint32_t count; uint32_t capacity; const char** ordered_ids; };
/* A service is RUNNING only after both callbacks return zero. These callbacks
 * must perform real work; absent callbacks are an error, never a readiness
 * shortcut. The health callback must independently inspect service health. */
typedef int (*chimera_service_start_fn)(const chimera_service_manifest*, void*);
typedef int (*chimera_service_health_fn)(const chimera_service_manifest*, void*);
struct chimera_service_ops {
  chimera_service_start_fn start;
  chimera_service_health_fn health;
};
struct chimera_service_report {
  uint32_t attempted;
  uint32_t ready;
  uint32_t failed;
  uint32_t blocked;
  const char* failed_service;
};
int chimera_service_validate(const chimera_service_manifest* services, uint32_t count);
int chimera_service_resolve(const chimera_service_manifest* services, uint32_t count, chimera_service_plan* plan);
int chimera_service_start_graph(const chimera_service_manifest* services, uint32_t count,
                                const chimera_service_ops* ops, void* context,
                                chimera_service_report* report);
int chimera_service_set_state(const char* id, uint32_t state);
uint32_t chimera_service_get_state(const char* id);
void chimera_kore_bootstrap(void);
#ifdef __cplusplus
}
#endif
