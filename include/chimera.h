#ifndef CHIMERA_H
#define CHIMERA_H

#include <stddef.h>
#include <stdint.h>
#include <pthread.h>

#define CHIMERA_MAX_CPUS 8
#define CHIMERA_MAX_REGS 8
#define CHIMERA_MAX_NODES 32
#define CHIMERA_MAX_EDGES 64
#define CHIMERA_MEMORY_SIZE 4096
#define CHIMERA_REG_BYTES 1024
#define CHIMERA_JSON_MAX 32768

typedef enum { CHIMERA_PAUSED = 0, CHIMERA_RUNNING = 1 } ChimeraRunState;
typedef struct { uint8_t bytes[CHIMERA_REG_BYTES]; } ChimeraReg8192;
typedef struct { uint32_t id; uint64_t pc; uint64_t instructions; uint8_t halted; ChimeraReg8192 regs[CHIMERA_MAX_REGS]; } ChimeraCPU;
typedef struct { uint16_t from, to; uint32_t packets; } ChimeraEdge;
typedef struct { uint32_t node_count; uint32_t edge_count; ChimeraEdge edges[CHIMERA_MAX_EDGES]; uint32_t activity[CHIMERA_MAX_NODES]; } ChimeraBrain;
typedef struct { ChimeraCPU cpus[CHIMERA_MAX_CPUS]; uint32_t cpu_count; uint8_t memory[CHIMERA_MEMORY_SIZE]; uint64_t ticks; uint64_t messages_sent; uint64_t messages_delivered; uint32_t scheduler_cursor; ChimeraRunState run_state; ChimeraBrain brain; pthread_mutex_t lock; } ChimeraState;
int chimera_init(ChimeraState *s, uint32_t cpu_count, uint32_t node_count);
void chimera_destroy(ChimeraState *s);
void chimera_reset(ChimeraState *s);
int chimera_step(ChimeraState *s);
int chimera_control(ChimeraState *s, const char *action);
int chimera_state_json(ChimeraState *s, char *out, size_t cap);
#endif
