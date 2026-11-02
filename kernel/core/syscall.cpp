#include "chimera/syscall.h"
#include "chimera/user_entry.h"
#include "chimera/address_space.h"
#include "chimera/vfs.h"
#include "chimera/compat.h"
#include "chimera/scheduler.h"
#include "chimera/timer.h"
namespace {
static volatile uint32_t g_initialized=0,g_dispatched=0,g_translated=0,g_rejected=0,g_last_os=0,g_last_entry=0,g_last_number=0,g_last_canonical=0xFFFFFFFFu;
static uint64_t error_value(){return (uint64_t)(-(int64_t)CHIMERA_ENOSYS);}
static uint64_t current_root(){uint64_t root=0;__asm__ volatile("mov %%cr3,%0":"=r"(root));return root&0x000FFFFFFFFFF000ull;}
static bool user_range(uint64_t p,uint64_t n,bool write){if(!n)return true;return koronos_address_space_validate_user_range(current_root(),p,n,write?1u:0u)==0;}
static int validate_user_path(uint64_t p){
 if(!p)return -14;
 for(uint32_t i=0;i<256u;i++){if(!user_range(p+i,1,false))return -14;const char c=*(const volatile char*)(uintptr_t)(p+i);if(c==0)return (int)i;}
 return -36;
}
}
extern "C" int chimera_syscall_init(void){g_initialized=1;return 0;}
extern "C" int chimera_syscall_dispatch(uint32_t entry,uint32_t bitness,uint32_t number,const uint64_t*args,uint64_t*return_value){
 if(!return_value)return -1;++g_dispatched;chimera_syscall_identity id{};
 if(chimera_compat_recognize_syscall(entry,bitness,number,&id)!=0){++g_rejected;*return_value=error_value();return -1;}
 g_last_os=id.os;g_last_entry=id.entry;g_last_number=id.number;g_last_canonical=id.canonical;if(id.canonical!=0xFFFFFFFFu)++g_translated;
 switch(id.canonical){
 case CHM_SYS_GETPID:case CHM_SYS_EXIT:case CHM_SYS_EXIT_GROUP:case CHM_SYS_OPEN:case CHM_SYS_CLOSE:case CHM_SYS_READ:case CHM_SYS_WRITE:case CHM_SYS_SEEK:
  ++g_rejected;*return_value=error_value();return -1;
 case CHM_SYS_YIELD:chimera_sched_yield();*return_value=0;return 0;
 case CHM_SYS_TIME_TICKS:*return_value=chimera_timer_now();return 0;
 default:(void)args;++g_rejected;*return_value=error_value();return -1;
 }
}
extern "C" int chimera_syscall_get_snapshot(chimera_syscall_snapshot*out){if(!out)return -1;out->abi=CHIMERA_SYSCALL_ABI;out->initialized=g_initialized;out->dispatched=g_dispatched;out->translated=g_translated;out->rejected=g_rejected;out->last_os=g_last_os;out->last_entry=g_last_entry;out->last_number=g_last_number;out->last_canonical=g_last_canonical;return 0;}
extern "C" { volatile uint64_t koronos_user_exit_code=0; }
extern "C" uint32_t koronos_target_active_pid(void);
extern "C" uint32_t koronos_target_validate_syscall_context(uint64_t user_rip);
extern "C" int64_t koronos_console_write_user(uint64_t address,uint64_t length);
extern "C" void koronos_target_log(const char*message);
extern "C" uint64_t koronos_syscall_user_dispatch(const koronos_user_syscall_frame*frame){
 if(!frame)return (uint64_t)-22ll;
 if(!koronos_target_validate_syscall_context(frame->rcx))return (uint64_t)-38ll;
 switch(frame->rax){
 case CHM_SYS_GETPID:{uint32_t pid=koronos_target_active_pid();return pid?(uint64_t)pid:(uint64_t)-38ll;}
 case CHM_SYS_YIELD:return 0;
 case CHM_SYS_TIME_TICKS:return chimera_timer_now();
 case CHM_SYS_OPEN:{
  uint64_t path=frame->rdi;int n=validate_user_path(path);if(n<0)return (uint64_t)(int64_t)n;
  return (uint64_t)(int64_t)koronos_vfs_open((const char*)(uintptr_t)path,(uint32_t)frame->rsi);
 }
 case CHM_SYS_READ:{
  uint64_t fd=frame->rdi,buf=frame->rsi,len=frame->rdx;if(len>65536u||!user_range(buf,len,true))return (uint64_t)-14ll;
  return (uint64_t)koronos_vfs_read((int)fd,(void*)(uintptr_t)buf,len);
 }
 case CHM_SYS_WRITE:{
  uint64_t fd=frame->rdi,buf=frame->rsi,len=frame->rdx;if(len>65536u||!user_range(buf,len,false))return (uint64_t)-14ll;
  if(fd<=2u)return (uint64_t)koronos_console_write_user(buf,len);
  return (uint64_t)koronos_vfs_write((int)fd,(const void*)(uintptr_t)buf,len);
 }
 case CHM_SYS_SEEK:return (uint64_t)koronos_vfs_seek((int)frame->rdi,(int64_t)frame->rsi,(uint32_t)frame->rdx);
 case CHM_SYS_CLOSE:return (uint64_t)(int64_t)koronos_vfs_close((int)frame->rdi);
 case CHM_SYS_EXIT:case CHM_SYS_EXIT_GROUP:koronos_user_exit_code=frame->rdi&0xFFu;koronos_target_log("[SYSC] userspace exit syscall received");return KORONOS_USER_SYSCALL_EXIT_SENTINEL;
 default:return (uint64_t)-38ll;
 }
}
