#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    KORE_UNIT_SERVICE = 0,
    KORE_UNIT_TARGET = 1
} kore_unit_type;
typedef enum {
    KORE_DEAD = 0,
    KORE_QUEUED = 1,
    KORE_STARTING = 2,
    KORE_RUNNING = 3,
    KORE_BLOCKED = 4,
    KORE_STOPPING = 5,
    KORE_STOPPED = 6,
    KORE_FAILED = 7
} kore_unit_state;

typedef void (*kore_service_fn)(void *arg);
typedef struct {
    uint32_t id;
    kore_unit_type type;
    kore_unit_state state;
    uint32_t priority;
    uint32_t wanted_by;
    uint32_t requires_count;
    uint32_t after_count;
    uint64_t runs;
    uint64_t last_error;
    const char *name;
    kore_service_fn start;
    void *arg;
} kore_unit_info;

void kore_init(uint32_t cpu_count);
int kore_register_service(const char *name, kore_service_fn start, void *arg, uint32_t priority);
int kore_register_target(const char *name, uint32_t priority);
int kore_add_wants(const char *target, const char *unit);
int kore_add_requires(const char *unit, const char *required);
int kore_add_after(const char *unit, const char *after);
int kore_start_target(const char *target);
uint32_t kore_dispatch(uint32_t budget);
uint32_t kore_running_count(void);
uint32_t kore_failed_count(void);
uint32_t kore_unit_count(void);
const kore_unit_info *kore_snapshot(uint32_t index);
void kore_print_status(void);

#ifdef __cplusplus
}
#endif
