#include <stdint.h>
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
static long write_console(const char *p, long n) {
  register long rax __asm__("rax") = 9;
  register long rdi __asm__("rdi") = 1;
  register const char *rsi __asm__("rsi") = p;
  register long rdx __asm__("rdx") = n;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi), "S"(rsi), "d"(rdx) : "rcx", "r11", "memory");
  return rax;
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
  if (write_console(blocked, (long)(sizeof(blocked)-1)) < 0) call1(1, 78);
  /* Exit 78 is an explicit unavailable-service result, not readiness. The
     production release gate must remain red until these services exist. */
  call1(1, 78);
  for (;;) __asm__ volatile("pause" ::: "memory");
}
