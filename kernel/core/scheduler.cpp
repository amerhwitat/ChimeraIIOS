#if defined(_MSC_VER)
#include <intrin.h>
#ifndef __sync_lock_test_and_set
#define __sync_lock_test_and_set(ptr, value) _InterlockedExchange(reinterpret_cast<volatile long *>(ptr), static_cast<long>(value))
#define __sync_lock_release(ptr) ((void)_InterlockedExchange(reinterpret_cast<volatile long *>(ptr), 0L))
#endif
#endif
#include "chimera/scheduler.h"
namespace {
constexpr uint32_t MAX_CPUS=256, MAX_TASKS=1024;
struct Task { chimera_task_fn fn=nullptr; void* arg=nullptr; chimera_task_info info{}; uint32_t wait_age=0; };
Task tasks[MAX_TASKS];
uint32_t count=0,next_id=1,rr=0,cpus=1,lock_word=0;
int32_t current_index[MAX_CPUS];
static void lock(){while(__sync_lock_test_and_set(&lock_word,1u)){}}
static void unlock(){__sync_lock_release(&lock_word);}
static bool cpu_allowed(const chimera_task_info&i,uint32_t cpu){
    if(i.affinity_mask==0)return true;
    return cpu<64&&(i.affinity_mask&(1ull<<cpu))!=0;
}
static bool owned_locked(uint32_t index){
    for(uint32_t cpu=0;cpu<cpus;cpu++)if(current_index[cpu]==(int32_t)index)return true;
    return false;
}
static int32_t current_locked(uint32_t cpu){
    if(cpu>=cpus)return -1;
    int32_t i=current_index[cpu];
    if(i<0||(uint32_t)i>=count||tasks[(uint32_t)i].info.cpu!=cpu)return -1;
    return i;
}
static int32_t pick_next_locked(uint32_t cpu){
    int32_t best=-1;uint64_t best_score=0;const uint32_t start=count?rr%count:0;
    for(uint32_t k=0;k<count;k++){
        uint32_t i=(start+k)%count;
        if(tasks[i].info.state!=CHIMERA_TASK_READY||owned_locked(i)||!cpu_allowed(tasks[i].info,cpu))continue;
        const uint32_t age=tasks[i].wait_age>1000000u?1000000u:tasks[i].wait_age;
        const uint64_t score=(uint64_t)tasks[i].info.priority+(uint64_t)age*32u;
        if(best<0||score>best_score){best=(int32_t)i;best_score=score;}
    }
    if(best>=0){
        for(uint32_t i=0;i<count;i++){
            if(tasks[i].info.state==CHIMERA_TASK_READY&&!owned_locked(i)&&
               (int32_t)i!=best&&tasks[i].wait_age<1000000u)++tasks[i].wait_age;
        }
        tasks[(uint32_t)best].wait_age=0;
        rr=((uint32_t)best+1u)%count;
    }
    return best;
}
static void change_current(uint32_t cpu,uint32_t state){
    lock();int32_t i=current_locked(cpu);
    if(i>=0&&tasks[(uint32_t)i].info.state!=CHIMERA_TASK_EXITED)tasks[(uint32_t)i].info.state=state;
    unlock();
}
}
extern "C" void chimera_sched_init(uint32_t n){
    lock();cpus=n?(n>MAX_CPUS?MAX_CPUS:n):1;count=0;rr=0;next_id=1;
    for(uint32_t i=0;i<MAX_TASKS;i++)tasks[i]={};
    for(uint32_t i=0;i<MAX_CPUS;i++)current_index[i]=-1;
    unlock();
}
extern "C" uint32_t chimera_sched_cpu_count(void){lock();uint32_t n=cpus;unlock();return n;}
extern "C" int chimera_sched_submit(chimera_task_fn fn, void *arg, uint32_t priority) {
    if (!fn) return -1;

    lock();
    if (count >= MAX_TASKS) {
        unlock();
        return -2;
    }

    const uint32_t i = count++;
    tasks[i].fn = fn;
    tasks[i].arg = arg;
    tasks[i].info = {next_id++, 0, CHIMERA_TASK_READY, priority, 0ull, 0, 0};
    if (!next_id) next_id = 1;

    const int id = (int)tasks[i].info.id;
    unlock();
    return id;
}
extern "C" int chimera_sched_set_affinity(uint32_t id, uint64_t mask) {
    if (!mask) return -1;

    lock();
    for (uint32_t i = 0; i < count; ++i) {
        if (tasks[i].info.id != id || tasks[i].info.state == CHIMERA_TASK_EXITED) continue;
        const uint32_t cpu = tasks[i].info.cpu;
        if (owned_locked(i) && (cpu >= 64 || (mask & (1ull << cpu)) == 0)) {
            unlock();
            return -3;
        }
        tasks[i].info.affinity_mask = mask;
        unlock();
        return 0;
    }
    unlock();
    return -2;
}
extern "C" uint32_t chimera_sched_run_once(uint32_t cpu){
    if(cpu>=chimera_sched_cpu_count())return 0;
    chimera_task_fn fn=nullptr;void*arg=nullptr;uint32_t index=0;
    lock();if(current_index[cpu]>=0){unlock();return 0;}
    int32_t selected=pick_next_locked(cpu);if(selected<0){unlock();return 0;}
    index=(uint32_t)selected;tasks[index].info.state=CHIMERA_TASK_RUNNING;
    tasks[index].info.cpu=cpu;current_index[cpu]=selected;fn=tasks[index].fn;arg=tasks[index].arg;
    unlock();
    /* Cooperative callback dispatcher; not a machine context switch. */
    fn(arg);
    lock();++tasks[index].info.runs;++tasks[index].info.ticks;
    if(tasks[index].info.state==CHIMERA_TASK_RUNNING&&tasks[index].info.cpu==cpu)
        tasks[index].info.state=CHIMERA_TASK_READY;
    if(current_index[cpu]==selected)current_index[cpu]=-1;
    unlock();return 1;
}
extern "C" uint32_t chimera_sched_run_parallel(uint32_t first,uint32_t amount){
    if(!amount||first>=chimera_sched_cpu_count())return 0;
    uint32_t end=first+amount;if(end<first||end>chimera_sched_cpu_count())end=chimera_sched_cpu_count();
    uint32_t ran=0;for(uint32_t cpu=first;cpu<end;cpu++)ran+=chimera_sched_run_once(cpu);return ran;
}
extern "C" void chimera_sched_yield_cpu(uint32_t cpu){change_current(cpu,CHIMERA_TASK_READY);}
extern "C" void chimera_sched_block_cpu(uint32_t cpu){change_current(cpu,CHIMERA_TASK_BLOCKED);}
extern "C" void chimera_sched_exit_cpu(uint32_t cpu){change_current(cpu,CHIMERA_TASK_EXITED);}
extern "C" void chimera_sched_yield(void){chimera_sched_yield_cpu(0);}
extern "C" void chimera_sched_block(void){chimera_sched_block_cpu(0);}
extern "C" void chimera_sched_exit(void){chimera_sched_exit_cpu(0);}
extern "C" void chimera_sched_wake(uint32_t id){
    lock();for(uint32_t i=0;i<count;i++)if(tasks[i].info.id==id&&tasks[i].info.state==CHIMERA_TASK_BLOCKED){
        tasks[i].info.state=CHIMERA_TASK_READY;break;
    }unlock();
}
extern "C" uint32_t chimera_sched_runnable_count(void){
    lock();uint32_t n=0;for(uint32_t i=0;i<count;i++)
        if(tasks[i].info.state==CHIMERA_TASK_READY&&!owned_locked(i))++n;
    unlock();return n;
}
extern "C" uint32_t chimera_sched_snapshot(chimera_task_info *out, uint32_t cap) {
    if (!out) return 0;

    lock();
    const uint32_t n = count < cap ? count : cap;
    for (uint32_t i = 0; i < n; ++i) {
        out[i] = tasks[i].info;
    }
    unlock();
    return n;
}
