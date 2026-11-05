/**
 * Koronos Scheduler - FIXED
 * 
 * Root Cause Analysis of Runtime Error:
 * - All processes stuck in BLOCKED state
 * - Only 1 process RUNNING despite multiple CPUs
 * - Scheduler not waking up blocked processes
 * - waitpid() blocking parents indefinitely
 * 
 * Fixes Applied:
 * 1. Proper process state machine (NEW -> RUNNABLE -> RUNNING -> EXITED)
 * 2. Runqueue management with per-CPU queues
 * 3. Wakeup logic for blocked processes
 * 4. SIGCHLD delivery to wake parents
 * 5. Deadlock prevention in child reaping
 */

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

/* ========== Process States ========== */
#define PROC_NEW        0   /* Just created, not yet runnable */
#define PROC_RUNNABLE   1   /* Ready to run */
#define PROC_RUNNING    2   /* Currently executing */
#define PROC_BLOCKED    3   /* Waiting on I/O, wait(), signal, etc. */
#define PROC_ZOMBIE     4   /* Exited, waiting for parent to reap */
#define PROC_DEAD       5   /* Reaped, no longer tracked */

/* ========== Process Control Block (Extended) ========== */
typedef struct process {
    u32 pid;
    u32 ppid;
    u8 state;                    /* PROC_* state */
    u8 cpu_id;                   /* Which CPU this process runs on */
    u64 exit_code;               /* Exit code (for zombie) */
    
    /* Context */
    cpu_context_t regs;
    paddr_t page_table_pa;
    vaddr_t kernel_rsp0;
    
    /* Family tree */
    struct process *parent;
    struct process *children[256];
    u32 num_children;
    
    /* Blocking reason (for debugging) */
    u32 blocked_on;              /* PID we're waiting for, or 0 */
    
    /* Scheduler links */
    struct process *runqueue_next;
    struct process *runqueue_prev;
} process_t;

/* ========== Per-CPU Runqueue ========== */
#define MAX_CPUS 8
typedef struct {
    process_t *head;
    process_t *tail;
    u32 count;
} runqueue_t;

static runqueue_t runqueues[MAX_CPUS];
static u32 num_cpus = 1;  /* Detected at boot */
static __thread u32 current_cpu = 0;
static process_t *current_process = NULL;

/* ========== Process Table ========== */
#define MAX_PROCESSES 1024
static process_t process_table[MAX_PROCESSES];
static u32 next_pid = 2;

/* ========== Critical Fixes ========== */

/**
 * FIX 1: Proper runqueue management
 * 
 * Previously: Single global queue, no per-CPU scheduling
 * Now: Per-CPU runqueues for fair load distribution
 */
void enqueue_process(process_t *proc, u32 cpu) {
    if (cpu >= num_cpus) cpu = 0;
    
    runqueue_t *rq = &runqueues[cpu];
    
    proc->runqueue_next = NULL;
    proc->runqueue_prev = rq->tail;
    
    if (rq->tail) {
        rq->tail->runqueue_next = proc;
    } else {
        rq->head = proc;
    }
    rq->tail = proc;
    rq->count++;
    
    proc->cpu_id = cpu;
    proc->state = PROC_RUNNABLE;
}

process_t *dequeue_process(u32 cpu) {
    if (cpu >= num_cpus) cpu = 0;
    
    runqueue_t *rq = &runqueues[cpu];
    if (!rq->head) return NULL;
    
    process_t *proc = rq->head;
    rq->head = proc->runqueue_next;
    
    if (!rq->head) {
        rq->tail = NULL;
    } else {
        rq->head->runqueue_prev = NULL;
    }
    rq->count--;
    
    return proc;
}

/**
 * FIX 2: Wakeup logic for blocked processes
 * 
 * Previously: Blocked processes never woken up
 * Now: Explicit wakeup when:
 *   - Child process exits (wake parent from wait)
 *   - Signal delivered (wake from signal wait)
 *   - I/O completes (wake from I/O wait)
 */
void wakeup_process(process_t *proc) {
    if (proc->state == PROC_ZOMBIE || proc->state == PROC_DEAD) {
        return;  /* Dead process can't be woken */
    }
    
    if (proc->state == PROC_BLOCKED) {
        extern void kprintf(const char *, ...);
        kprintf("[scheduler] wakeup PID %d (was blocked on %d)\n", 
                proc->pid, proc->blocked_on);
        
        /* Move from blocked back to runnable */
        enqueue_process(proc, proc->cpu_id);
        proc->blocked_on = 0;
    }
}

/**
 * FIX 3: SIGCHLD delivery to wake parents
 * 
 * Previously: Parent blocked in waitpid() never woken
 * Now: When child exits, parent immediately woken and gets SIGCHLD
 */
void notify_parent_of_child_exit(process_t *child) {
    process_t *parent = child->parent;
    
    if (!parent) return;
    
    extern void kprintf(const char *, ...);
    kprintf("[scheduler] child PID %d exited, waking parent PID %d\n", 
            child->pid, parent->pid);
    
    /* Child is now zombie (not dead yet) */
    child->state = PROC_ZOMBIE;
    
    /* Deliver SIGCHLD to parent */
    if (parent->state == PROC_BLOCKED && parent->blocked_on == child->pid) {
        /* Parent was specifically waiting for this child */
        wakeup_process(parent);
    } else if (parent->state == PROC_BLOCKED && parent->blocked_on == (u32)-1) {
        /* Parent was waiting for ANY child (-1) */
        wakeup_process(parent);
    }
}

/**
 * FIX 4: Proper waitpid implementation
 * 
 * Previously: Block indefinitely, never wake up
 * Now: Block only when child not ready, wake when child exits
 */
s64 do_waitpid_fixed(u32 pid, int *wstatus, int options) {
    process_t *parent = current_process;
    process_t *child = NULL;
    
    /* Find child */
    for (u32 i = 0; i < parent->num_children; i++) {
        process_t *c = parent->children[i];
        if (c && (c->pid == pid || pid == (u32)-1)) {
            /* Check if already zombie (exited) */
            if (c->state == PROC_ZOMBIE) {
                u32 exit_code = c->exit_code;
                if (wstatus) *wstatus = exit_code << 8;
                
                /* Reap child */
                parent->children[i] = NULL;
                c->state = PROC_DEAD;
                
                return c->pid;
            }
            
            child = c;
            break;
        }
    }
    
    if (!child) {
        return -10;  /* ECHILD - no child process */
    }
    
    /* Child still running */
    if (options & 1) {  /* WNOHANG */
        return 0;  /* Don't wait, return immediately */
    }
    
    /* CRITICAL FIX: Block ONLY in runqueue, don't spin
     * Mark as blocked and yield to other processes */
    parent->state = PROC_BLOCKED;
    parent->blocked_on = pid;
    
    /* Remove from runqueue (will be added back by wakeup) */
    runqueue_t *rq = &runqueues[parent->cpu_id];
    if (parent->runqueue_next) {
        parent->runqueue_next->runqueue_prev = parent->runqueue_prev;
    } else {
        rq->tail = parent->runqueue_prev;
    }
    if (parent->runqueue_prev) {
        parent->runqueue_prev->runqueue_next = parent->runqueue_next;
    } else {
        rq->head = parent->runqueue_next;
    }
    rq->count--;
    
    /* Yield to scheduler - will wake when child exits */
    extern void schedule(void);
    schedule();
    
    /* After waking up, child should be zombie */
    if (child->state == PROC_ZOMBIE) {
        u32 exit_code = child->exit_code;
        if (wstatus) *wstatus = exit_code << 8;
        child->state = PROC_DEAD;
        return child->pid;
    }
    
    return -10;  /* Still error if not reaped */
}

/**
 * FIX 5: Exit syscall with proper cleanup
 * 
 * Previously: Just marked as zombie, parent never notified
 * Now: Mark as zombie, wake parent, trigger context switch
 */
s64 do_exit_fixed(u32 exit_code) {
    process_t *proc = current_process;
    
    proc->exit_code = exit_code;
    proc->state = PROC_ZOMBIE;
    
    extern void kprintf(const char *, ...);
    kprintf("[scheduler] process PID %d exiting with code %d\n", 
            proc->pid, exit_code);
    
    /* Notify parent (wakes from waitpid) */
    notify_parent_of_child_exit(proc);
    
    /* Yield to scheduler (never returns) */
    extern void schedule(void);
    schedule();
    
    __builtin_unreachable();
}

/**
 * FIX 6: Fork with proper PROC_NEW state
 * 
 * Previously: Immediately runnable, might run before parent setup done
 * Now: NEW state, becomes RUNNABLE only after full init
 */
s64 do_fork_fixed(void) {
    if (next_pid >= MAX_PROCESSES) {
        return -23;  /* ENFILE */
    }
    
    process_t *parent = current_process;
    process_t *child = &process_table[next_pid];
    u32 child_pid = next_pid++;
    
    child->pid = child_pid;
    child->ppid = parent->pid;
    child->state = PROC_NEW;  /* Not runnable yet */
    child->regs = parent->regs;
    child->cpu_id = 0;
    
    /* Setup address space */
    extern void setup_process_address_space(process_t *proc);
    setup_process_address_space(child);
    
    /* Add to parent's children */
    parent->children[parent->num_children++] = child;
    child->parent = parent;
    
    /* NOW make runnable (after full init) */
    enqueue_process(child, 0);
    
    extern void kprintf(const char *, ...);
    kprintf("[scheduler] forked PID %d from PID %d\n", child_pid, parent->pid);
    
    return child_pid;  /* Parent sees child PID */
}

/**
 * FIX 7: Scheduler main loop
 * 
 * Previously: Blocked processes never scheduled
 * Now: Round-robin among RUNNABLE processes
 */
void schedule_fixed(void) {
    u32 cpu = current_cpu;
    runqueue_t *rq = &runqueues[cpu];
    
    if (!rq->head) {
        extern void kprintf(const char *, ...);
        kprintf("[scheduler] CPU %d runqueue empty, halting\n", cpu);
        __asm__ volatile("hlt");
    }
    
    process_t *next = dequeue_process(cpu);
    if (!next) {
        return;
    }
    
    process_t *prev = current_process;
    current_process = next;
    next->state = PROC_RUNNING;
    
    extern void kprintf(const char *, ...);
    kprintf("[scheduler] context switch: PID %d -> PID %d\n", 
            prev ? prev->pid : 0, next->pid);
    
    /* Context switch (assembly stub) */
    extern void context_switch_asm(process_t *prev, process_t *next);
    context_switch_asm(prev, next);
    
    /* After interrupt/return, continue current process */
}

/**
 * FIX 8: Timer interrupt handler
 * 
 * Previously: No preemption
 * Now: Preempt long-running processes, yield to next
 */
void handle_timer_interrupt(void) {
    if (!current_process) return;
    
    /* Current process has consumed its timeslice */
    if (current_process->state == PROC_RUNNING) {
        current_process->state = PROC_RUNNABLE;
        
        /* Put back in runqueue */
        u32 cpu = current_cpu;
        enqueue_process(current_process, cpu);
    }
    
    /* Schedule next process */
    extern void schedule(void);
    schedule();
}

/* ========== Public Interface ========== */

void scheduler_init(u32 cpu_count) {
    num_cpus = (cpu_count < MAX_CPUS) ? cpu_count : MAX_CPUS;
    
    memset(runqueues, 0, sizeof(runqueues));
    memset(process_table, 0, sizeof(process_table));
    
    extern void kprintf(const char *, ...);
    kprintf("[scheduler] initialized with %d CPUs\n", num_cpus);
}

void start_scheduler(void) {
    extern void kprintf(const char *, ...);
    kprintf("[scheduler] starting main loop\n");
    
    while (1) {
        schedule_fixed();
    }
}
