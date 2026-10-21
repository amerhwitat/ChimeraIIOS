#include "chimera/syscall.h"
#include "chimera/user_entry.h"
#include "chimera/address_space.h"
#include "chimera/compat.h"
#include "chimera/scheduler.h"
#include "chimera/timer.h"

namespace {
static volatile uint32_t g_initialized = 0;
static volatile uint32_t g_dispatched = 0;
static volatile uint32_t g_translated = 0;
static volatile uint32_t g_rejected = 0;
static volatile uint32_t g_last_os = 0;
static volatile uint32_t g_last_entry = 0;
static volatile uint32_t g_last_number = 0;
static volatile uint32_t g_last_canonical = 0xFFFFFFFFu;

static uint64_t error_value() {
    return (uint64_t)(-(int64_t)CHIMERA_ENOSYS);
}
}

extern "C" int chimera_syscall_init(void) {
    g_initialized = 1;
    return 0;
}

extern "C" int chimera_syscall_dispatch(uint32_t entry, uint32_t bitness, uint32_t number,
                                         const uint64_t *args, uint64_t *return_value) {
    if (!return_value) return -1;
    ++g_dispatched;

    chimera_syscall_identity id{};
    if (chimera_compat_recognize_syscall(entry, bitness, number, &id) != 0) {
        ++g_rejected;
        *return_value = error_value();
        return -1;
    }

    g_last_os = id.os;
    g_last_entry = id.entry;
    g_last_number = id.number;
    g_last_canonical = id.canonical;

    if (id.canonical != 0xFFFFFFFFu) ++g_translated;

    switch (id.canonical) {
        case CHM_SYS_GETPID:
            /* This compatibility dispatcher has no active process context.
             * The native ring-3 path resolves GETPID from the kernel-owned
             * active process record. Fail closed here rather than invent PID 1. */
            ++g_rejected;
            *return_value = error_value();
            return -1;
        case CHM_SYS_YIELD:
            chimera_sched_yield();
            *return_value = 0;
            return 0;
        case CHM_SYS_TIME_TICKS:
            *return_value = chimera_timer_now();
            return 0;
        case CHM_SYS_EXIT:
        case CHM_SYS_EXIT_GROUP:
            /* No process identity/teardown is available in this compatibility
             * dispatcher. Only the native process-bound entry may exit a task. */
            (void)args;
            ++g_rejected;
            *return_value = error_value();
            return -1;
        default:
            ++g_rejected;
            *return_value = error_value();
            return -1;
    }
}

extern "C" int chimera_syscall_get_snapshot(chimera_syscall_snapshot *out) {
    if (!out) return -1;
    out->abi = CHIMERA_SYSCALL_ABI;
    out->initialized = g_initialized;
    out->dispatched = g_dispatched;
    out->translated = g_translated;
    out->rejected = g_rejected;
    out->last_os = g_last_os;
    out->last_entry = g_last_entry;
    out->last_number = g_last_number;
    out->last_canonical = g_last_canonical;
    return 0;
}

extern "C" {
volatile uint64_t koronos_user_exit_code = 0;
}
extern "C" uint32_t koronos_target_active_pid(void);
extern "C" uint32_t koronos_target_validate_syscall_context(uint64_t user_rip);
extern "C" int64_t koronos_console_write_user(uint64_t address, uint64_t length);
extern "C" void koronos_target_log(const char *message);
extern "C" int koronos_user_timeout_pending(void);
extern "C" __attribute__((noreturn)) void koronos_user_timeout_abort(void);
extern "C" int64_t koronos_vfs_open_user(uint64_t path_address,uint64_t flags);
extern "C" int64_t koronos_vfs_read_user(uint64_t fd,uint64_t address,uint64_t length);
extern "C" int64_t koronos_vfs_write_user(uint64_t fd,uint64_t address,uint64_t length);
extern "C" int64_t koronos_vfs_seek_user(uint64_t fd,uint64_t offset);
extern "C" int64_t koronos_vfs_close_user(uint64_t fd);
extern "C" int64_t koronos_vfs_stat_user(uint64_t path_address,uint64_t out_address);
extern "C" int64_t koronos_vfs_create_user(uint64_t path_address,uint64_t mode);
extern "C" int64_t koronos_vfs_unlink_user(uint64_t path_address);
extern "C" int64_t koronos_vfs_truncate_user(uint64_t path_address,uint64_t length);
extern "C" int64_t koronos_vfs_chmod_user(uint64_t path_address,uint64_t mode);
extern "C" int64_t koronos_vfs_chown_user(uint64_t path_address,uint64_t uid,uint64_t gid);
extern "C" int64_t koronos_vfs_mkdir_user(uint64_t path_address,uint64_t mode);
extern "C" int64_t koronos_vfs_rmdir_user(uint64_t path_address);
extern "C" int64_t koronos_vfs_rename_user(uint64_t old_address,uint64_t new_address);



extern "C" uint64_t koronos_syscall_user_dispatch(const koronos_user_syscall_frame *frame) {
    if (!frame) return static_cast<uint64_t>(-22ll);
    /* A deadline may expire while the task is in CPL3. Refuse further work and
       unwind through the dedicated timeout path before dispatching any syscall. */
    if (koronos_user_timeout_pending()) {
        koronos_target_log("[SYSC] launch deadline expired; aborting user process");
        koronos_user_timeout_abort();
    }
    /* Temporary acceptance diagnostics: distinguish a failed INT 0x80 return
     * from a native SYSCALL context/dispatch failure without manufacturing
     * any userspace readiness marker. */
    koronos_target_log("[SYSC] entered native user syscall dispatcher");
    /* SYSCALL does not preserve caller CS. It may serve the active process,
     * but it cannot produce the CPL3 acceptance acknowledgement. That proof
     * is emitted only by the DPL3 INT 0x80 gate after checking saved CS.RPL. */
    if (!koronos_target_validate_syscall_context(frame->rcx)) {
        koronos_target_log("[SYSC] rejected user syscall context (RIP/CR3/PID mismatch)");
        return static_cast<uint64_t>(-38ll);
    }
    koronos_target_log("[SYSC] accepted user syscall context");
    switch (frame->rax) {
        case CHM_SYS_GETPID: {
            /* PID comes from the active kernel-owned process record. Never
             * fabricate PID 1 when no target process is actually running. */
            const uint32_t pid = koronos_target_active_pid();
            return pid ? static_cast<uint64_t>(pid) : static_cast<uint64_t>(-38ll);
        }
        case CHM_SYS_YIELD:
            // The bootstrap user entry is single-process until the scheduler owns
            // address-space context switches; yielding is currently a safe no-op.
            return 0;
        case CHM_SYS_TIME_TICKS:
            return chimera_timer_now();
        case CHM_SYS_READ:
            return static_cast<uint64_t>(koronos_vfs_read_user(frame->rdi,frame->rsi,frame->rdx));
        case CHM_SYS_WRITE:
            return static_cast<uint64_t>(koronos_vfs_write_user(frame->rdi,frame->rsi,frame->rdx));
        case CHM_SYS_OPEN:
            return static_cast<uint64_t>(koronos_vfs_open_user(frame->rdi,frame->rsi));
        case CHM_SYS_CLOSE:
            return static_cast<uint64_t>(koronos_vfs_close_user(frame->rdi));
        case CHM_SYS_SEEK:
            return static_cast<uint64_t>(koronos_vfs_seek_user(frame->rdi,frame->rsi));
        case CHM_SYS_STAT:
            return static_cast<uint64_t>(koronos_vfs_stat_user(frame->rdi,frame->rsi));
        case CHM_SYS_CREATE:
            return static_cast<uint64_t>(koronos_vfs_create_user(frame->rdi,frame->rsi));
        case CHM_SYS_UNLINK:
            return static_cast<uint64_t>(koronos_vfs_unlink_user(frame->rdi));
        case CHM_SYS_TRUNCATE:
            return static_cast<uint64_t>(koronos_vfs_truncate_user(frame->rdi,frame->rsi));
        case CHM_SYS_CHMOD:
            return static_cast<uint64_t>(koronos_vfs_chmod_user(frame->rdi,frame->rsi));
        case CHM_SYS_CHOWN:
            return static_cast<uint64_t>(koronos_vfs_chown_user(frame->rdi,frame->rsi,frame->rdx));
        case CHM_SYS_MKDIR:
            return static_cast<uint64_t>(koronos_vfs_mkdir_user(frame->rdi,frame->rsi));
        case CHM_SYS_RMDIR:
            return static_cast<uint64_t>(koronos_vfs_rmdir_user(frame->rdi));
        case CHM_SYS_RENAME:
            return static_cast<uint64_t>(koronos_vfs_rename_user(frame->rdi,frame->rsi));
        case CHM_SYS_EXIT:
        case CHM_SYS_EXIT_GROUP:
            koronos_user_exit_code = frame->rdi & 0xFFu;
            koronos_target_log("[SYSC] userspace exit syscall received");
            return KORONOS_USER_SYSCALL_EXIT_SENTINEL;
        default:
            return static_cast<uint64_t>(-38ll);
    }
}
