#ifndef CHIMERA_H
#define CHIMERA_H
#include <stddef.h>
#include <stdint.h>
#ifdef _WIN32
#include <windows.h>
typedef CRITICAL_SECTION ChimeraMutex;
static inline int chimera_mutex_init(ChimeraMutex*m){InitializeCriticalSection(m);return 0;}
static inline void chimera_mutex_destroy(ChimeraMutex*m){DeleteCriticalSection(m);}
static inline void chimera_mutex_lock(ChimeraMutex*m){EnterCriticalSection(m);}
static inline void chimera_mutex_unlock(ChimeraMutex*m){LeaveCriticalSection(m);}
#else
#include <pthread.h>
typedef pthread_mutex_t ChimeraMutex;
static inline int chimera_mutex_init(ChimeraMutex*m){return pthread_mutex_init(m,NULL);}
static inline void chimera_mutex_destroy(ChimeraMutex*m){(void)pthread_mutex_destroy(m);}
static inline void chimera_mutex_lock(ChimeraMutex*m){(void)pthread_mutex_lock(m);}
static inline void chimera_mutex_unlock(ChimeraMutex*m){(void)pthread_mutex_unlock(m);}
#endif
#define CHIMERA_MAX_CPUS 8
#define CHIMERA_MAX_REGS 8
#define CHIMERA_MAX_NODES 32
#define CHIMERA_MAX_EDGES 64
#define CHIMERA_MEMORY_SIZE 4096
#define CHIMERA_REG_BYTES 1024
#define CHIMERA_JSON_MAX 32768
typedef enum { CHIMERA_PAUSED=0, CHIMERA_RUNNING=1 } ChimeraRunState;
typedef struct { uint8_t bytes[CHIMERA_REG_BYTES]; } ChimeraReg8192;
typedef struct { uint32_t id; uint64_t pc; uint64_t instructions; uint8_t halted; ChimeraReg8192 regs[CHIMERA_MAX_REGS]; } ChimeraCPU;
typedef struct { uint16_t from,to; uint32_t packets; } ChimeraEdge;
typedef struct { uint32_t node_count,edge_count; ChimeraEdge edges[CHIMERA_MAX_EDGES]; uint32_t activity[CHIMERA_MAX_NODES]; } ChimeraBrain;
typedef struct { ChimeraCPU cpus[CHIMERA_MAX_CPUS]; uint32_t cpu_count; uint8_t memory[CHIMERA_MEMORY_SIZE]; uint64_t ticks,messages_sent,messages_delivered; uint32_t scheduler_cursor; ChimeraRunState run_state; ChimeraBrain brain; ChimeraMutex lock; } ChimeraState;
int chimera_init(ChimeraState*,uint32_t,uint32_t);
void chimera_destroy(ChimeraState*);
void chimera_reset(ChimeraState*);
int chimera_step(ChimeraState*);
int chimera_control(ChimeraState*,const char*);
int chimera_state_json(ChimeraState*,char*,size_t);
#endif
