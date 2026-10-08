#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_WATCHDOG_ABI 1u
#define CHIMERA_WATCHDOG_MAX 64u
#define CHIMERA_WATCHDOG_KORONOS 1u
#define CHIMERA_WATCHDOG_MICROKERNEL 2u
#define CHIMERA_WATCHDOG_KORE 3u
typedef enum chimera_watchdog_state { CHIMERA_WATCHDOG_EMPTY=0, CHIMERA_WATCHDOG_HEALTHY=1, CHIMERA_WATCHDOG_EXPIRED=2, CHIMERA_WATCHDOG_RECOVERING=3 } chimera_watchdog_state;
typedef struct chimera_watchdog_slot { uint32_t id,state; uint64_t timeout_ns,last_heartbeat_ns; uint32_t restart_count,reserved; } chimera_watchdog_slot;
int chimera_watchdog_init(uint64_t now_ns);
int chimera_watchdog_register(uint32_t id,uint64_t timeout_ns,uint64_t now_ns);
int chimera_watchdog_heartbeat(uint32_t id,uint64_t now_ns);
int chimera_watchdog_tick(uint64_t now_ns);
int chimera_watchdog_mark_recovering(uint32_t id,uint64_t now_ns);
int chimera_watchdog_get(uint32_t id,chimera_watchdog_slot *out);
uint32_t chimera_watchdog_expired_count(void);
uint32_t chimera_watchdog_restart_count(uint32_t id);
#ifdef __cplusplus
}
#endif
