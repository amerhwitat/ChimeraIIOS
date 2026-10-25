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
/* Target-specific GUI entrypoint names; these are lookup targets, not a claim that execve/graphics are implemented. */
#if CHIMERA_INIT_TARGET_ID == 1
#define CHIMERA_GUI_COMPONENT "aurora-session"
#define CHIMERA_GUI_ENTRYPOINT "/usr/bin/aurora-session"
#elif CHIMERA_INIT_TARGET_ID == 2
#define CHIMERA_GUI_COMPONENT "install-executor"
#define CHIMERA_GUI_ENTRYPOINT "/usr/bin/chimera-installer"
#elif CHIMERA_INIT_TARGET_ID == 3
#define CHIMERA_GUI_COMPONENT "recovery-runtime"
#define CHIMERA_GUI_ENTRYPOINT "/usr/bin/chimera-recovery"
#else
#error "Unknown CHIMERA_INIT_TARGET"
#endif
static long open_readonly(const char *path) {
  register long number __asm__("rax") = 17;
  register const char *pathname __asm__("rdi") = path;
  register long flags __asm__("rsi") = 0;
  __asm__ volatile("syscall" : "+a"(number) : "D"(pathname), "S"(flags) : "rcx", "r11", "memory");
  return number;
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
  if (call1(18, fd) != 0) return -6;

  /* Re-open with O_TRUNC and prove that the old bytes are no longer readable. */
  const long truncated_fd = call2(17, (long)path, 0x0402L); /* O_TRUNC|O_RDWR */
  if (truncated_fd < 3) return -7;
  if (call3(8, truncated_fd, (long)observed, 1) != 0) {
    (void)call1(18, truncated_fd);
    return -8;
  }
  return call1(18, truncated_fd) == 0 ? 0 : -9;
}
static int os_release_selftest(void) {
  static const char path[] = "/etc/os-release";
  static const char name_prefix[] = "NAME=";
  static const char id_prefix[] = "ID=";
  char observed[512];
  const long fd = open_readonly(path);
  if (fd < 3) return -1;
  const long count = call3(8, fd, (long)observed, (long)sizeof(observed));
  const long close_rc = call1(18, fd);
  if (count <= 0 || count > (long)sizeof(observed) || close_rc != 0) return -2;
  int identity_found = 0;
  for (long i = 0; i < count; ++i) {
    if (i + (long)(sizeof(name_prefix) - 1u) <= count) {
      size_t j = 0;
      while (j < sizeof(name_prefix) - 1u && observed[i + (long)j] == name_prefix[j]) ++j;
      if (j == sizeof(name_prefix) - 1u) identity_found = 1;
    }
    if (i + (long)(sizeof(id_prefix) - 1u) <= count) {
      size_t j = 0;
      while (j < sizeof(id_prefix) - 1u && observed[i + (long)j] == id_prefix[j]) ++j;
      if (j == sizeof(id_prefix) - 1u) identity_found = 1;
    }
  }
  return identity_found ? 0 : -3;
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
  static const char component_prefix[] = "NATIVE INIT TARGET ENTRYPOINT: " CHIMERA_GUI_COMPONENT " path=" CHIMERA_GUI_ENTRYPOINT "\n";
  static const char component_missing[] = "NATIVE INIT GUI ENTRYPOINT MISSING: target executable is absent from rootfs.\n";
  static const char component_unlaunchable[] = "NATIVE INIT GUI ENTRYPOINT FOUND, BUT EXECVE/GRAPHICS BACKEND IS UNAVAILABLE; refusing false readiness.\n";
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
  static const char tmpfs_passed[] = "USERSPACE TMPFS MUTATION PASS: CREATE WRITE READ TRUNCATE\n";
  if (write_console(vfs_passed, (long)(sizeof(vfs_passed)-1)) < 0) call1(1, 78);
  if (write_console(tmpfs_passed, (long)(sizeof(tmpfs_passed)-1)) < 0) call1(1, 78);
  if (os_release_selftest() != 0) {
    static const char os_release_failed[] = "USERSPACE ROOTFS FILE SELFTEST FAIL: /etc/os-release OPEN READ CLOSE\n";
    (void)write_console(os_release_failed, (long)(sizeof(os_release_failed)-1));
    call1(1, 78);
  }
  static const char os_release_passed[] = "USERSPACE ROOTFS FILE SELFTEST PASS: /etc/os-release OPEN READ CLOSE\n";
  if (write_console(os_release_passed, (long)(sizeof(os_release_passed)-1)) < 0) call1(1, 78);
  if (write_console(component_prefix, (long)(sizeof(component_prefix)-1)) < 0) call1(1, 78);
  const long gui_fd = open_readonly(CHIMERA_GUI_ENTRYPOINT);
  if (gui_fd < 0) {
    if (write_console(component_missing, (long)(sizeof(component_missing)-1)) < 0) call1(1, 78);
    call1(1, 78);
  }
  (void)call1(18, gui_fd);
  if (write_console(component_unlaunchable, (long)(sizeof(component_unlaunchable)-1)) < 0) call1(1, 78);
  if (write_console(blocked, (long)(sizeof(blocked)-1)) < 0) call1(1, 78);
  /* Exit 78 is an explicit unavailable-service result, not readiness. The
     production release gate must remain red until these services exist. */
  call1(1, 78);
  for (;;) __asm__ volatile("pause" ::: "memory");
}
