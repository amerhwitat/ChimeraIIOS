#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
struct chimera_learning_event { uint64_t timestamp; uint32_t cpu; uint32_t action; int64_t value; };
void chimera_learning_init(uint32_t cpus);
void chimera_learning_record(uint32_t action, int64_t value);
void chimera_learning_step(void);
const volatile uint64_t* chimera_learning_event_count(void);
#ifdef __cplusplus
}
#endif
