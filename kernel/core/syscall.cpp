#include "chimera/syscall.h"
#include "chimera/user_entry.h"
#include "chimera/address_space.h"
#include "chimera/compat.h"
#include "chimera/scheduler.h"
#include "chimera/timer.h"
#include "chimera/vfs.h"
#include "chimera/process_fd.h"

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
            /* No process-owned saved context exists in this compatibility
             * entry. Do not claim a yield occurred when no switch can happen. */
            ++g_rejected;
            *return_value = error_value();
            return -1;
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
extern "C" void koronos_target_log(const char *message);
extern "C" int koronos_copy_from_user(void *destination,uint64_t source,uint64_t length);
extern "C" int koronos_copy_to_user(uint64_t destination,const void *source,uint64_t length);

namespace {
constexpr uint64_t USER_FD_MAX=32u;
static bool copy_user_path(uint64_t address,char *out,uint64_t capacity) {
    if(!out||capacity<2u)return false;
    for(uint64_t i=0;i<capacity;i++){
        if(address>UINT64_MAX-i)return false;
        char ch=0;
        if(koronos_copy_from_user(&ch,address+i,1u)!=0)return false;
        out[i]=ch;
        if(ch==0)return i!=0;
    }
    out[capacity-1u]=0;
    return false;
}
static uint64_t dispatch_native(const koronos_user_syscall_frame *frame,uint64_t user_rip) {
    if(!frame)return static_cast<uint64_t>(-22ll);
    if(!koronos_target_validate_syscall_context(user_rip)){
        koronos_target_log("[SYSC] rejected user syscall context (RIP/CR3/PID mismatch)");
        return static_cast<uint64_t>(-38ll);
    }
    const uint32_t pid=koronos_target_active_pid();
    if(!pid)return static_cast<uint64_t>(-38ll);
    switch(frame->rax){
        case CHM_SYS_GETPID:
            return static_cast<uint64_t>(pid);
        case CHM_SYS_YIELD:
            /* The callback scheduler cannot switch a ring-3 process context.
             * Return ENOSYS until saved-RSP/CR3 rescheduling is implemented. */
            return static_cast<uint64_t>(-38ll);
        case CHM_SYS_TIME_TICKS:
            return chimera_timer_now();
        case CHM_SYS_WRITE: {
            const uint64_t fd=frame->rdi,address=frame->rsi,length=frame->rdx;
            if(length>4096u)return static_cast<uint64_t>(-22ll);
            if(fd<=2u)return static_cast<uint64_t>(koronos_console_write_user(address,length));
            if(fd>=USER_FD_MAX)return static_cast<uint64_t>(-9ll);
            uint8_t buffer[4096];
            if(koronos_copy_from_user(buffer,address,length)!=0)return static_cast<uint64_t>(-14ll);
            return static_cast<uint64_t>(koronos_process_fd_write(pid,static_cast<int>(fd),buffer,length));
        }
        case CHM_SYS_READ: {
            const uint64_t fd=frame->rdi,address=frame->rsi,length=frame->rdx;
            if(fd<3u||fd>=USER_FD_MAX)return static_cast<uint64_t>(-9ll);
            if(length>4096u)return static_cast<uint64_t>(-22ll);
            if(length==0)return 0;
            if(!koronos_target_validate_user_buffer(address,length,1u))return static_cast<uint64_t>(-14ll);
            uint8_t buffer[4096];
            const int64_t n=koronos_process_fd_read(pid,static_cast<int>(fd),buffer,length);
            if(n<0)return static_cast<uint64_t>(n);
            if(koronos_copy_to_user(address,buffer,static_cast<uint64_t>(n))!=0)return static_cast<uint64_t>(-14ll);
            return static_cast<uint64_t>(n);
        }
        case CHM_SYS_OPEN: {
            if(frame->rsi>UINT32_MAX)return static_cast<uint64_t>(-22ll);
            char path[KORONOS_VFS_PATH_MAX];
            if(!copy_user_path(frame->rdi,path,sizeof(path)))return static_cast<uint64_t>(-14ll);
            const int fd=koronos_process_fd_open(pid,path,static_cast<uint32_t>(frame->rsi));
            return static_cast<uint64_t>(fd);
        }
        case CHM_SYS_CLOSE:
            if(frame->rdi>=USER_FD_MAX)return static_cast<uint64_t>(-9ll);
            return static_cast<uint64_t>(koronos_process_fd_close(pid,static_cast<int>(frame->rdi)));
        case CHM_SYS_SEEK:
            if(frame->rdi>=USER_FD_MAX||frame->rdx>2u)return static_cast<uint64_t>(-22ll);
            return static_cast<uint64_t>(koronos_process_fd_seek(pid,static_cast<int>(frame->rdi),
                static_cast<int64_t>(frame->rsi),static_cast<uint32_t>(frame->rdx)));
        case CHM_SYS_EXIT:
        case CHM_SYS_EXIT_GROUP:
            (void)koronos_process_fd_close_all(pid);
            koronos_user_exit_code=frame->rdi&0xFFu;
            koronos_target_log("[SYSC] userspace exit syscall received");
            return KORONOS_USER_SYSCALL_EXIT_SENTINEL;
        default:
            return static_cast<uint64_t>(-38ll);
    }
}
}

extern "C" void koronos_syscall_reset_process_fds(void) {
    const uint32_t pid=koronos_target_active_pid();
    if(pid)(void)koronos_process_fd_close_all(pid);
}
extern "C" void koronos_syscall_close_process_fds(void) {
    const uint32_t pid=koronos_target_active_pid();
    if(pid)(void)koronos_process_fd_close_all(pid);
}
extern "C" uint64_t koronos_syscall_user_dispatch(const koronos_user_syscall_frame *frame) {
    if(!frame)return static_cast<uint64_t>(-22ll);
    koronos_target_log("[SYSC] entered native user syscall dispatcher");
    return dispatch_native(frame,frame->rcx);
}
extern "C" uint64_t koronos_syscall_int80_dispatch(const koronos_user_syscall_frame *frame,
                                                    uint64_t user_rip,uint64_t user_cs) {
    if((user_cs&3u)!=3u)return static_cast<uint64_t>(-1ll);
    if(!frame)return static_cast<uint64_t>(-22ll);
    if(frame->rax==CHM_SYS_EXIT||frame->rax==CHM_SYS_EXIT_GROUP)
        return static_cast<uint64_t>(-38ll);
    return dispatch_native(frame,user_rip);
}
