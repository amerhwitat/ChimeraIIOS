#ifndef CHIMERA_EVENT_H
#define CHIMERA_EVENT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHM_EVENT_ABI 1u
#define CHM_EVENT_QUEUE_CAPACITY 256u

typedef uint64_t chm_handle;
typedef enum chm_event_type {
    CHM_EVENT_NONE = 0,
    CHM_EVENT_QUIT = 1,
    CHM_EVENT_WINDOW_CREATE = 2,
    CHM_EVENT_WINDOW_CLOSE = 3,
    CHM_EVENT_KEY_DOWN = 4,
    CHM_EVENT_KEY_UP = 5,
    CHM_EVENT_POINTER_MOVE = 6,
    CHM_EVENT_POINTER_DOWN = 7,
    CHM_EVENT_POINTER_UP = 8,
    CHM_EVENT_TIMER = 9,
    CHM_EVENT_FILE_CHANGED = 10,
    CHM_EVENT_IO_READY = 11,
    CHM_EVENT_USER = 0x1000
} chm_event_type;

typedef struct chm_event {
    uint32_t size;
    uint32_t type;
    uint64_t timestamp_ns;
    chm_handle target;
    int64_t value1;
    int64_t value2;
    uintptr_t payload;
} chm_event;

typedef struct chm_event_queue chm_event_queue;
typedef void (*chm_event_handler)(const chm_event *event, void *context);

/* Thread-safe user-space event queue. timeout_ms: 0 polls, UINT32_MAX waits. */
chm_event_queue *chm_event_queue_create(size_t capacity);
void chm_event_queue_destroy(chm_event_queue *queue);
int chm_event_post(chm_event_queue *queue, const chm_event *event);
int chm_event_next(chm_event_queue *queue, chm_event *out, uint32_t timeout_ms);
int chm_event_run(chm_event_queue *queue, chm_event_handler handler,
                  void *context, uint32_t idle_timeout_ms);
void chm_event_stop(chm_event_queue *queue);

/* Small message-pump compatibility helpers for Win32-shaped source ports. */
typedef chm_event CHM_MSG;
int CHM_PostMessage(chm_event_queue *queue, chm_handle target,
                    uint32_t type, int64_t value1, int64_t value2);
int CHM_GetMessage(chm_event_queue *queue, CHM_MSG *out, uint32_t timeout_ms);
int CHM_DispatchMessage(const CHM_MSG *message, chm_event_handler handler,
                        void *context);

#ifdef __cplusplus
}
#endif
#endif
