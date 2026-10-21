#include <stdint.h>
#include <stddef.h>
#include "chimera/target_launch.h"
#include "chimera/multiboot_modules.h"
#include "chimera/process_loader.h"
#include "chimera/process.h"
#include "chimera/user_entry.h"
#include "chimera/address_space.h"
#include "chimera/elf64.h"
#include "chimera/frame_allocator.h"

namespace {
constexpr uint64_t USER_STACK_TOP = 0x00007FFFFFFFE000ull; // Loader requires a page-aligned stack ceiling
constexpr uint64_t USER_STACK_SIZE = 64ull * 1024ull;
constexpr uint64_t MAX_INIT_IMAGE = 64ull * 1024ull * 1024ull;
enum Target : uint32_t { TARGET_NONE=0, TARGET_LIVE=1, TARGET_INSTALLER=2, TARGET_RECOVERY=3 };
static volatile uint32_t active_target = TARGET_NONE;
static volatile uint32_t ready_seen = 0;
static uint32_t active_pid = 0;
static uint64_t active_root = 0;
static uint32_t syscall_ack_seen = 0;
static bool attempted = false;

extern "C" void koronos_target_log(const char *message);
extern "C" void koronos_vfs_close_process(uint32_t pid);

static bool token(const char *text, const char *needle) {
    if (!text || !needle) return false;
    const uint64_t nlen = [&]() { uint64_t n=0; while (needle[n]) ++n; return n; }();
    for (uint64_t i=0; text[i]; ++i) {
        if (i && text[i-1] != ' ') continue;
        uint64_t j=0;
        while (j<nlen && text[i+j] == needle[j]) ++j;
        if (j==nlen && (text[i+j]==0 || text[i+j]==' ')) return true;
    }
    return false;
}
static Target parse_target(const char *cmdline) {
    const bool live = token(cmdline,"target=live");
    const bool installer = token(cmdline,"target=installer");
    const bool recovery = token(cmdline,"target=recovery");
    if ((live?1:0)+(installer?1:0)+(recovery?1:0) != 1) return TARGET_NONE;
    return live ? TARGET_LIVE : (installer ? TARGET_INSTALLER : TARGET_RECOVERY);
}
static const char *target_name(Target target) {
    switch (target) {
        case TARGET_LIVE: return "live";
        case TARGET_INSTALLER: return "installer";
        case TARGET_RECOVERY: return "recovery";
        default: return "unknown";
    }
}
static void log_user_init_syscall(Target target, uint32_t pid) {
    char message[96];
    const char *name = target_name(target);
    const char prefix[] = "USER INIT SYSCALL: target=";
    size_t used = 0;
    for (size_t i = 0; i < sizeof(prefix) - 1u; ++i) message[used++] = prefix[i];
    while (*name) message[used++] = *name++;
    const char middle[] = " init_pid=";
    for (size_t i = 0; i < sizeof(middle) - 1u; ++i) message[used++] = middle[i];
    char reversed[10]; size_t digits = 0;
    do { reversed[digits++] = (char)('0' + (pid % 10u)); pid /= 10u; }
    while (pid && digits < sizeof(reversed));
    while (digits) message[used++] = reversed[--digits];
    message[used] = 0;
    koronos_target_log(message);
}
static bool target_marker(const char *bytes, uint64_t length, Target target, uint32_t pid) {
    const char *name = target_name(target);
    char prefix[80];
    uint64_t p=0;
    const char *a="USERSPACE READY: target=";
    while (*a) prefix[p++]=*a++;
    while (*name) prefix[p++]=*name++;
    const char *b=" init_pid=";
    while (*b) prefix[p++]=*b++;
    if (length < p+2u) return false;
    bool found=false;
    for (uint64_t i=0; i+p<length; ++i) {
        uint64_t j=0;
        while (j<p && bytes[i+j]==prefix[j]) ++j;
        if (j!=p) continue;
        uint64_t k=i+p;
        uint32_t parsed=0, digits=0;
        while (k<length && bytes[k]>='0' && bytes[k]<='9') {
            parsed=parsed*10u+(uint32_t)(bytes[k]-'0');
            ++k; ++digits;
        }
        if (digits && parsed==pid && (k==length || bytes[k]=='\n' || bytes[k]=='\r' || bytes[k]==' ')) {
            found=true; break;
        }
    }
    return found;
}
}

extern "C" uint32_t koronos_target_userspace_ready(void) { return ready_seen; }
extern "C" uint32_t koronos_target_active_pid(void) {
    return active_target != TARGET_NONE ? active_pid : 0u;
}
static uint32_t validate_active_user_context(uint64_t user_rip) {
    if (active_target == TARGET_NONE || !active_pid || !active_root) return 0u;
    if (user_rip < 0x0000000100000000ull || user_rip >= 0x0000800000000000ull) return 0u;
    uint64_t current_cr3 = 0;
    __asm__ volatile("mov %%cr3, %0" : "=r"(current_cr3));
    return ((current_cr3 & 0x000FFFFFFFFFF000ull) == active_root) ? active_pid : 0u;
}
extern "C" uint32_t koronos_target_validate_syscall_context(uint64_t user_rip) {
    return validate_active_user_context(user_rip);
}
extern "C" uint32_t koronos_target_note_user_syscall(uint64_t user_rip, uint64_t user_cs) {
    /* This acknowledgement is only reachable from the DPL3 INT 0x80 gate.
       The CPU-saved CS RPL, not an inferred user RIP, proves CPL3 origin. */
    if ((user_cs & 3u) != 3u) return 0u;
    const uint32_t pid = validate_active_user_context(user_rip);
    if (!pid) return 0u;
    if (!syscall_ack_seen) {
        syscall_ack_seen = 1u;
        log_user_init_syscall(static_cast<Target>(active_target), pid);
    }
    return pid;
}
extern "C" int koronos_target_note_user_write(const char *bytes, uint64_t length) {
    if (!bytes || !length || active_target==TARGET_NONE || !active_pid) return 0;
    /* Readiness is valid only after this active process has already
       issued a syscall through the DPL3 gate and the kernel verified its
       saved CS.RPL, RIP and CR3. A write that arrives first cannot satisfy
       the readiness half of the acceptance handshake. */
    if (syscall_ack_seen && active_pid &&
        target_marker(bytes,length,static_cast<Target>(active_target),active_pid)) {
        ready_seen=1;
        return 1;
    }
    return 0;
}

extern "C" int koronos_launch_selected_userspace(void) {
    if (attempted) return 0;
    attempted=true;
    const chimera_boot_module *selected=nullptr;
    uint32_t count=0;
    for (uint32_t i=0;i<chimera_multiboot_module_count();++i) {
        const chimera_boot_module *m=chimera_multiboot_module(i);
        if (m && m->kind==CHIMERA_MODULE_USER_INIT_ELF) { selected=m; ++count; }
    }
    if (count==0) return 0; // Kernel-only smoke boots intentionally have no user ELF.
    if (count!=1 || !selected || !selected->base || selected->size<sizeof(koronos_elf64_ehdr) ||
        selected->size>MAX_INIT_IMAGE || selected->base>=KORONOS_FRAME_PHYS_LIMIT ||
        selected->size>KORONOS_FRAME_PHYS_LIMIT-selected->base) {
        koronos_target_log("[RUN ] ERROR: expected exactly one bounded USER_INIT_ELF module");
        return -1;
    }
    const Target target=parse_target(selected->cmdline);
    if (target==TARGET_NONE) {
        koronos_target_log("[RUN ] ERROR: user init module must select exactly one target=live|installer|recovery");
        return -2;
    }
    if (!koronos_address_space_ready()) {
        koronos_target_log("[RUN ] ERROR: address-space/ring-3 backend unavailable");
        return -3;
    }
    const chimera_elf_load_ops *ops=koronos_address_space_loader_ops();
    if (!ops) {
        koronos_target_log("[RUN ] ERROR: ELF loader has no real address-space operations");
        return -4;
    }

    chimera_process_image process{};
    const int pid=chimera_process_admit_elf(reinterpret_cast<const void *>(static_cast<uintptr_t>(selected->base)),
        selected->size,KORONOS_EM_X86_64,USER_STACK_TOP,&process);
    if (pid<=0) {
        koronos_target_log("[RUN ] ERROR: selected user init failed protected-process admission");
        return -5;
    }
    chimera_loaded_elf loaded{};
    const int load_rc=chimera_elf_load_user_image(
        reinterpret_cast<const void *>(static_cast<uintptr_t>(selected->base)),selected->size,
        KORONOS_EM_X86_64,USER_STACK_TOP,USER_STACK_SIZE,ops,nullptr,&loaded);
    if (load_rc!=0) {
        (void)chimera_process_set_state(static_cast<uint32_t>(pid),CHIMERA_PROCESS_FAULTED);
        koronos_target_log("[RUN ] ERROR: selected user init ELF load failed");
        return -6;
    }
    const uint64_t root=koronos_address_space_root(loaded.address_space);
    if (!root) {
        ops->destroy_address_space(nullptr,loaded.address_space);
        (void)chimera_process_set_state(static_cast<uint32_t>(pid),CHIMERA_PROCESS_FAULTED);
        koronos_target_log("[RUN ] ERROR: selected user init has no owned CR3 root");
        return -7;
    }
    active_target=target;
    active_pid=static_cast<uint32_t>(pid);
    active_root=root;
    syscall_ack_seen=0;
    ready_seen=0;
    (void)chimera_process_set_state(active_pid,CHIMERA_PROCESS_RUNNING);
    // 100 Hz PIT deadline: 1,000 ticks gives user init ten seconds to return
    // and emit readiness. This is enforced by IRQ0 inside the kernel, not by
    // the outer QEMU test timeout.
    if (koronos_user_timeout_arm(1000u) != 0) {
        ops->destroy_address_space(nullptr,loaded.address_space);
        (void)chimera_process_set_state(active_pid,CHIMERA_PROCESS_FAULTED);
        active_target=TARGET_NONE;
        koronos_target_log("[RUN ] ERROR: failed to arm PIT-backed in-kernel user timeout");
        return -10;
    }
    koronos_target_log("[RUN ] Dispatching selected user init through CR3 + ring-3 entry with 10s kernel deadline");
    /* _start is a freestanding C entry, not a CRT process-entry shim.
     * Give it the SysV function-entry stack alignment (RSP % 16 == 8).
     * The full final stack page is already mapped by the ELF loader. */
    const uint64_t user_entry_stack = loaded.user_stack_top - sizeof(uint64_t);
    const int exit_code=koronos_arch_enter_user(root,loaded.entry,user_entry_stack);
    koronos_user_timeout_disarm();
    koronos_vfs_close_process(active_pid);
    ops->destroy_address_space(nullptr,loaded.address_space);
    (void)chimera_process_set_state(active_pid,exit_code==0 ? CHIMERA_PROCESS_EXITED : CHIMERA_PROCESS_FAULTED);
    active_target=TARGET_NONE;
    active_root=0;
    if (exit_code == -10) {
        koronos_target_log("[RUN ] ERROR: in-kernel PIT deadline expired; user process aborted and address space will be reclaimed");
        return -11;
    }
    if (!ready_seen) {
        koronos_target_log("[RUN ] ERROR: userspace init exited before its target-specific USERSPACE READY handshake");
        return -8;
    }
    if (exit_code!=0) {
        koronos_target_log("[RUN ] ERROR: userspace init exited nonzero after readiness");
        return -9;
    }
    koronos_target_log("[RUN ] Target userspace init emitted its own readiness handshake and exited cleanly");
    return 0;
}
