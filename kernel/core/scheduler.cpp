#if defined(_MSC_VER)
#include <intrin.h>
#ifndef __sync_lock_test_and_set
#define __sync_lock_test_and_set(ptr, value) _InterlockedExchange(reinterpret_cast<volatile long *>(ptr), static_cast<long>(value))
#define __sync_lock_release(ptr) ((void)_InterlockedExchange(reinterpret_cast<volatile long *>(ptr), 0L))
#endif
#endif
#include "chimera/scheduler.h"
#if defined(KORONOS_FREESTANDING)
#include "chimera/frame_allocator.h"
#include "chimera/physmap.h"
#endif

namespace {
constexpr uint32_t MAX_CPUS=256,MAX_TASKS=1024;
#if defined(KORONOS_FREESTANDING)
constexpr uint32_t TASK_STACK_PAGES=4;
volatile uint64_t context_switches=0;
#endif
enum PendingAction : uint8_t { ACTION_NONE=0, ACTION_YIELD=1, ACTION_BLOCK=2, ACTION_EXIT=3 };
struct Task {
    chimera_task_fn fn=nullptr;
    void* arg=nullptr;
    chimera_task_info info{};
    uint32_t round_seen=0;
    uint8_t pending_action=ACTION_NONE;
    uint64_t saved_rsp=0;
    uint64_t stack_physical=0;
    uint32_t stack_pages=0;
};
Task tasks[MAX_TASKS];
uint32_t count=0,next_id=1,rr=0,dispatch_round=1,cpus=1,lock_word=0;
volatile int32_t current_index[MAX_CPUS];
#if defined(KORONOS_FREESTANDING)
uint64_t scheduler_rsp[MAX_CPUS];
extern "C" void koronos_context_switch(uint64_t *old_rsp,uint64_t new_rsp);
extern "C" void koronos_scheduler_task_trampoline(void);
#endif

static void lock(){while(__sync_lock_test_and_set(&lock_word,1u)){} }
static void unlock(){__sync_lock_release(&lock_word);}
static bool cpu_allowed(const chimera_task_info& info,uint32_t cpu){
    if(info.affinity_mask==0) return true;
    if(cpu>=64) return false;
    return (info.affinity_mask & (1ull<<cpu)) != 0;
}
static int32_t pick_next_locked(uint32_t cpu){
    if(count==0) return -1;
    int32_t best=-1; uint32_t best_priority=0;
    const uint32_t start=rr%count;
    bool found_unseen=false;
    for(uint32_t offset=0;offset<count;offset++){
        const uint32_t i=(start+offset)%count;
        const chimera_task_info& info=tasks[i].info;
        if(info.state!=CHIMERA_TASK_READY || !cpu_allowed(info,cpu)) continue;
        if(tasks[i].round_seen==dispatch_round) continue;
        found_unseen=true;
        if(best<0 || info.priority>best_priority){best=(int32_t)i;best_priority=info.priority;}
    }
    if(!found_unseen){
        ++dispatch_round;if(dispatch_round==0)dispatch_round=1;
        for(uint32_t i=0;i<count;i++) tasks[i].round_seen=0;
        for(uint32_t offset=0;offset<count;offset++){
            const uint32_t i=(start+offset)%count;
            const chimera_task_info& info=tasks[i].info;
            if(info.state!=CHIMERA_TASK_READY || !cpu_allowed(info,cpu)) continue;
            if(best<0 || info.priority>best_priority){best=(int32_t)i;best_priority=info.priority;}
        }
    }
    if(best>=0){tasks[(uint32_t)best].round_seen=dispatch_round;rr=((uint32_t)best+1u)%count;}
    return best;
}
#if defined(KORONOS_FREESTANDING)
static bool allocate_stack(Task *task,uint32_t index) {
    if(!task || !koronos_physmap_ready()) return false;
    const uint64_t physical=koronos_frame_alloc_contiguous(TASK_STACK_PAGES);
    if(!physical) return false;
    const uint64_t bytes=(uint64_t)TASK_STACK_PAGES*KORONOS_FRAME_SIZE;
    auto *base=static_cast<uint8_t*>(koronos_phys_to_virt(physical,bytes));
    if(!base) { (void)koronos_frame_free_contiguous(physical,TASK_STACK_PAGES); return false; }
    for(uint64_t i=0;i<bytes;i++) base[i]=0;
    uintptr_t top=(reinterpret_cast<uintptr_t>(base)+bytes)&~static_cast<uintptr_t>(0xFu);
    // Context-switch ABI: r15,r14,r13,r12,rbx,rbp,return-address,padding.
    // The trampoline enters with SysV RSP%16 == 8, as if called normally.
    uint64_t *frame=reinterpret_cast<uint64_t*>(top-9u*sizeof(uint64_t));
    frame[0]=0; frame[1]=0; frame[2]=0; frame[3]=index;
    frame[4]=0; frame[5]=0;
    frame[6]=0x2u; // RFLAGS reserved bit set; interrupts stay disabled for first entry.
    frame[7]=reinterpret_cast<uint64_t>(&koronos_scheduler_task_trampoline);
    frame[8]=0;
    task->saved_rsp=reinterpret_cast<uint64_t>(frame);
    task->stack_physical=physical;
    task->stack_pages=TASK_STACK_PAGES;
    return true;
}
static void release_stack(uint64_t physical,uint32_t pages) {
    if(physical && pages) (void)koronos_frame_free_contiguous(physical,pages);
}
#endif
static int request_action(uint32_t cpu, uint8_t action) {
    if(cpu>=cpus) return -1;
    lock();
    const int32_t i=current_index[cpu];
    if(i<0 || (uint32_t)i>=count || tasks[(uint32_t)i].info.state!=CHIMERA_TASK_RUNNING) {
        unlock();return -2;
    }
    Task &t=tasks[(uint32_t)i];
#if defined(KORONOS_FREESTANDING)
    if(!scheduler_rsp[cpu]) { unlock(); return -4; }
    t.info.state=(action==ACTION_EXIT)?CHIMERA_TASK_EXITED:
                 (action==ACTION_BLOCK)?CHIMERA_TASK_BLOCKED:CHIMERA_TASK_READY;
    t.pending_action=action;
    unlock();
    // Save this task's callee-saved register set and RSP; resume the scheduler
    // on its own bootstrap stack. This call returns only when this task is run again.
    __sync_fetch_and_add(&context_switches,1ull);
    koronos_context_switch(&t.saved_rsp,scheduler_rsp[cpu]);
    return 0;
#else
    /* Host contract tests exercise deterministic callback-boundary semantics.
       The freestanding kernel uses the stackful switch path above. */
    if(t.pending_action==ACTION_EXIT || t.pending_action==ACTION_BLOCK) {unlock();return -3;}
    if(action==ACTION_EXIT || action==ACTION_BLOCK || t.pending_action==ACTION_NONE)
        t.pending_action=action;
    unlock();return 0;
#endif
}
static void legacy_action(uint8_t action) {
    lock(); int32_t owner=-1; uint32_t active=0;
    for(uint32_t cpu=0;cpu<cpus;cpu++) if(current_index[cpu]>=0) {owner=(int32_t)cpu;++active;}
    unlock();
    if(active==1) (void)request_action((uint32_t)owner,action);
}
}
extern "C" void chimera_sched_init(uint32_t n){
    lock(); cpus=n?n:1;if(cpus>MAX_CPUS)cpus=MAX_CPUS;
    count=0;rr=0;dispatch_round=1;next_id=1;
#if defined(KORONOS_FREESTANDING)
    context_switches=0;
#endif
    for(uint32_t i=0;i<MAX_TASKS;i++) tasks[i]={};
    for(uint32_t i=0;i<MAX_CPUS;i++) {
        current_index[i]=-1;
#if defined(KORONOS_FREESTANDING)
        scheduler_rsp[i]=0;
#endif
    }
    unlock();
}
extern "C" uint32_t chimera_sched_cpu_count(){lock();uint32_t n=cpus;unlock();return n;}
extern "C" int chimera_sched_submit(chimera_task_fn fn,void* arg,uint32_t priority){
    if(!fn)return -1;
#if defined(KORONOS_FREESTANDING)
    Task prepared{};
    if(!allocate_stack(&prepared,count)) return -4;
#endif
    lock();
    if(count>=MAX_TASKS){
        unlock();
#if defined(KORONOS_FREESTANDING)
        release_stack(prepared.stack_physical,prepared.stack_pages);
#endif
        return -2;
    }
    uint32_t i=count++;
    tasks[i]={};
    tasks[i].fn=fn;tasks[i].arg=arg;
    tasks[i].info={next_id++,0,CHIMERA_TASK_READY,priority,0ull,0,0};
#if defined(KORONOS_FREESTANDING)
    // The stack's first frame stores the stable scheduler slot, not the PID.
    uint64_t *frame=reinterpret_cast<uint64_t*>(prepared.saved_rsp);
    frame[3]=i;
    tasks[i].saved_rsp=prepared.saved_rsp;
    tasks[i].stack_physical=prepared.stack_physical;
    tasks[i].stack_pages=prepared.stack_pages;
#endif
    int id=(int)tasks[i].info.id;unlock();return id;
}
extern "C" int chimera_sched_set_affinity(uint32_t task_id,uint64_t mask){
    if(mask==0)return -1;
    lock();
    for(uint32_t i=0;i<count;i++) if(tasks[i].info.id==task_id&&tasks[i].info.state!=CHIMERA_TASK_EXITED){
        tasks[i].info.affinity_mask=mask;unlock();return 0;
    }
    unlock();return -2;
}
extern "C" uint32_t chimera_sched_run_once(uint32_t cpu){
    lock();if(cpu>=cpus){unlock();return 0;}
    if(current_index[cpu]>=0){unlock();return 0;}
    const int32_t selected=pick_next_locked(cpu);
    if(selected<0){unlock();return 0;}
    const uint32_t index=(uint32_t)selected;
    tasks[index].info.state=CHIMERA_TASK_RUNNING;
    tasks[index].info.cpu=cpu;
    tasks[index].pending_action=ACTION_NONE;
    current_index[cpu]=(int32_t)index;
#if defined(KORONOS_FREESTANDING)
    tasks[index].info.runs++;
    const uint64_t new_rsp=tasks[index].saved_rsp;
    unlock();
    __sync_fetch_and_add(&context_switches,1ull);
    koronos_context_switch(&scheduler_rsp[cpu],new_rsp);
    uint64_t dead_stack=0; uint32_t dead_pages=0;
    lock();
    Task &resumed=tasks[index];
    if(resumed.info.ticks<UINT64_MAX) resumed.info.ticks++;
    if(resumed.info.state==CHIMERA_TASK_RUNNING)
        resumed.info.state=CHIMERA_TASK_READY;
    if(current_index[cpu]==(int32_t)index)current_index[cpu]=-1;
    if(resumed.info.state==CHIMERA_TASK_EXITED) {
        dead_stack=resumed.stack_physical;dead_pages=resumed.stack_pages;
        resumed.stack_physical=0;resumed.stack_pages=0;resumed.saved_rsp=0;
    }
    unlock();
    release_stack(dead_stack,dead_pages);
    return 1;
#else
    chimera_task_fn fn=tasks[index].fn;void* arg=tasks[index].arg;
    unlock();
    fn(arg);
    lock();
    Task &t=tasks[index];t.info.runs++;t.info.ticks++;
    switch(t.pending_action){
        case ACTION_YIELD:t.info.state=CHIMERA_TASK_READY;break;
        case ACTION_BLOCK:t.info.state=CHIMERA_TASK_BLOCKED;break;
        case ACTION_EXIT:t.info.state=CHIMERA_TASK_EXITED;break;
        default:if(t.info.state==CHIMERA_TASK_RUNNING)t.info.state=CHIMERA_TASK_READY;break;
    }
    t.pending_action=ACTION_NONE;
    if(current_index[cpu]==(int32_t)index)current_index[cpu]=-1;
    unlock();return 1;
#endif
}
#if defined(KORONOS_FREESTANDING)
extern "C" void chimera_sched_task_start(uint32_t index) {
    chimera_task_fn fn=nullptr;void *arg=nullptr;uint32_t cpu=0;
    lock();
    if(index<count) {fn=tasks[index].fn;arg=tasks[index].arg;cpu=tasks[index].info.cpu;}
    unlock();
    if(fn) fn(arg);
    (void)chimera_sched_exit_on_cpu(cpu);
    for(;;) __asm__ volatile("pause" ::: "memory");
}
extern "C" uint64_t chimera_sched_context_switch_count(void) {
    return context_switches;
}
#endif
extern "C" uint32_t chimera_sched_run_serial_range(uint32_t first_cpu,uint32_t n){
    lock();uint32_t total=cpus;unlock();
    if(first_cpu>=total||n==0)return 0;
    uint32_t end=first_cpu+n;if(end<first_cpu||end>total)end=total;
    uint32_t ran=0;for(uint32_t cpu=first_cpu;cpu<end;cpu++)ran+=chimera_sched_run_once(cpu);
    return ran;
}
extern "C" uint32_t chimera_sched_run_parallel(uint32_t first_cpu,uint32_t n){
    (void)first_cpu;(void)n;
    return 0;
}
extern "C" int chimera_sched_yield_on_cpu(uint32_t cpu){return request_action(cpu,ACTION_YIELD);}
extern "C" int chimera_sched_block_on_cpu(uint32_t cpu){return request_action(cpu,ACTION_BLOCK);}
extern "C" int chimera_sched_exit_on_cpu(uint32_t cpu){return request_action(cpu,ACTION_EXIT);}
extern "C" void chimera_sched_yield(void){legacy_action(ACTION_YIELD);}
extern "C" void chimera_sched_block(void){legacy_action(ACTION_BLOCK);}
extern "C" void chimera_sched_wake(uint32_t id){
    lock();for(uint32_t i=0;i<count;i++)if(tasks[i].info.id==id&&tasks[i].info.state==CHIMERA_TASK_BLOCKED)tasks[i].info.state=CHIMERA_TASK_READY;unlock();
}
extern "C" void chimera_sched_exit(void){legacy_action(ACTION_EXIT);}
extern "C" uint32_t chimera_sched_runnable_count(void){
    lock();uint32_t n=0;for(uint32_t i=0;i<count;i++)if(tasks[i].info.state==CHIMERA_TASK_READY)++n;unlock();return n;
}
extern "C" uint32_t chimera_sched_snapshot(chimera_task_info *out, uint32_t cap) {
    if(out==nullptr)return 0;
    lock();const uint32_t n=count<cap?count:cap;
    for(uint32_t i=0;i<n;i++)out[i]=tasks[i].info;
    unlock();return n;
}
