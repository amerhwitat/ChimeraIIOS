#pragma once
/* Freestanding ring-3 init payload helpers for native Koronos targets.
 *
 * These payloads run at CPL 3 and may only use the stable Chimera syscall ABI:
 *   EXIT=1, GETPID=2, YIELD=3, TIME_TICKS=4, READ=8, WRITE=9, OPEN=17, CLOSE=18, SEEK=19.
 * No libc, no builtins, no stack protector, no CRT shim.
 *
 * The DPL3 INT 0x80 gate is entered first so the kernel can prove the call
 * originated at CPL 3 from the saved CS.RPL; the readiness line itself is
 * emitted from user code, never from the kernel.
 */

#ifndef CHIMERA_TARGET_NAME
#error "CHIMERA_TARGET_NAME must be defined (live|installer|recovery)"
#endif

#define CHM_SYS_EXIT 1
#define CHM_SYS_GETPID 2
#define CHM_SYS_YIELD 3
#define CHM_SYS_TIME_TICKS 4
#define CHM_SYS_READ 8
#define CHM_SYS_WRITE 9
#define CHM_SYS_OPEN 17
#define CHM_SYS_CLOSE 18
#define CHM_SYS_SEEK 19
#define CHM_O_RDWR 2
#define CHM_O_CREAT 0x100
#define CHM_SEEK_SET 0

static void init_int80(void) {
    __asm__ volatile("int $0x80" ::: "memory");
}

static long init_syscall1(long number) {
    register long rax __asm__("rax") = number;
    __asm__ volatile("syscall"
                     : "+a"(rax)
                     :
                     : "rcx", "r11", "memory");
    return rax;
}

static long init_syscall3(long number, long arg1, long arg2, long arg3) {
    register long rax __asm__("rax") = number;
    register long rdi __asm__("rdi") = arg1;
    register long rsi __asm__("rsi") = arg2;
    register long rdx __asm__("rdx") = arg3;
    __asm__ volatile("syscall"
                     : "+a"(rax)
                     : "D"(rdi), "S"(rsi), "d"(rdx)
                     : "rcx", "r11", "memory");
    return rax;
}

static long init_getpid(void) { return init_syscall1(CHM_SYS_GETPID); }
static void init_yield(void) { (void)init_syscall1(CHM_SYS_YIELD); }
static long init_time_ticks(void) { return init_syscall1(CHM_SYS_TIME_TICKS); }
static long init_write(long fd, const char *buffer, long length) {
    return init_syscall3(CHM_SYS_WRITE, fd, (long)buffer, length);
}
__attribute__((noreturn)) static void init_exit(long code) {
    register long rax __asm__("rax") = CHM_SYS_EXIT;
    register long rdi __asm__("rdi") = code;
    __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi) : "rcx", "r11", "memory");
    /* The native exit syscall does not return to ring 3; this loop only guards
     * against an unexpected return. */
    for (;;) __asm__ volatile("pause" ::: "memory");
}

static long init_strlen(const char *s) {
    long n = 0;
    while (s[n]) ++n;
    return n;
}

static void init_writestr(const char *s) {
    (void)init_write(1, s, init_strlen(s));
}

static long init_syscall_arg1(long number,long arg1) {
    register long rax __asm__("rax") = number;
    register long rdi __asm__("rdi") = arg1;
    __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi) : "rcx", "r11", "memory");
    return rax;
}
static long init_read(long fd,void *buffer,long length) { return init_syscall3(CHM_SYS_READ,fd,(long)buffer,length); }
static long init_open(const char *path,long flags) { return init_syscall3(CHM_SYS_OPEN,(long)path,flags,0); }
static long init_close(long fd) { return init_syscall_arg1(CHM_SYS_CLOSE,fd); }
static long init_seek(long fd,long offset,long whence) { return init_syscall3(CHM_SYS_SEEK,fd,offset,whence); }
static int init_vfs_acceptance(void) {
    static const char payload[]="koronos-vfs-tmpfs-ok";
    char buffer[sizeof(payload)];
    const long etc=init_open("/etc/os-release",0); if(etc<3) return 0;
    char release[8]; const long got=init_read(etc,release,sizeof(release));
    const long etc_closed=init_close(etc); if(got<=0 || etc_closed!=0) return 0;
    const long fd=init_open("/tmp/koronos-acceptance",CHM_O_RDWR|CHM_O_CREAT); if(fd<3) return 0;
    const long wrote=init_write(fd,payload,(long)sizeof(payload)-1);
    const long seeked=init_seek(fd,0,CHM_SEEK_SET);
    const long readn=init_read(fd,buffer,(long)sizeof(payload)-1);
    const long closed=init_close(fd);
    if(wrote!=(long)sizeof(payload)-1 || seeked!=0 || readn!=(long)sizeof(payload)-1 || closed!=0) return 0;
    for(long i=0;i<(long)sizeof(payload)-1;i++) if(buffer[i]!=payload[i]) return 0;
    return 1;
}
static void init_emit_readiness(long pid) {
    char message[96];
    long used = 0;
    long i;
    const char *p = "USERSPACE READY: target=";
    for (i = 0; p[i]; ++i) message[used++] = p[i];
    for (i = 0; CHIMERA_TARGET_NAME[i]; ++i) message[used++] = CHIMERA_TARGET_NAME[i];
    p = " init_pid=";
    for (i = 0; p[i]; ++i) message[used++] = p[i];

    char reversed[20];
    long digits = 0;
    unsigned long value = (unsigned long)pid;
    if (value == 0) {
        reversed[digits++] = '0';
    } else {
        while (value && digits < (long)sizeof(reversed)) {
            reversed[digits++] = (char)('0' + (value % 10u));
            value /= 10u;
        }
    }
    while (digits) message[used++] = reversed[--digits];
    message[used++] = '\n';
    (void)init_write(1, message, used);
}

static void init_write_uint(unsigned long value) {
    char reversed[24];
    char forward[24];
    long digits = 0;
    long i = 0;
    if (value == 0) {
        reversed[digits++] = '0';
    } else {
        while (value && digits < (long)sizeof(reversed)) {
            reversed[digits++] = (char)('0' + (value % 10u));
            value /= 10u;
        }
    }
    while (digits) forward[i++] = reversed[--digits];
    (void)init_write(1, forward, i);
}
