#if defined(_MSC_VER)
#include <intrin.h>
#ifndef __sync_lock_test_and_set
#define __sync_lock_test_and_set(ptr, value) _InterlockedExchange(reinterpret_cast<volatile long *>(ptr), static_cast<long>(value))
#define __sync_lock_release(ptr) ((void)_InterlockedExchange(reinterpret_cast<volatile long *>(ptr), 0L))
#endif
#endif
#include "chimera/dpc.h"

namespace {
struct Dpc { chimera_dpc_callback callback; void*context; uint32_t id; uint8_t queued,cancelled; };
Dpc queue[CHIMERA_DPC_MAX]; volatile uint32_t lock_word=0; uint32_t next_id=1;
static void lock(){while(__sync_lock_test_and_set(&lock_word,1u)){}}
static void unlock(){__sync_lock_release(&lock_word);}
}
extern "C" int chimera_dpc_init(void){lock();for(uint32_t i=0;i<CHIMERA_DPC_MAX;++i)queue[i]={};next_id=1;unlock();return 0;}
extern "C" int chimera_dpc_queue(chimera_dpc_callback cb,void*ctx,chimera_dpc_id*out){
 if(!cb||!out)return-1;
 lock();
 for(uint32_t i=0;i<CHIMERA_DPC_MAX;++i){
  if(!queue[i].queued){
   queue[i]={cb,ctx,next_id++,1,0};
   *out=queue[i].id;
   unlock();
   return 0;
  }
 }
 unlock();
 return-2;
}
extern "C" int chimera_dpc_cancel(chimera_dpc_id id){if(!id)return-1;lock();for(uint32_t i=0;i<CHIMERA_DPC_MAX;++i)if(queue[i].queued&&queue[i].id==id){queue[i].cancelled=1;queue[i].queued=0;unlock();return 0;}unlock();return-2;}
extern "C" uint32_t chimera_dpc_run(uint32_t budget){uint32_t done=0;while(done<budget){chimera_dpc_callback cb=0;void*ctx=0;chimera_dpc_id id=0;lock();for(uint32_t i=0;i<CHIMERA_DPC_MAX;++i)if(queue[i].queued&&!queue[i].cancelled){id=queue[i].id;cb=queue[i].callback;ctx=queue[i].context;queue[i].queued=0;break;}unlock();if(!cb)break;cb(id,ctx);++done;}return done;}
extern "C" uint32_t chimera_dpc_pending(void){uint32_t n=0;lock();for(uint32_t i=0;i<CHIMERA_DPC_MAX;++i)n+=queue[i].queued?1u:0u;unlock();return n;}
