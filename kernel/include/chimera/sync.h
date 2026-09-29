#pragma once
#include <stdint.h>
#include "chimera/thread.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_SYNC_MAX_WAITERS 32u
#define CHIMERA_WAIT_INFINITE 0xffffffffu

typedef enum {
    CHIMERA_WAIT_FAILED = -1,
    CHIMERA_WAIT_SIGNALED = 0,
    CHIMERA_WAIT_TIMEOUT = 1,
    CHIMERA_WAIT_BLOCKED = 2,
    CHIMERA_WAIT_ALERTED = 3
} chimera_wait_result;

typedef enum {
    CHIMERA_WAITABLE_EVENT = 1,
    CHIMERA_WAITABLE_MUTEX = 2,
    CHIMERA_WAITABLE_SEMAPHORE = 3
} chimera_waitable_type;

typedef struct {
    uint32_t thread_id;
    uint8_t active;
} chimera_waiter;

typedef struct {
    chimera_waitable_type type;
    volatile uint32_t lock_word;
    uint32_t signaled;
    uint32_t manual_reset;
    uint32_t owner_thread;
    uint32_t recursion;
    uint32_t count;
    uint32_t limit;
    chimera_waiter waiters[CHIMERA_SYNC_MAX_WAITERS];
} chimera_waitable;

void chimera_event_init(chimera_waitable *event, uint32_t manual_reset, uint32_t initial_state);
int chimera_event_set(chimera_waitable *event);
int chimera_event_reset(chimera_waitable *event);
int chimera_mutex_init(chimera_waitable *mutex);
int chimera_mutex_release(chimera_waitable *mutex);
int chimera_semaphore_init(chimera_waitable *semaphore, uint32_t initial_count, uint32_t maximum_count);
int chimera_semaphore_release(chimera_waitable *semaphore, uint32_t release_count, uint32_t *previous_count);

chimera_wait_result chimera_wait_one(chimera_waitable *object, uint32_t timeout_ticks, uint32_t alertable);
chimera_wait_result chimera_wait_register(chimera_waitable *object, uint32_t timeout_ticks, uint32_t alertable);
int chimera_wait_cancel(chimera_waitable *object, chimera_thread_id thread_id);
uint32_t chimera_waiter_count(const chimera_waitable *object);

#ifdef __cplusplus
}
#endif
