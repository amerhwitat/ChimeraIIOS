#include "chimera/scheduler.h"
namespace {
constexpr uint32_t MAX_CPUS=256,MAX_TASKS=1024;
struct Task { chimera_task_fn fn; void* arg; chimera_task_info info; };
Task tasks[MAX_TASKS]; volatile uint32_t count=0,next_id=1,rr=0,cpus=1,lock_word=0;
volatile int32_t current_index[MAX_CPUS];
static void lock(){while(__sync_lock_test_and_set(&lock_word,1u)){} }
static void unlock(){__sync_lock_release(&lock_word);}
static bool cpu_allowed(const chimera_task_info& info,uint32_t cpu){
    if(cpu>=64 || info.affinity_mask==0) return true;
    return (info.affinity_mask & (1ull<<cpu)) != 0;
}
}
extern "C" void chimera_sched_init(uint32_t n){
    cpus=n?n:1; if(cpus>MAX_CPUS)cpus=MAX_CPUS;
    lock(); count=0; rr=0; next_id=1;
    for(uint32_t i=0;i<MAX_TASKS;i++) tasks[i]={};
    for(uint32_t i=0;i<MAX_CPUS;i++) current_index[i]=-1;
    unlock();
}
extern "C" uint32_t chimera_sched_cpu_count(){return cpus;}
extern "C" int chimera_sched_submit(chimera_task_fn fn,void* arg,uint32_t priority){
    if(!fn) return -1;
    lock();
    if(count>=MAX_TASKS){unlock();return -2;}
    uint32_t i=count++; tasks[i].fn=fn; tasks[i].arg=arg;
    tasks[i].info={next_id++,0,CHIMERA_TASK_READY,priority,0ull,0,0};
    int id=(int)tasks[i].info.id; unlock(); return id;
}
extern "C" int chimera_sched_set_affinity(uint32_t task_id,uint64_t affinity_mask){
    if(affinity_mask==0) return -1;
    lock();
    for(uint32_t i=0;i<count;i++){
        if(tasks[i].info.id==task_id && tasks[i].info.state!=CHIMERA_TASK_EXITED){
            tasks[i].info.affinity_mask=affinity_mask;
            unlock(); return 0;
        }
    }
    unlock(); return -2;
}
extern "C" uint32_t chimera_sched_run_once(uint32_t cpu){
    if(cpu>=cpus) return 0;
    uint32_t ran=0; lock(); uint32_t n=count,start=rr++; unlock();
    for(uint32_t k=0;k<n;k++){
        uint32_t i=(start+k)%n; lock();
        if(tasks[i].info.state!=CHIMERA_TASK_READY || !cpu_allowed(tasks[i].info,cpu)){unlock();continue;}
        tasks[i].info.state=CHIMERA_TASK_RUNNING; tasks[i].info.cpu=cpu;
        chimera_task_fn f=tasks[i].fn; void* a=tasks[i].arg; current_index[cpu]=(int32_t)i; unlock();
        f(a);
        lock();
        tasks[i].info.runs++; tasks[i].info.ticks++;
        if(tasks[i].info.state==CHIMERA_TASK_RUNNING) tasks[i].info.state=CHIMERA_TASK_READY;
        current_index[cpu]=-1; unlock(); ran++;
    }
    return ran;
}
extern "C" uint32_t chimera_sched_run_parallel(uint32_t first_cpu,uint32_t cpu_count){
    if(first_cpu>=cpus || cpu_count==0) return 0;
    uint32_t end=first_cpu+cpu_count; if(end>cpus) end=cpus;
    uint32_t ran=0;
    /* This is the SMP dispatch surface: AP startup/interrupt code may call
       run_once concurrently on each CPU. On a uniprocessor it remains safe
       and deterministic, while SMP callers obtain independent per-CPU state. */
    for(uint32_t cpu=first_cpu;cpu<end;cpu++) ran+=chimera_sched_run_once(cpu);
    return ran;
}
extern "C" void chimera_sched_yield(void){
    for(uint32_t cpu=0;cpu<cpus;cpu++) { lock(); int32_t i=current_index[cpu]; if(i>=0) tasks[(uint32_t)i].info.state=CHIMERA_TASK_READY; unlock(); }
}
extern "C" void chimera_sched_block(void){
    for(uint32_t cpu=0;cpu<cpus;cpu++) { lock(); int32_t i=current_index[cpu]; if(i>=0) tasks[(uint32_t)i].info.state=CHIMERA_TASK_BLOCKED; unlock(); }
}
extern "C" void chimera_sched_wake(uint32_t task_id){
    lock(); for(uint32_t i=0;i<count;i++) if(tasks[i].info.id==task_id && tasks[i].info.state==CHIMERA_TASK_BLOCKED) tasks[i].info.state=CHIMERA_TASK_READY; unlock();
}
extern "C" void chimera_sched_exit(void){
    for(uint32_t cpu=0;cpu<cpus;cpu++) { lock(); int32_t i=current_index[cpu]; if(i>=0) tasks[(uint32_t)i].info.state=CHIMERA_TASK_EXITED; unlock(); }
}
extern "C" uint32_t chimera_sched_runnable_count(void){
    uint32_t n=0; lock(); for(uint32_t i=0;i<count;i++) if(tasks[i].info.state==CHIMERA_TASK_READY) ++n; unlock(); return n;
}
extern "C" uint32_t chimera_sched_snapshot(chimera_task_info* out,uint32_t cap){
    if(!out) return 0; lock(); uint32_t n=count<cap?count:cap; for(uint32_t i=0;i<n;i++)out[i]=tasks[i].info; unlock(); return n;
}
