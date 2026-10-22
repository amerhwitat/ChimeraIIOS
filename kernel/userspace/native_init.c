#include <stddef.h>
#include <stdint.h>

/* Koronos native userspace ABI, not Linux and not a shell interpreter.
 * INT 0x80 proves CPL3 entry through the DPL3 gate; native services use the
 * kernel's documented SYSCALL register convention in syscall.h.
 */
#if defined(CHIMERA_TARGET_LIVE)
#define TARGET_NAME "live"
#elif defined(CHIMERA_TARGET_INSTALLER)
#define TARGET_NAME "installer"
#elif defined(CHIMERA_TARGET_RECOVERY)
#define TARGET_NAME "recovery"
#else
#error "Select exactly one native init target"
#endif

#define CHM_SYS_EXIT 1u
#define CHM_SYS_GETPID 2u
#define CHM_SYS_WRITE 9u
#define CHM_SYS_VALIDATE_BOOT_PAYLOAD 17u

static volatile uint64_t native_init_state = 1;

static inline long koronos_syscall1(uint64_t number, uint64_t arg1) {
    register uint64_t rax __asm__("rax") = number;
    register uint64_t rdi __asm__("rdi") = arg1;
    __asm__ volatile ("syscall" : "+a"(rax) : "D"(rdi)
                      : "rcx", "r11", "memory");
    return (long)rax;
}
static inline long koronos_syscall3(uint64_t number, uint64_t arg1,
                                    const void *arg2, uint64_t arg3) {
    register uint64_t rax __asm__("rax") = number;
    register uint64_t rdi __asm__("rdi") = arg1;
    register const void *rsi __asm__("rsi") = arg2;
    register uint64_t rdx __asm__("rdx") = arg3;
    __asm__ volatile ("syscall" : "+a"(rax)
                      : "D"(rdi), "S"(rsi), "d"(rdx)
                      : "rcx", "r11", "memory");
    return (long)rax;
}
static __attribute__((noreturn)) void fail_closed(uint64_t code) {
    (void)koronos_syscall1(CHM_SYS_EXIT, code);
    for (;;) __asm__ volatile ("pause" ::: "memory");
}
static size_t append(char *out, size_t at, const char *in) {
    while (*in) out[at++] = *in++;
    return at;
}
static size_t append_u64(char *out, size_t at, uint64_t value) {
    char reverse[20];
    size_t n = 0;
    do { reverse[n++] = (char)('0' + value % 10u); value /= 10u; }
    while (value && n < sizeof(reverse));
    while (n) out[at++] = reverse[--n];
    return at;
}

__attribute__((noreturn, used)) void _start(void) {
    native_init_state = 2;
    /* This interrupt is the verifier's hardware-originated CPL3 acknowledgement.
       The kernel validates the saved CS.RPL, RIP, active PID and CR3. */
    __asm__ volatile ("int $0x80" ::: "memory");

    const long pid = koronos_syscall1(CHM_SYS_GETPID, 0);
    if (pid <= 0) fail_closed(78);
    /* Require target data-module validation before reporting init readiness. */
    if (koronos_syscall1(CHM_SYS_VALIDATE_BOOT_PAYLOAD, 0) != 0) fail_closed(78);

    /* Report only the native-init ABI milestone. VFS mounting, storage
       durability, service supervision and desktop readiness remain separate
       gates and are deliberately not asserted by this minimal init. */
    char ready[96];
    size_t used = 0;
    used = append(ready, used, "USERSPACE READY: " TARGET_NAME " init pid=");
    used = append_u64(ready, used, (uint64_t)pid);
    ready[used++] = '\n';
    const long written = koronos_syscall3(CHM_SYS_WRITE, 1, ready, used);
    if (written != (long)used) fail_closed(78);

    static const char returned[] = "NATIVE INIT: Koronos syscall round-trip verified\n";
    if (koronos_syscall3(CHM_SYS_WRITE, 1, returned, sizeof(returned)-1u)
        != (long)(sizeof(returned)-1u)) fail_closed(78);

    native_init_state = 3;
    fail_closed(0);
}
