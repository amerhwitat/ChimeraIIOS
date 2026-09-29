#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint32_t chimera_timer_id;
typedef void (*chimera_timer_callback)(chimera_timer_id id, void *context);

#define CHIMERA_TIMER_MAX 256u
#define CHIMERA_TIMER_INACTIVE 0u

int chimera_timer_init(void);
int chimera_timer_create(uint64_t due_tick, uint64_t period_ticks,
                         chimera_timer_callback callback, void *context,
                         chimera_timer_id *out_id);
int chimera_timer_cancel(chimera_timer_id id);
uint64_t chimera_timer_now(void);
uint32_t chimera_timer_tick(uint32_t elapsed_ticks);
uint32_t chimera_timer_active_count(void);

#ifdef __cplusplus
}
#endif
