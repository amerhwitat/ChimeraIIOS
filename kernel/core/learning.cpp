#include "chimera/learning.h"
#include <stdint.h>
static volatile uint64_t g_events=0;
static volatile uint64_t g_steps=0;
static uint32_t g_cpus=1;
extern "C" void chimera_learning_init(uint32_t cpus){ g_cpus=cpus?cpus:1; g_events=0; g_steps=0; }
extern "C" void chimera_learning_record(uint32_t, int64_t){ ++g_events; }
extern "C" void chimera_learning_step(void){ ++g_steps; }
extern "C" const volatile uint64_t* chimera_learning_event_count(void){ return &g_events; }
