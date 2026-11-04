#include "chimera/syscall.h"
#include "chimera/user_entry.h"
#include "chimera/address_space.h"
#include "chimera/compat.h"
#include "chimera/scheduler.h"
#include "chimera/timer.h"
#include "chimera/vfs.h"

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
extern "C" int koronos_target_validate_user_buffer(uint64_t,uint64_t,uint32_t);
namespace {
constexpr uint32_t PROCESS_FD_MAX=32u;
struct ProcessFd { int handle; bool used; };
static ProcessFd process_fds[PROCESS_FD_MAX];
static int fd_allocate(int handle) {
    for(uint32_t i=3;i<PROCESS_FD_MAX;i++) if(!process_fds[i].used) { process_fds[i]={handle,true}; return static_cast<int>(i); }
    return -1;
}
static int fd_handle(uint64_t fd) { return fd>=3u && fd<PROCESS_FD_MAX && process_fds[fd].used ? process_fds[fd].handle : -1; }
static bool copy_user_path(uint64_t address,char *out,uint64_t capacity) {
    if(!out || capacity<2u) return false;
    for(uint64_t i=0;i<capacity;i++) {
        if(address>UINT64_MAX-i || !koronos_target_validate_user_buffer(address+i,1u,0u)) return false;
        const char ch=*reinterpret_cast<const char*>(static_cast<uintptr_t>(address+i));
        out[i]=ch; if(!ch) return i!=0;
    }
    out[capacity-1u]=0; return false;
}
}
extern "C" void koronos_syscall_reset_process_fds(void) { for(uint32_t i=0;i<PROCESS_FD_MAX;i++) process_fds[i]={-1,false}; }
extern "C" void koronos_syscall_close_process_fds(void) { for(uint32_t i=3;i<PROCESS_FD_MAX;i++) if(process_fds[i].used) { (void)koronos_vfs_close(process_fds[i].handle); process_fds[i]={-1,false}; } }
extern "C" void koronos_target_log(const char *message);

extern "C" uint64_t koronos_syscall_user_dispatch(const koronos_user_syscall_frame *frame) {
    if (!frame) return static_cast<uint64_t>(-22ll);
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
        case CHM_SYS_WRITE: {
            const uint64_t fd=frame->rdi,address=frame->rsi,length=frame->rdx;
            if(length>4096u || !koronos_target_validate_user_buffer(address,length,0u)) return static_cast<uint64_t>(-14ll);
            if(fd<=2u) return static_cast<uint64_t>(koronos_console_write_user(address,length));
            const int handle=fd_handle(fd); if(handle<0) return static_cast<uint64_t>(-9ll);
            return static_cast<uint64_t>(koronos_vfs_write(handle,reinterpret_cast<const void*>(static_cast<uintptr_t>(address)),length));
        }
        case CHM_SYS_READ: {
            const uint64_t fd=frame->rdi,address=frame->rsi,length=frame->rdx;
            if(length>4096u || !koronos_target_validate_user_buffer(address,length,1u)) return static_cast<uint64_t>(-14ll);
            const int handle=fd_handle(fd); if(handle<0) return static_cast<uint64_t>(-9ll);
            return static_cast<uint64_t>(koronos_vfs_read(handle,reinterpret_cast<void*>(static_cast<uintptr_t>(address)),length));
        }
        case CHM_SYS_OPEN: {
            char path[KORONOS_VFS_PATH_MAX];
            if(frame->rsi>UINT32_MAX || !copy_user_path(frame->rdi,path,sizeof(path))) return static_cast<uint64_t>(-14ll);
            const int handle=koronos_vfs_open(path,static_cast<uint32_t>(frame->rsi));
            if(handle<0) return static_cast<uint64_t>(-2ll);
            const int fd=fd_allocate(handle); if(fd<0) { (void)koronos_vfs_close(handle); return static_cast<uint64_t>(-24ll); }
            return static_cast<uint64_t>(fd);
        }
        case CHM_SYS_CLOSE: {
            const uint64_t fd=frame->rdi; const int handle=fd_handle(fd);
            if(handle<0) return static_cast<uint64_t>(-9ll);
            const int rc=koronos_vfs_close(handle); process_fds[fd]={-1,false}; return static_cast<uint64_t>(rc);
        }
        case CHM_SYS_SEEK: {
            const int handle=fd_handle(frame->rdi); if(handle<0) return static_cast<uint64_t>(-9ll);
            return static_cast<uint64_t>(koronos_vfs_seek(handle,static_cast<int64_t>(frame->rsi),static_cast<uint32_t>(frame->rdx)));
        }
        case CHM_SYS_EXIT:
        case CHM_SYS_EXIT_GROUP:
            koronos_syscall_close_process_fds();
            koronos_user_exit_code = frame->rdi & 0xFFu;
            koronos_target_log("[SYSC] userspace exit syscall received");
            return KORONOS_USER_SYSCALL_EXIT_SENTINEL;
        default:
            return static_cast<uint64_t>(-38ll);
    }
}
