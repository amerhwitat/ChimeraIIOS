#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_SERVICE_ABI 0x00010000u
#define CHIMERA_SERVICE_MAX 64u

typedef enum chimera_service_state {
  CHM_SVC_DECLARED=0, CHM_SVC_BLOCKED=1, CHM_SVC_STARTING=2, CHM_SVC_RUNNING=3,
  CHM_SVC_STOPPING=4, CHM_SVC_STOPPED=5, CHM_SVC_FAILED=6, CHM_SVC_RECOVERING=7
} chimera_service_state;
typedef enum chimera_service_restart {
  CHM_RESTART_NEVER=0, CHM_RESTART_FAILURE=1
} chimera_service_restart;

typedef struct chimera_service_manifest {
  uint32_t abi_version;
  const char* id;
  uint32_t state;
  uint32_t restart;
  uint8_t critical;
  uint8_t dependency_count;
  const char* const* dependencies;
} chimera_service_manifest;

typedef struct chimera_service_plan {
  uint32_t count;
  uint32_t capacity;
  const char** ordered_ids;
} chimera_service_plan;

/*
 * The supervisor is deliberately backend-neutral. The backend must connect
 * these callbacks to real process/service operations; tests may supply a
 * deterministic fake backend. No callback result is inferred from registration.
 *
 * start: 0 on successful spawn/activation and writes a nonzero handle.
 * probe: 1 healthy, 0 still starting, negative on failure.
 * wait_exit: 0 still running, 1 exited (writes exit_code), negative on error.
 * stop: 0 after successful stop/reap, negative on failure.
 * sleep_ticks: bounded scheduler/timer wait; may be null only when all wait
 * limits and backoffs are zero.
 */
typedef struct chimera_service_backend {
  int (*start)(const char* id, uint64_t* handle, void* context);
  int (*probe)(const char* id, uint64_t handle, void* context);
  int (*wait_exit)(const char* id, uint64_t handle, int* exit_code, void* context);
  int (*stop)(const char* id, uint64_t handle, void* context);
  void (*sleep_ticks)(uint32_t ticks, void* context);
  void* context;
} chimera_service_backend;

typedef struct chimera_service_supervisor_config {
  uint32_t health_timeout_ticks;
  uint32_t health_poll_ticks;
  uint32_t restart_backoff_ticks;
  uint32_t max_restarts;
} chimera_service_supervisor_config;

int chimera_service_validate(const chimera_service_manifest* services, uint32_t count);
int chimera_service_resolve(const chimera_service_manifest* services, uint32_t count, chimera_service_plan* plan);
int chimera_service_set_state(const char* id, uint32_t state);
uint32_t chimera_service_get_state(const char* id);
void chimera_kore_bootstrap(void);

/* Start in dependency order; critical failure rolls back already-started services. */
int chimera_service_supervisor_start(const chimera_service_manifest* services,
                                     uint32_t count,
                                     const chimera_service_backend* backend,
                                     const chimera_service_supervisor_config* config);
/* Nonblocking monitor step: observes exits and applies the bounded restart policy. */
int chimera_service_supervisor_poll(void);
/* Stop in reverse dependency order. All started services are attempted. */
int chimera_service_supervisor_stop(void);
uint32_t chimera_service_supervisor_count(void);

#ifdef __cplusplus
}
#endif
