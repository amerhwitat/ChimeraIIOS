#include <stdint.h>
/* Native ring-3 init boundary. It validates process identity and exercises
 * filesystem mutation syscalls, but deliberately withholds USERSPACE READY
 * until persistent storage and target service startup are genuinely available. */
enum { SYS_EXIT=1, SYS_GETPID=2, SYS_READ=8, SYS_WRITE=9, SYS_OPEN=17, SYS_CLOSE=18, SYS_SEEK=19, SYS_STAT=20, SYS_UNLINK=22, SYS_TRUNCATE=23, SYS_CHMOD=24, SYS_CHOWN=25, SYS_MKDIR=26, SYS_RMDIR=27, SYS_RENAME=28 };
enum { FD_READ=1, FD_WRITE=2, FD_CREATE=4 };
enum { TYPE_FILE=1 };
struct vfs_stat { uint64_t size,capacity; uint32_t uid,gid,mode,type; };
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
 static const char dir[]="/run";
 static const char path[]="/run/native-init-selftest";
 static const char moved[]="/run/native-init-renamed";
 static const char payload[]="koronos-vfs-roundtrip";
 static const char good[]="[INIT] CPL3 identity and RAM VFS create/write/seek/read/stat/chmod/chown/truncate/close/rename/unlink/mkdir/rmdir passed; persistent services unavailable, readiness withheld.\n";
 static const char bad[]="[INIT] ERROR: CPL3 identity or RAM VFS syscall self-test failed; readiness withheld.\n";
 char buffer[sizeof(payload)]={0};struct vfs_stat st={0};
 long md=-1,fd=-1,wr=-1,sk=-1,rd=-1,stat1=-1,chmod1=-1,chown1=-1,trunc=-1,stat2=-1,busy=-1,cl=-1,ren=-1,un=-1,rdmd=-1;
 if(pid>0)md=syscall3(SYS_MKDIR,(long)dir,0755,0);
 if(md==0)fd=syscall3(SYS_OPEN,(long)path,FD_READ|FD_WRITE|FD_CREATE,0);
 if(fd>=3)wr=syscall3(SYS_WRITE,fd,(long)payload,sizeof(payload));
 if(wr==(long)sizeof(payload))sk=syscall3(SYS_SEEK,fd,0,0);
 if(sk==0)rd=syscall3(SYS_READ,fd,(long)buffer,sizeof(payload));
 if(rd==(long)sizeof(payload)&&same(buffer,payload,sizeof(payload)))stat1=syscall3(SYS_STAT,(long)path,(long)&st,0);
 if(stat1==0&&st.size==sizeof(payload)&&st.type==TYPE_FILE)chmod1=syscall3(SYS_CHMOD,(long)path,0600,0);
 if(chmod1==0)chown1=syscall3(SYS_CHOWN,(long)path,0,0);
 if(chown1==0)trunc=syscall3(SYS_TRUNCATE,(long)path,4,0);
 if(trunc==0)stat2=syscall3(SYS_STAT,(long)path,(long)&st,0);
 if(stat2==0&&st.size==4&&st.mode==0600)busy=syscall3(SYS_RMDIR,(long)dir,0,0);
 if(busy==-9)cl=syscall3(SYS_CLOSE,fd,0,0);
 if(cl==0)ren=syscall3(SYS_RENAME,(long)path,(long)moved,0);
 if(ren==0)un=syscall3(SYS_UNLINK,(long)moved,0,0);
 if(un==0)rdmd=syscall3(SYS_RMDIR,(long)dir,0,0);
 if(pid>0&&md==0&&fd>=3&&wr==(long)sizeof(payload)&&sk==0&&rd==(long)sizeof(payload)&&same(buffer,payload,sizeof(payload))&&stat1==0&&chmod1==0&&chown1==0&&trunc==0&&stat2==0&&st.size==4&&st.mode==0600&&busy==-9&&cl==0&&ren==0&&un==0&&rdmd==0)
  (void)syscall3(SYS_WRITE,1,(long)good,sizeof(good)-1);
 else {
  if(fd>=3) (void)syscall3(SYS_CLOSE,fd,0,0);
  if(ren!=0) (void)syscall3(SYS_UNLINK,(long)path,0,0);
  (void)syscall3(SYS_UNLINK,(long)moved,0,0);
  (void)syscall3(SYS_RMDIR,(long)dir,0,0);
  (void)syscall3(SYS_WRITE,2,(long)bad,sizeof(bad)-1);
 }
 (void)syscall3(SYS_EXIT,78,0,0);
 for(;;)__asm__ volatile("pause");
}
