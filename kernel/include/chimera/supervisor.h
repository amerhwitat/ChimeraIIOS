#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* The supervisor is kernel-internal for this change. CHM_SYS_WAIT and the
 * compatibility syscall dispatcher are left untouched: changing their ABI
 * here would risk the existing compatibility gate. User-visible wait is a
 * follow-up, not part of this kernel-runtime implementation. */
/* Kernel-owned process supervisor.
 *
 * This is a real runtime facility, not a table of fixed test values. PID 1 is
 * created at initialization as a resident scheduler task, children are real
 * chimera_sched_submit() tasks, and their exit codes come from the work entry
 * point they actually executed. */
#define CHIMERA_SUPERVISOR_ABI 1u
#define CHIMERA_SUPERVISOR_MAX_PROCESSES 128u
#define CHIMERA_SUPERVISOR_NAME_MAX 32u

/* wait() results. */
#define CHIMERA_SUP_WAIT_DELIVERED 0   /* a zombie was delivered to the parent */
#define CHIMERA_SUP_WAIT_PENDING   1   /* children exist, none has exited yet */
#define CHIMERA_SUP_WAIT_NONE      2   /* parent has no live children */

typedef enum chimera_supervisor_state {
    CHIMERA_SUP_EMPTY   = 0,
    CHIMERA_SUP_READY   = 1,
    CHIMERA_SUP_RUNNING = 2,
    CHIMERA_SUP_ZOMBIE  = 3,
    CHIMERA_SUP_EXITED  = 4,
    CHIMERA_SUP_ACTIVE  = 5
} chimera_supervisor_state;

/* Work entry point. The returned value becomes the process exit code. */
typedef uint32_t (*chimera_supervisor_work_fn)(void *arg);

typedef struct chimera_supervisor_process {
    uint32_t pid;
    uint32_t parent_pid;
    uint32_t state;
    uint32_t exit_code;
    char name[CHIMERA_SUPERVISOR_NAME_MAX];
    uint32_t id;                 /* service/tag id carried by the record */
    uint32_t sched_task_id;      /* real scheduler task id */
    uint32_t restartable;
    uint32_t max_restarts;
    uint32_t restart_count;
    uint64_t runs;
    chimera_supervisor_work_fn work;
    void *work_arg;
} chimera_supervisor_process;

typedef struct chimera_supervisor_snapshot_data {
    uint32_t process_count;
    uint32_t active_count;
    uint32_t ready_count;
    uint32_t running_count;
    uint32_t zombie_count;
    uint32_t exited_count;
    uint32_t reaped_total;
    uint32_t restarts_total;
    uint32_t notifications;
    uint32_t reaped_last_pid;
    uint32_t reaped_last_status;
    uint32_t restart_last_pid;
    uint32_t pid1_pid;
    uint32_t pid1_state;
    uint32_t pid1_task_id;
    uint32_t next_pid;
    uint32_t observed_count;
    uint32_t observed_pid[8];
    uint32_t observed_status[8];
} chimera_supervisor_snapshot_data;

int chimera_supervisor_init(void);
uint32_t chimera_supervisor_gate_requested(void);

/* parent_pid==0 creates an unparented process; pid is allocated by the kernel. */
int chimera_supervisor_spawn(chimera_supervisor_work_fn entry, void *arg,
                             uint32_t parent_pid, const char *name,
                             int restartable, uint32_t *pid_out);

/* Non-blocking wait. CHIMERA_SUP_WAIT_DELIVERED moves an EXITED child to
   ZOMBIE and returns its measured pid and exit code to the parent. */
int chimera_supervisor_wait(uint32_t parent_pid, uint32_t *pid_out,
                            uint32_t *status_out);

/* Reaps ZOMBIE children of parent_pid and returns the number reaped. */
uint32_t chimera_supervisor_reap_children(uint32_t parent_pid);

/* Changes restart policy without resetting an accumulated restart count. */
int chimera_supervisor_set_service_policy(uint32_t pid, int restartable,
                                          uint32_t max_restarts);

uint32_t chimera_supervisor_snapshot(chimera_supervisor_snapshot_data *out);
uint32_t chimera_supervisor_pid1_state(void);

/* Verifier that drives the real API and the real scheduler. */
int chimera_supervisor_selftest(void);

#ifdef __cplusplus
}
#endif
