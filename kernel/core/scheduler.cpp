#if defined(_MSC_VER)
#include <intrin.h>
#ifndef __sync_lock_test_and_set
#define __sync_lock_test_and_set(ptr, value) _InterlockedExchange(reinterpret_cast<volatile long *>(ptr), static_cast<long>(value))
#define __sync_lock_release(ptr) ((void)_InterlockedExchange(reinterpret_cast<volatile long *>(ptr), 0L))
#endif
#endif
#include "chimera/scheduler.h"
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
#include "chimera/address_space.h"
#include "chimera/kernel_stack.h"
#include "chimera/x86_64_cpu.h"
#endif
namespace {
constexpr uint32_t MAX_CPUS=256,MAX_TASKS=1024;
enum PendingAction : uint8_t { ACTION_NONE=0, ACTION_YIELD=1, ACTION_BLOCK=2, ACTION_EXIT=3 };
struct Task {
    chimera_task_fn fn;
    void* arg;
    chimera_task_info info;
    uint32_t round_seen=0;
    uint8_t pending_action=ACTION_NONE;
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    koronos_kernel_stack kernel_stack{};
    chimera_x86_64_context context{};
    bool stack_ready=false;
    bool context_ready=false;
#endif
};
Task tasks[MAX_TASKS]; uint32_t count=0,next_id=1,rr=0,dispatch_round=1,cpus=1,lock_word=0;
volatile int32_t current_index[MAX_CPUS];
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
static chimera_x86_64_context scheduler_context{};
static volatile uint32_t context_dispatches = 0;
static volatile uint32_t context_dispatch_faults = 0;
static void task_context_entry(void *opaque) {
    Task *task = static_cast<Task *>(opaque);
    if (!task || !task->fn) for (;;) __asm__ volatile("cli; hlt" ::: "memory");
    uint64_t rsp = 0;
    __asm__ volatile("mov %%rsp, %0" : "=r"(rsp));
    const bool valid = chimera_x86_64_cpu_kernel_stack(0) == task->kernel_stack.top &&
        chimera_x86_64_cpu_current_pid(0) == task->info.id &&
        rsp >= task->kernel_stack.base && rsp < task->kernel_stack.top;
    if (!valid) {
        ++context_dispatch_faults;
        task->pending_action = ACTION_EXIT;
        if (koronos_x86_64_context_switch(&task->context, &scheduler_context) != 0)
            for (;;) __asm__ volatile("cli; hlt" ::: "memory");
    } else {
        ++context_dispatches;
        task->fn(task->arg);
        /* A callback that returns has completed; never restart it as a new
         * invocation. The saved task context is retired by the scheduler. */
        chimera_sched_exit();
    }
    for (;;) __asm__ volatile("cli; hlt" ::: "memory");
}
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
static int request_action(uint32_t cpu, uint8_t action) {
    if(cpu>=cpus) return -1;
    lock();
    const int32_t i=current_index[cpu];
    if(i<0 || (uint32_t)i>=count || tasks[(uint32_t)i].info.state!=CHIMERA_TASK_RUNNING) {
        unlock();return -2;
    }
    Task &t=tasks[(uint32_t)i];
    /* A terminal/block request must not be overwritten by a later yield. */
    if(t.pending_action==ACTION_EXIT || t.pending_action==ACTION_BLOCK) {unlock();return -3;}
    if(action==ACTION_EXIT || action==ACTION_BLOCK || t.pending_action==ACTION_NONE)
        t.pending_action=action;
    unlock();return 0;
}
static int yield_to_scheduler(uint32_t cpu) {
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    if (cpu != 0) return -1;
    const int32_t index = current_index[cpu];
    if (index < 0 || static_cast<uint32_t>(index) >= count) return -2;
    return koronos_x86_64_context_switch(
        &tasks[static_cast<uint32_t>(index)].context, &scheduler_context);
#else
    (void)cpu;
    return 0;
#endif
}
static void legacy_action(uint8_t action) {
    lock(); int32_t owner=-1; uint32_t active=0;
    for(uint32_t cpu=0;cpu<cpus;cpu++) if(current_index[cpu]>=0) {owner=(int32_t)cpu;++active;}
    unlock();
    if(active==1) {
        const uint32_t cpu = static_cast<uint32_t>(owner);
        if (request_action(cpu, action) == 0) (void)yield_to_scheduler(cpu);
    }
}
}
extern "C" void chimera_sched_init(uint32_t n){
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    for(uint32_t i=0;i<count;i++)
        if(tasks[i].stack_ready) (void)koronos_kernel_stack_release(&tasks[i].kernel_stack);
    scheduler_context = {};
    context_dispatches = 0;
    context_dispatch_faults = 0;
#endif
    lock(); cpus=n?n:1;if(cpus>MAX_CPUS)cpus=MAX_CPUS;
    count=0;rr=0;dispatch_round=1;next_id=1;
    for(uint32_t i=0;i<MAX_TASKS;i++) tasks[i]={};
    for(uint32_t i=0;i<MAX_CPUS;i++) current_index[i]=-1;
    unlock();
}
extern "C" uint32_t chimera_sched_cpu_count(){lock();uint32_t n=cpus;unlock();return n;}
extern "C" int chimera_sched_submit(chimera_task_fn fn,void* arg,uint32_t priority){
    if(!fn)return -1;
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    koronos_kernel_stack stack{};
    if(!koronos_address_space_ready() || !chimera_x86_64_cpu_is_ready(0) ||
       koronos_kernel_stack_allocate(&stack)!=0) return -3;
#endif
    lock();
    if(count>=MAX_TASKS){
        unlock();
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
        (void)koronos_kernel_stack_release(&stack);
#endif
        return -2;
    }
    uint32_t i=count++;tasks[i]={};tasks[i].fn=fn;tasks[i].arg=arg;
    tasks[i].info={next_id++,0,CHIMERA_TASK_READY,priority,0ull,0,0};
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    tasks[i].kernel_stack=stack;tasks[i].stack_ready=true;
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
    /* A CPU may own at most one active callback. Without this guard, a second
       concurrent/re-entrant run_once(cpu) can overwrite current_index[cpu],
       lose ownership of the first callback, and misroute yield/block/exit. */
    if(current_index[cpu]>=0){unlock();return 0;}
    chimera_task_fn fn=nullptr;void* arg=nullptr;uint32_t index=0;
    const int32_t selected=pick_next_locked(cpu);
    if(selected<0){unlock();return 0;}
    index=(uint32_t)selected;
    tasks[index].info.state=CHIMERA_TASK_RUNNING;tasks[index].info.cpu=cpu;
    tasks[index].pending_action=ACTION_NONE;current_index[cpu]=(int32_t)index;
    fn=tasks[index].fn;arg=tasks[index].arg;unlock();
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    (void)fn; (void)arg;
    if(cpu!=0 || !tasks[index].stack_ready) {
        lock();tasks[index].info.state=CHIMERA_TASK_READY;current_index[cpu]=-1;unlock();
        return 0;
    }
    /* run_once returns to its caller after a task yields. The previous
       scheduler_context therefore points into a retired run_once stack frame.
       Start a fresh dispatcher continuation for every dispatch before saving
       the current frame into it. */
    scheduler_context = {};
    const uint64_t root=koronos_address_space_current_root();
    Task &selected_task=tasks[index];
    if (!selected_task.context_ready) {
        selected_task.context={};
        if(!root || koronos_x86_64_context_prepare(
            &selected_task.context, selected_task.kernel_stack.base,
            selected_task.kernel_stack.top-selected_task.kernel_stack.base,
            root, task_context_entry, &selected_task)!=0) {
            lock();selected_task.info.state=CHIMERA_TASK_READY;current_index[cpu]=-1;unlock();
            return 0;
        }
        selected_task.context.kernel_stack_top=selected_task.kernel_stack.top;
        selected_task.context.pid=selected_task.info.id;
        selected_task.context_ready=true;
    }
    if(koronos_x86_64_context_switch(&scheduler_context,&selected_task.context)!=0) {
        lock();selected_task.info.state=CHIMERA_TASK_READY;current_index[cpu]=-1;unlock();
        return 0;
    }
#else
    fn(arg);
#endif
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    koronos_kernel_stack retired_stack{};
    bool retire_stack=false;
#endif
    lock();
    Task &t=tasks[index];t.info.runs++;t.info.ticks++;
    switch(t.pending_action){
        case ACTION_YIELD:t.info.state=CHIMERA_TASK_READY;break;
        case ACTION_BLOCK:t.info.state=CHIMERA_TASK_BLOCKED;break;
        case ACTION_EXIT:t.info.state=CHIMERA_TASK_EXITED;break;
        default:if(t.info.state==CHIMERA_TASK_RUNNING)t.info.state=CHIMERA_TASK_READY;break;
    }
    t.pending_action=ACTION_NONE;
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    if(t.info.state==CHIMERA_TASK_EXITED && t.stack_ready) {
        retired_stack=t.kernel_stack;
        t.stack_ready=false;
        t.context_ready=false;
        t.context={};
        retire_stack=true;
    }
#endif
    if(current_index[cpu]==(int32_t)index)current_index[cpu]=-1;
    unlock();
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    if(retire_stack && koronos_kernel_stack_release(&retired_stack)!=0) {
        lock();
        t.kernel_stack=retired_stack;
        t.stack_ready=true;
        unlock();
    }
#endif
    return 1;
}
extern "C" uint32_t chimera_sched_run_serial_range(uint32_t first_cpu,uint32_t n){
    lock();uint32_t total=cpus;unlock();
    if(first_cpu>=total||n==0)return 0;
    uint32_t end=first_cpu+n;if(end<first_cpu||end>total)end=total;
    uint32_t ran=0;for(uint32_t cpu=first_cpu;cpu<end;cpu++)ran+=chimera_sched_run_once(cpu);
    return ran;
}
/* No AP workers currently enter this scheduler from independent CPUs.
 * Never report serial callback invocations as parallel execution. */
extern "C" uint32_t chimera_sched_run_parallel(uint32_t first_cpu,uint32_t n){
    (void)first_cpu;(void)n;
    return 0;
}
extern "C" int chimera_sched_yield_on_cpu(uint32_t cpu){
    const int rc=request_action(cpu,ACTION_YIELD);
    return rc==0 ? yield_to_scheduler(cpu) : rc;
}
extern "C" int chimera_sched_block_on_cpu(uint32_t cpu){
    const int rc=request_action(cpu,ACTION_BLOCK);
    return rc==0 ? yield_to_scheduler(cpu) : rc;
}
extern "C" int chimera_sched_exit_on_cpu(uint32_t cpu){
    const int rc=request_action(cpu,ACTION_EXIT);
    return rc==0 ? yield_to_scheduler(cpu) : rc;
}
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
    if (out == nullptr) {
        return 0;
    }

    lock();
    const uint32_t n = count < cap ? count : cap;
    for (uint32_t i = 0; i < n; ++i) {
        out[i] = tasks[i].info;
    }
    unlock();
    return n;
}

extern "C" uint32_t chimera_sched_context_dispatch_count(void) {
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    return context_dispatches;
#else
    return 0;
#endif
}
extern "C" uint32_t chimera_sched_context_fault_count(void) {
#if defined(CHIMERA_ENABLE_CONTEXT_SCHEDULER)
    return context_dispatch_faults;
#else
    return 0;
#endif
}
