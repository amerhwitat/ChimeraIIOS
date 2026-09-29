#include "chimera/timer.h"
#include "chimera/thread.h"

namespace {
struct Timer { uint64_t due, period; chimera_timer_callback callback; void *context; uint8_t active; };
Timer timers[CHIMERA_TIMER_MAX];
volatile uint32_t lock_word=0;
uint64_t now_tick=0, next_id=1;
static void lock(){while(__sync_lock_test_and_set(&lock_word,1u)){}}
static void unlock(){__sync_lock_release(&lock_word);}
}
extern "C" int chimera_timer_init(void){ lock(); for(uint32_t i=0;i<CHIMERA_TIMER_MAX;++i) timers[i]={}; now_tick=0; next_id=1; unlock(); return 0; }
extern "C" int chimera_timer_create(uint64_t due,uint64_t period,chimera_timer_callback cb,void*ctx,chimera_timer_id*out){
 if(!cb||!out)return-1; lock(); for(uint32_t i=0;i<CHIMERA_TIMER_MAX;++i) if(!timers[i].active){ timers[i]={due,period,cb,ctx,1}; *out=(chimera_timer_id)(i+1); unlock(); return 0;} unlock(); return-2;
}
extern "C" int chimera_timer_cancel(chimera_timer_id id){ if(id==0||id>CHIMERA_TIMER_MAX)return-1; lock(); timers[id-1].active=0; unlock(); return 0; }
extern "C" uint64_t chimera_timer_now(void){return now_tick;}
extern "C" uint32_t chimera_timer_tick(uint32_t elapsed){
 uint32_t fired=0; for(uint32_t step=0;step<elapsed;++step){ ++now_tick;
  for(uint32_t i=0;i<CHIMERA_TIMER_MAX;++i){ lock(); Timer t=timers[i]; if(!t.active||t.due>now_tick){unlock();continue;}
   if(t.period) timers[i].due += t.period; else timers[i].active=0; unlock();
   t.callback((chimera_timer_id)(i+1),t.context); ++fired;
  }
 } return fired;
}
extern "C" uint32_t chimera_timer_active_count(void){uint32_t n=0;lock();for(uint32_t i=0;i<CHIMERA_TIMER_MAX;++i)n+=timers[i].active?1u:0u;unlock();return n;}
