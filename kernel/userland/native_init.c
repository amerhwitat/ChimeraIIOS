#include <stdint.h>
/* Native ring-3 init boundary. It verifies real process identity and performs
 * create/write/seek/read/close/unlink through CPL3 syscalls, but deliberately
 * withholds USERSPACE READY until the target's persistent storage, service
 * graph and desktop/installer/recovery operations are actually implemented. */
enum { SYS_EXIT=1, SYS_GETPID=2, SYS_READ=8, SYS_WRITE=9, SYS_OPEN=17, SYS_CLOSE=18, SYS_SEEK=19, SYS_UNLINK=22 };
enum { FD_READ=1, FD_WRITE=2, FD_CREATE=4 };
static inline long syscall3(long n,long a,long b,long c){
 register long r10 __asm__("r10")=0;
 register long r8 __asm__("r8")=0;
 register long r9 __asm__("r9")=0;
 long result;
 __asm__ volatile("syscall":"=a"(result):"a"(n),"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");
 return result;
}
static int same(const char*a,const char*b,uint64_t n){for(uint64_t i=0;i<n;++i)if(a[i]!=b[i])return 0;return 1;}
__attribute__((noreturn)) void _start(void){
 __asm__ volatile("int $0x80" ::: "memory","cc");
 long pid=syscall3(SYS_GETPID,0,0,0);
 static const char path[]="/run/native-init-selftest";
 static const char payload[]="koronos-vfs-roundtrip";
 static const char good[]="[INIT] CPL3 identity and RAM VFS create/write/seek/read/close/unlink self-test passed; production services unavailable, readiness withheld.\n";
 static const char bad[]="[INIT] ERROR: CPL3 identity or RAM VFS syscall self-test failed; readiness withheld.\n";
 char buffer[sizeof(payload)]={0};
 long fd=-1,wr=-1,sk=-1,rd=-1,cl=-1,un=-1;
 if(pid>0){
  fd=syscall3(SYS_OPEN,(long)path,FD_READ|FD_WRITE|FD_CREATE,0);
  if(fd>=3)wr=syscall3(SYS_WRITE,fd,(long)payload,sizeof(payload));
  if(wr==(long)sizeof(payload))sk=syscall3(SYS_SEEK,fd,0,0);
  if(sk==0)rd=syscall3(SYS_READ,fd,(long)buffer,sizeof(payload));
  if(rd==(long)sizeof(payload)&&same(buffer,payload,sizeof(payload)))cl=syscall3(SYS_CLOSE,fd,0,0);
  if(cl==0)un=syscall3(SYS_UNLINK,(long)path,0,0);
 }
 if(pid>0&&fd>=3&&wr==(long)sizeof(payload)&&sk==0&&rd==(long)sizeof(payload)&&same(buffer,payload,sizeof(payload))&&cl==0&&un==0)
  (void)syscall3(SYS_WRITE,1,(long)good,sizeof(good)-1);
 else
  (void)syscall3(SYS_WRITE,2,(long)bad,sizeof(bad)-1);
 (void)syscall3(SYS_EXIT,78,0,0);
 for(;;)__asm__ volatile("pause");
}
