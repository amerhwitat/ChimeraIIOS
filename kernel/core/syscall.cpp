#include "chimera/syscall.h"
#include "chimera/user_entry.h"
#include "chimera/address_space.h"
#include "chimera/compat.h"
#include "chimera/scheduler.h"
#include "chimera/timer.h"
#include "chimera/initramfs_fs.h"

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
namespace {
struct InitramfsFd { uint32_t node; uint64_t offset; uint8_t used; };
static InitramfsFd initramfs_fds[16];
static uint32_t initramfs_fd_owner = 0;
static void reset_initramfs_fds(uint32_t pid) {
    if (pid == initramfs_fd_owner) return;
    for (uint32_t i=0;i<16u;i++) initramfs_fds[i] = {};
    initramfs_fd_owner = pid;
}
static uint64_t active_cr3_root() {
    uint64_t root=0;
    __asm__ volatile("mov %%cr3, %0" : "=r"(root));
    return root & 0x000FFFFFFFFFF000ull;
}
static bool copy_user_path(uint64_t address, uint64_t root, char *out, uint32_t capacity) {
    if (!address || !root || !out || capacity<2u) return false;
    for (uint32_t i=0;i<capacity;i++) {
        if (koronos_address_space_validate_user_range(root,address+i,1u,0u)!=0) return false;
        const char c=*reinterpret_cast<const volatile char*>(address+i);
        out[i]=c;
        if (!c) return i>0u;
    }
    out[capacity-1u]=0;
    return false;
}
static int open_initramfs_file(uint64_t path_address,uint64_t flags,uint64_t root,uint32_t pid) {
    /* This bootstrap root is intentionally read-only. Accept O_RDONLY plus
       O_CLOEXEC only; never turn an absent path into a disk write request. */
    constexpr uint64_t O_ACCMODE=3u, O_CLOEXEC=0x80000u;
    if ((flags&O_ACCMODE)!=0u || (flags&~(O_ACCMODE|O_CLOEXEC))!=0u) return -30;
    char path[256];
    if (!copy_user_path(path_address,root,path,sizeof(path))) return -14;
    uint32_t node=0;
    koronos_initramfs_stat st{};
    if (koronos_initramfs_lookup(path,&node)!=0 ||
        koronos_initramfs_stat_node(node,&st)!=0 || st.type!=2u) return -2;
    reset_initramfs_fds(pid);
    for (uint32_t fd=3;fd<16u;fd++) if (!initramfs_fds[fd].used) {
        initramfs_fds[fd].node=node;
        initramfs_fds[fd].offset=0;
        initramfs_fds[fd].used=1;
        return static_cast<int>(fd);
    }
    return -24;
}
static int64_t read_initramfs_file(uint64_t fd,uint64_t buffer,uint64_t length,uint64_t root,uint32_t pid) {
    if (fd<3u || fd>=16u || length>65536u) return -22;
    reset_initramfs_fds(pid);
    InitramfsFd &entry=initramfs_fds[fd];
    if (!entry.used) return -9;
    if (!length) return 0;
    if (!buffer || !root ||
        koronos_address_space_validate_user_range(root,buffer,length,1u)!=0) return -14;
    uint64_t count=0;
    if (koronos_initramfs_read(entry.node,entry.offset,
            reinterpret_cast<void*>(buffer),length,&count)!=0) return -5;
    entry.offset+=count;
    return static_cast<int64_t>(count);
}
static int close_initramfs_file(uint64_t fd,uint32_t pid) {
    if (fd<3u || fd>=16u) return -9;
    reset_initramfs_fds(pid);
    if (!initramfs_fds[fd].used) return -9;
    initramfs_fds[fd]={};
    return 0;
}
}
extern "C" int64_t koronos_console_write_user(uint64_t address, uint64_t length);
extern "C" void koronos_target_log(const char *message);
extern "C" void koronos_syscall_trace(const char *message);

static void koronos_syscall_trace_u64(const char *label, uint64_t value) {
    static const char digits[] = "0123456789ABCDEF";
    char message[64];
    uint32_t used = 0;
    while (label && *label && used < sizeof(message) - 17u)
        message[used++] = *label++;
    for (int shift = 60; shift >= 0; shift -= 4)
        message[used++] = digits[(value >> shift) & 0xFu];
    message[used] = 0;
    koronos_syscall_trace(message);
}

extern "C" uint64_t koronos_syscall_user_dispatch(const koronos_user_syscall_frame *frame) {
    if (!frame) return static_cast<uint64_t>(-22ll);
    /* Temporary acceptance diagnostics: distinguish a failed INT 0x80 return
     * from a native SYSCALL context/dispatch failure without manufacturing
     * any userspace readiness marker. */
    koronos_syscall_trace("[SYSC] entered native user syscall dispatcher");
    /* SYSCALL does not preserve caller CS. It may serve the active process,
     * but it cannot produce the CPL3 acceptance acknowledgement. That proof
     * is emitted only by the DPL3 INT 0x80 gate after checking saved CS.RPL. */
    if (!koronos_target_validate_syscall_context(frame->rcx)) {
        koronos_syscall_trace("[SYSC] rejected user syscall context (RIP/CR3/PID mismatch)");
        return static_cast<uint64_t>(-38ll);
    }
    koronos_syscall_trace("[SYSC] accepted user syscall context");

    /* Octavian's init is linked against musl and enters through the Linux
     * x86-64 syscall ABI. Translate the raw Linux syscall number into the
     * stable Chimera semantic ABI before dispatch. Do not interpret Linux
     * syscall 1 (write) as native CHM_SYS_EXIT (also 1). */
    chimera_syscall_identity identity{};
    if (chimera_compat_recognize_syscall(
            CHM_ENTRY_X86_SYSCALL, 64u,
            static_cast<uint32_t>(frame->rax), &identity) != 0 ||
        identity.canonical == 0xFFFFFFFFu) {
        koronos_syscall_trace("[SYSC] rejected unknown Linux syscall number");
        return static_cast<uint64_t>(-38ll);
    }

    koronos_syscall_trace("[SYSC] Linux syscall translated");
    switch (identity.canonical) {
        case CHM_SYS_GETPID: {
            /* PID comes from the active kernel-owned process record. Never
             * fabricate PID 1 when no target process is actually running. */
            const uint32_t pid = koronos_target_active_pid();
            if (!pid) {
                koronos_syscall_trace("[SYSC] GETPID rejected: active process PID missing");
                return static_cast<uint64_t>(-38ll);
            }
            return static_cast<uint64_t>(pid);
        }
        case CHM_SYS_YIELD:
            // The bootstrap user entry is single-process until the scheduler owns
            // address-space context switches; yielding is currently a safe no-op.
            return 0;
        case CHM_SYS_TIME_TICKS:
            return chimera_timer_now();
        case CHM_SYS_OPEN: {
            const uint64_t raw=frame->rax;
            const uint64_t path=(raw==257u)?frame->rsi:frame->rdi;
            const uint64_t flags=(raw==257u)?frame->rdx:frame->rsi;
            if (raw==257u && static_cast<int64_t>(frame->rdi)!=-100ll)
                return static_cast<uint64_t>(-38ll); // AT_FDCWD only
            const int fd=open_initramfs_file(path,flags,active_cr3_root(),koronos_target_active_pid());
            return static_cast<uint64_t>(static_cast<int64_t>(fd));
        }
        case CHM_SYS_CLOSE:
            return static_cast<uint64_t>(static_cast<int64_t>(
                close_initramfs_file(frame->rdi,koronos_target_active_pid())));
        case CHM_SYS_READ: {
            const int64_t count=read_initramfs_file(frame->rdi,frame->rsi,frame->rdx,
                active_cr3_root(),koronos_target_active_pid());
            return static_cast<uint64_t>(count);
        }
        case CHM_SYS_WRITE: {
            koronos_syscall_trace("[SYSC] dispatching native WRITE");
            const uint64_t fd = frame->rdi;
            const uint64_t address = frame->rsi;
            const uint64_t length = frame->rdx;
            koronos_syscall_trace_u64("[SYSC] WRITE fd=0x", fd);
            koronos_syscall_trace_u64("[SYSC] WRITE ptr=0x", address);
            koronos_syscall_trace_u64("[SYSC] WRITE len=0x", length);
            if (fd > 2u) {
                koronos_syscall_trace("[SYSC] WRITE rejected: fd exceeds stderr");
                return static_cast<uint64_t>(-22ll);
            }
            if (length > 4096u) {
                koronos_syscall_trace("[SYSC] WRITE rejected: length exceeds 4096");
                return static_cast<uint64_t>(-22ll);
            }
            koronos_syscall_trace("[SYSC] WRITE arguments accepted; entering console copy");
            const int64_t written = koronos_console_write_user(address, length);
            koronos_syscall_trace("[SYSC] WRITE console copy returned");
            return static_cast<uint64_t>(written);
        }
        case CHM_SYS_EXIT:
        case CHM_SYS_EXIT_GROUP:
            koronos_user_exit_code = frame->rdi & 0xFFu;
            koronos_syscall_trace("[SYSC] userspace exit syscall received");
            return KORONOS_USER_SYSCALL_EXIT_SENTINEL;
        default:
            return static_cast<uint64_t>(-38ll);
    }
}
