#include "chimera/process_fd.h"
#include <assert.h>
#include <string.h>
int main(){
 assert(koronos_vfs_init()==0); assert(koronos_vfs_mount_tmpfs()==0);
 assert(koronos_process_fd_init()==0);
 int a=koronos_process_fd_open(101,"/etc/os-release",KORONOS_VFS_O_RDONLY);
 int b=koronos_process_fd_open(202,"/etc/os-release",KORONOS_VFS_O_RDONLY);
 assert(a==3&&b==3);
 char x[128]={},y[128]={};
 assert(koronos_process_fd_read(101,a,x,sizeof(x)-1)>0);
 assert(koronos_process_fd_read(202,b,y,sizeof(y)-1)>0);
 assert(strstr(x,"ID=koronos")&&strstr(y,"ID=koronos"));
 assert(koronos_process_fd_close(101,a)==0);
 assert(koronos_process_fd_read(101,a,x,1)<0);
 assert(koronos_process_fd_read(202,b,y,1)==0);
 assert(koronos_process_fd_close_all(202)==0);
 assert(koronos_process_fd_count(101)==0&&koronos_process_fd_count(202)==0);
 int w=koronos_process_fd_open(303,"/tmp/process-owned",KORONOS_VFS_O_RDWR|KORONOS_VFS_O_CREAT);
 assert(w==3);
 const char msg[]="per-process-fd";
 assert(koronos_process_fd_write(303,w,msg,sizeof(msg)-1)==(int64_t)sizeof(msg)-1);
 assert(koronos_process_fd_seek(303,w,0,0)==0);
 char out[sizeof(msg)]={};
 assert(koronos_process_fd_read(303,w,out,sizeof(msg)-1)==(int64_t)sizeof(msg)-1);
 assert(memcmp(msg,out,sizeof(msg)-1)==0);
 assert(koronos_process_fd_close_all(303)==0);
 assert(koronos_process_fd_open(0,"/etc/os-release",KORONOS_VFS_O_RDONLY)<0);
 return 0;
}
