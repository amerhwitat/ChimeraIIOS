#include <stdint.h>
#include <stddef.h>
#ifndef CHIMERA_INIT_TARGET
#error CHIMERA_INIT_TARGET must be set by the target build
#endif
#ifndef CHIMERA_INIT_TARGET_NAME
#error CHIMERA_INIT_TARGET_NAME must be set by the target build
#endif

static long call0(long number) {
  register long rax __asm__("rax") = number;
  __asm__ volatile("syscall" : "+a"(rax) : : "rcx", "r11", "memory");
  return rax;
}
static long call1(long number, long a) {
  register long rax __asm__("rax") = number;
  register long rdi __asm__("rdi") = a;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi) : "rcx", "r11", "memory");
  return rax;
}
static long call2(long number, long a, long b) {
  register long rax __asm__("rax") = number;
  register long rdi __asm__("rdi") = a;
  register long rsi __asm__("rsi") = b;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi), "S"(rsi) : "rcx", "r11", "memory");
  return rax;
}
static long call3(long number, long a, long b, long c) {
  register long rax __asm__("rax") = number;
  register long rdi __asm__("rdi") = a;
  register long rsi __asm__("rsi") = b;
  register long rdx __asm__("rdx") = c;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi), "S"(rsi), "d"(rdx) : "rcx", "r11", "memory");
  return rax;
}
static int vfs_selftest(void) {
  static const char path[] = "/tmp/.chimera-vfs-selftest";
  static const char payload[] = "CHIMERA-VFS-OK\n";
  char observed[sizeof(payload)];
  const long fd = call2(17, (long)path, 0x0502L); /* O_CREAT|O_TRUNC|O_RDWR */
  if (fd < 3) return -1;
  if (call3(9, fd, (long)payload, (long)sizeof(payload)) != (long)sizeof(payload)) {
    (void)call1(18, fd);
    return -2;
  }
  if (call3(19, fd, 0, 0) != 0) {
    (void)call1(18, fd);
    return -3;
  }
  if (call3(8, fd, (long)observed, (long)sizeof(payload)) != (long)sizeof(payload)) {
    (void)call1(18, fd);
    return -4;
  }
  for (size_t i = 0; i < sizeof(payload); ++i) {
    if (observed[i] != payload[i]) {
      (void)call1(18, fd);
      return -5;
    }
  }
  return call1(18, fd) == 0 ? 0 : -6;
}
static long write_console(const char *p, long n) {
  register long rax __asm__("rax") = 9;
  register long rdi __asm__("rdi") = 1;
  register const char *rsi __asm__("rsi") = p;
  register long rdx __asm__("rdx") = n;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi), "S"(rsi), "d"(rdx) : "rcx", "r11", "memory");
  return rax;
}
static void write_pid_diagnostic(long pid) {
  char message[96];
  char reversed[20];
  static const char prefix[] = "NATIVE INIT PID: target=" CHIMERA_INIT_TARGET_NAME " pid=";
  size_t used = 0;
  for (size_t i = 0; i < sizeof(prefix) - 1u; ++i) message[used++] = prefix[i];
  unsigned long value = (unsigned long)pid;
  size_t digits = 0;
  while (value && digits < sizeof(reversed)) {
    reversed[digits++] = (char)('0' + (value % 10u));
    value /= 10u;
  }
  if (digits == 0 || used + digits + 1u > sizeof(message)) call1(1, 78);
  while (digits) message[used++] = reversed[--digits];
  message[used++] = '\n';
  if (write_console(message, (long)used) < 0) call1(1, 78);
}
__attribute__((noreturn, used)) void _start(void) {
  static const char started[] = "NATIVE INIT STARTED: " CHIMERA_INIT_TARGET_NAME "\n";
  static const char blocked[] = "NATIVE INIT BLOCKED: required native filesystem, process, device and graphics services are not available; refusing to claim USERSPACE READY.\n";
  /* DPL3 interrupt acknowledges the actual ring-3 origin; GETPID must come
     from the kernel-owned process record and may never be fabricated. */
  __asm__ volatile("int $0x80" ::: "memory");
  long pid = call0(2);
  if (pid <= 0) call1(1, 78);
  if (write_console(started, (long)(sizeof(started)-1)) < 0) call1(1, 78);
  write_pid_diagnostic(pid);
  if (vfs_selftest() != 0) {
    static const char vfs_failed[] = "NATIVE INIT VFS SELFTEST FAIL: rootfs/tmpfs syscall contract unavailable.\n";
    (void)write_console(vfs_failed, (long)(sizeof(vfs_failed)-1));
    call1(1, 78);
  }
  static const char vfs_passed[] = "NATIVE INIT VFS SELFTEST PASS: create/write/seek/read/close verified.\n";
  if (write_console(vfs_passed, (long)(sizeof(vfs_passed)-1)) < 0) call1(1, 78);
  if (write_console(blocked, (long)(sizeof(blocked)-1)) < 0) call1(1, 78);
  /* Exit 78 is an explicit unavailable-service result, not readiness. The
     production release gate must remain red until these services exist. */
  call1(1, 78);
  for (;;) __asm__ volatile("pause" ::: "memory");
}
