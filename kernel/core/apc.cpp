#include "chimera/apc.h"
#include "chimera/sync.h"

namespace {
struct Queue { chimera_thread_id tid; chimera_apc_record entries[CHIMERA_APC_MAX_PER_THREAD]; };
Queue queues[1024]; volatile uint32_t lock_word=0;
static void lock(){while(__sync_lock_test_and_set(&lock_word,1u)){}}
static void unlock(){__sync_lock_release(&lock_word);}
static Queue* find(chimera_thread_id tid,bool create){ for(uint32_t i=0;i<1024;++i)if(queues[i].tid==tid)return &queues[i]; if(!create)return 0; for(uint32_t i=0;i<1024;++i)if(queues[i].tid==0){queues[i].tid=tid;return &queues[i];}return 0;}
}
extern "C" int chimera_apc_queue(chimera_thread_id tid,chimera_apc_callback cb,void*ctx){
 if(!tid||!cb)return-1; lock(); Queue*q=find(tid,true); if(!q){unlock();return-2;} for(uint32_t i=0;i<CHIMERA_APC_MAX_PER_THREAD;++i)if(!q->entries[i].queued){q->entries[i]={cb,ctx,1,1};unlock();chimera_thread_wake(tid);return 0;} unlock();return-3;
}
extern "C" uint32_t chimera_apc_pending(chimera_thread_id tid){uint32_t n=0;lock();Queue*q=find(tid,false);if(q)for(uint32_t i=0;i<CHIMERA_APC_MAX_PER_THREAD;++i)n+=q->entries[i].queued?1u:0u;unlock();return n;}
extern "C" uint32_t chimera_apc_deliver(chimera_thread_id tid,uint32_t alertable,uint32_t budget){
 if(!tid||!alertable)return 0;uint32_t done=0;
 while(done<budget){chimera_apc_callback cb=0;void*ctx=0;lock();Queue*q=find(tid,false);if(q)for(uint32_t i=0;i<CHIMERA_APC_MAX_PER_THREAD;++i)if(q->entries[i].queued){cb=q->entries[i].callback;ctx=q->entries[i].context;q->entries[i].queued=0;break;}unlock();if(!cb)break;cb(tid,ctx);++done;}return done;
}
extern "C" int chimera_apc_cancel_thread(chimera_thread_id tid){if(!tid)return-1;lock();Queue*q=find(tid,false);if(!q){unlock();return-2;}for(uint32_t i=0;i<CHIMERA_APC_MAX_PER_THREAD;++i)q->entries[i].queued=0;unlock();return 0;}
