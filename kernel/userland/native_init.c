#include <stdint.h>
/* Native ring-3 init boundary. This deliberately does not emit USERSPACE READY:
 * storage mounts, target services and a real target runtime must be verified
 * before readiness can be truthful. It exercises CPL3 INT 0x80 plus SYSCALL,
 * then exits fail-closed with status 78. */
enum { SYS_EXIT=1, SYS_GETPID=2, SYS_WRITE=9 };
static inline long syscall3(long n,long a,long b,long c){
 register long r10 __asm__("r10")=0;
 register long r8 __asm__("r8")=0;
 register long r9 __asm__("r9")=0;
 long result;
 __asm__ volatile("syscall":"=a"(result):"a"(n),"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");
 return result;
}
__attribute__((noreturn)) void _start(void){
 __asm__ volatile("int $0x80" ::: "memory","cc");
 long pid=syscall3(SYS_GETPID,0,0,0);
 static const char good[]="[INIT] Native ring-3 init entered; required production services are not yet verified. Readiness withheld.\n";
 static const char bad[]="[INIT] ERROR: kernel did not provide a valid process-owned PID. Readiness withheld.\n";
 if(pid>0) (void)syscall3(SYS_WRITE,1,(long)good,sizeof(good)-1);
 else (void)syscall3(SYS_WRITE,2,(long)bad,sizeof(bad)-1);
 (void)syscall3(SYS_EXIT,78,0,0);
 for(;;)__asm__ volatile("pause");
}
