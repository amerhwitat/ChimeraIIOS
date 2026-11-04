#include "chimera/process_fd.h"
namespace {
struct Entry { int vfs_handle; bool used; };
struct Owner { uint32_t pid; bool used; Entry fds[KORONOS_PROCESS_FD_MAX]; };
Owner owners[KORONOS_PROCESS_FD_PROCESSES]{};
volatile uint32_t fd_lock_word=0;
void lock(){while(__sync_lock_test_and_set(&fd_lock_word,1u)){}}
void unlock(){__sync_lock_release(&fd_lock_word);}
int owner_index(uint32_t pid){for(uint32_t i=0;i<KORONOS_PROCESS_FD_PROCESSES;i++)if(owners[i].used&&owners[i].pid==pid)return (int)i;return -1;}
int ensure_owner(uint32_t pid){int i=owner_index(pid);if(i>=0)return i;for(uint32_t n=0;n<KORONOS_PROCESS_FD_PROCESSES;n++)if(!owners[n].used){owners[n]={};owners[n].used=true;owners[n].pid=pid;return (int)n;}return -1;}
Entry *entry(uint32_t pid,int fd){int i=owner_index(pid);if(i<0||fd<0||fd>=(int)KORONOS_PROCESS_FD_MAX||!owners[i].fds[fd].used)return nullptr;return &owners[i].fds[fd];}
}
extern "C" int koronos_process_fd_init(){lock();for(uint32_t i=0;i<KORONOS_PROCESS_FD_PROCESSES;i++){for(uint32_t j=0;j<KORONOS_PROCESS_FD_MAX;j++)if(owners[i].used&&owners[i].fds[j].used)(void)koronos_vfs_close(owners[i].fds[j].vfs_handle);owners[i]={};}unlock();return 0;}
extern "C" int koronos_process_fd_open(uint32_t pid,const char*path,uint32_t flags){if(!pid||!path)return -1;lock();int oi=ensure_owner(pid);if(oi<0){unlock();return -2;}int fd=-1;for(uint32_t i=0;i<KORONOS_PROCESS_FD_MAX;i++)if(!owners[oi].fds[i].used){fd=(int)i;break;}if(fd<0){unlock();return -3;}int h=koronos_vfs_open(path,flags);if(h<0){unlock();return h;}owners[oi].fds[fd]={h,true};unlock();return fd;}
extern "C" int64_t koronos_process_fd_read(uint32_t pid,int fd,void*buffer,uint64_t n){if(!pid||(!buffer&&n))return -1;lock();Entry*e=entry(pid,fd);if(!e){unlock();return -2;}int64_t r=koronos_vfs_read(e->vfs_handle,buffer,n);unlock();return r;}
extern "C" int64_t koronos_process_fd_write(uint32_t pid,int fd,const void*buffer,uint64_t n){if(!pid||(!buffer&&n))return -1;lock();Entry*e=entry(pid,fd);if(!e){unlock();return -2;}int64_t r=koronos_vfs_write(e->vfs_handle,buffer,n);unlock();return r;}
extern "C" int64_t koronos_process_fd_seek(uint32_t pid,int fd,int64_t off,uint32_t whence){if(!pid)return -1;lock();Entry*e=entry(pid,fd);if(!e){unlock();return -2;}int64_t r=koronos_vfs_seek(e->vfs_handle,off,whence);unlock();return r;}
extern "C" int koronos_process_fd_close(uint32_t pid,int fd){if(!pid)return -1;lock();Entry*e=entry(pid,fd);if(!e){unlock();return -2;}int r=koronos_vfs_close(e->vfs_handle);if(r==0)*e={};unlock();return r;}
extern "C" int koronos_process_fd_close_all(uint32_t pid){if(!pid)return -1;lock();int oi=owner_index(pid);if(oi<0){unlock();return 0;}int result=0;for(uint32_t i=0;i<KORONOS_PROCESS_FD_MAX;i++)if(owners[oi].fds[i].used){if(koronos_vfs_close(owners[oi].fds[i].vfs_handle)!=0)result=-2;owners[oi].fds[i]={};}owners[oi]={};unlock();return result;}
extern "C" uint32_t koronos_process_fd_count(uint32_t pid){if(!pid)return 0;lock();int oi=owner_index(pid);uint32_t n=0;if(oi>=0)for(uint32_t i=0;i<KORONOS_PROCESS_FD_MAX;i++)if(owners[oi].fds[i].used)n++;unlock();return n;}
