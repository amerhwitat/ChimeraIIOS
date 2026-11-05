#include <stddef.h>
#include <stdint.h>

#if defined(CHIMERA_TARGET_LIVE)
#define CHIMERA_TARGET_NAME "live"
#elif defined(CHIMERA_TARGET_INSTALLER)
#define CHIMERA_TARGET_NAME "installer"
#elif defined(CHIMERA_TARGET_RECOVERY)
#define CHIMERA_TARGET_NAME "recovery"
#else
#error "Select CHIMERA_TARGET_LIVE, CHIMERA_TARGET_INSTALLER, or CHIMERA_TARGET_RECOVERY"
#endif

static long syscall3(long number,long arg1,long arg2,long arg3) {
    register long rax __asm__("rax")=number;
    register long rdi __asm__("rdi")=arg1;
    register long rsi __asm__("rsi")=arg2;
    register long rdx __asm__("rdx")=arg3;
    __asm__ volatile("syscall"
        : "+a"(rax)
        : "D"(rdi),"S"(rsi),"d"(rdx)
        : "rcx","r11","memory");
    return rax;
}
static long text_len(const char *s) { long n=0; while(s[n])++n; return n; }
static void report(const char *s) { (void)syscall3(9,1,(long)s,text_len(s)); }
static int contains_bytes(const char *bytes,long length,const char *needle) {
    size_t n=0; while(needle[n])++n;
    if(length<0||(size_t)length<n)return 0;
    for(long i=0;i<=length-(long)n;i++){
        size_t j=0; while(j<n&&bytes[i+(long)j]==needle[j])++j;
        if(j==n)return 1;
    }
    return 0;
}
__attribute__((noreturn)) static void fail_init(const char *stage) {
    report("USER INIT PROBE FAILED: ");
    report(stage);
    report("\n");
    (void)syscall3(1,1,0,0); /* CHM_SYS_EXIT */
    for(;;)__asm__ volatile("pause");
}
static void verify_cpl3_vfs(void) {
    static const char os_path[]="/etc/os-release";
    char os_data[512];
    long fd=syscall3(17,(long)os_path,0,0); /* OPEN, O_RDONLY */
    if(fd<3||fd>=32)fail_init("open /etc/os-release");
    long n=syscall3(8,fd,(long)os_data,sizeof(os_data)); /* READ */
    if(n<=0||!contains_bytes(os_data,n,"ID=koronos"))fail_init("read /etc/os-release");
    if(syscall3(19,fd,0,0)!=0)fail_init("seek /etc/os-release");
    if(syscall3(18,fd,0,0)!=0)fail_init("close /etc/os-release");

    static const char tmp_path[]="/tmp/koronos-cpl3-vfs-probe";
    static const char expected[]="Koronos CPL3 VFS round-trip";
    char actual[sizeof(expected)]={0};
    fd=syscall3(17,(long)tmp_path,0x102u,0); /* OPEN, O_RDWR|O_CREAT */
    if(fd<3||fd>=32)fail_init("create /tmp probe");
    if(syscall3(9,fd,(long)expected,sizeof(expected)-1u)!=(long)sizeof(expected)-1u)
        fail_init("write /tmp probe");
    if(syscall3(19,fd,0,0)!=0)fail_init("seek /tmp probe");
    n=syscall3(8,fd,(long)actual,sizeof(expected)-1u);
    if(n!=(long)sizeof(expected)-1u)fail_init("read /tmp probe");
    for(size_t i=0;i<sizeof(expected)-1u;i++)if(actual[i]!=expected[i])fail_init("compare /tmp probe");
    if(syscall3(18,fd,0,0)!=0)fail_init("close /tmp probe");
    report("[TEST] CPL3 VFS OPEN/READ/WRITE/SEEK/CLOSE and /tmp round-trip passed\n");
}

__attribute__((noreturn, used)) void _start(void) {
#if defined(CHIMERA_TEST_HANG)
    for (;;) __asm__ volatile("pause" ::: "memory");
#endif
    /* The IDT's DPL3 INT 0x80 entry validates the CPU-saved CS.RPL and active
       CR3, then dispatches a real native syscall. This acknowledgement is not
       emitted by a kernel-authored readiness shortcut. */
    register long int80_number __asm__("rax")=0;
    register long int80_arg1 __asm__("rdi")=0;
    register long int80_arg2 __asm__("rsi")=0;
    register long int80_arg3 __asm__("rdx")=0;
    __asm__ volatile("int $0x80" : "+a"(int80_number) : "D"(int80_arg1),"S"(int80_arg2),"d"(int80_arg3) : "memory");
    register long number __asm__("rax")=2; /* CHM_SYS_GETPID */
    __asm__ volatile("syscall" : "+a"(number) : : "rcx","r11","memory");
    if(number<=0)fail_init("getpid");

    verify_cpl3_vfs();

    char ready_message[96];
    const char prefix[]="USERSPACE READY: target=" CHIMERA_TARGET_NAME " init_pid=";
    size_t used=0;
    for(size_t i=0;i<sizeof(prefix)-1u;i++)ready_message[used++]=prefix[i];
    char reversed[20]; size_t digits=0; unsigned long pid=(unsigned long)number;
    while(pid&&digits<sizeof(reversed)){reversed[digits++]=(char)('0'+(pid%10u));pid/=10u;}
    if(!digits||used+digits+2u>sizeof(ready_message))fail_init("format readiness");
    while(digits)ready_message[used++]=reversed[--digits];
    ready_message[used++]='\n';
    number=syscall3(9,1,(long)ready_message,(long)used);
    if(number!=(long)used)fail_init("write readiness");

    static const char returned_message[]="USERSPACE SYSCALL RETURNED TO RING3\n";
    if(syscall3(9,1,(long)returned_message,sizeof(returned_message)-1u)
       !=(long)sizeof(returned_message)-1u)fail_init("write ring3 return marker");

    (void)syscall3(1,0,0,0); /* CHM_SYS_EXIT */
    for(;;)__asm__ volatile("pause");
}
