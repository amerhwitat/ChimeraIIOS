#include "chimera/tmpfs.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void *alloc_mem(uint64_t n,void*){return malloc((size_t)n);}
static void free_mem(void*p,void*){free(p);}
static int fail(const char*m){fprintf(stderr,"TMPFS TEST FAIL: %s\n",m);return 1;}
int main(){
    const chimera_ramfs_allocator a{alloc_mem,free_mem,nullptr};
    const chimera_tmpfs_limits limits{64u,CHIMERA_VFS_MAX_PATH,1024u,4096u};
    chimera_tmpfs*fs=nullptr;if(chimera_tmpfs_create(&a,&limits,&fs)!=0||!fs)return fail("create");
    if(chimera_vfs_init()!=0)return fail("vfs init");
    if(chimera_vfs_mount("/",chimera_tmpfs_vfs_ops(),fs,0)!=0)return fail("mount tmpfs");
    if(chimera_vfs_mkdir("/var",0755u)!=0)return fail("mkdir");
    int64_t fd=chimera_vfs_open(10,"/var/state",CHIMERA_VFS_O_CREAT|CHIMERA_VFS_O_RDWR,0644u);if(fd<3)return fail("create file");
    const char input[]="transactional-tmpfs";if(chimera_vfs_write(10,fd,input,sizeof(input))!=(int64_t)sizeof(input))return fail("write");
    if(chimera_vfs_seek(10,fd,0,0)!=0)return fail("seek");
    char output[32]{};if(chimera_vfs_read(10,fd,output,sizeof(input))!=(int64_t)sizeof(input))return fail("read");
    if(memcmp(input,output,sizeof(input)))return fail("readback");
    if(chimera_vfs_close(10,fd)!=0)return fail("close");
    fd=chimera_vfs_open(10,"/var/state",CHIMERA_VFS_O_RDWR|CHIMERA_VFS_O_TRUNC,0644u);if(fd<3)return fail("truncate open");
    chimera_vfs_stat st{};if(chimera_vfs_stat_path("/var/state",&st)!=0||st.size!=0)return fail("truncate did not clear file");
    if(chimera_vfs_close(10,fd)!=0)return fail("close truncated file");
    if(chimera_vfs_unlink("/var/state",0)!=0)return fail("unlink file");
    if(chimera_vfs_unlink("/var",1)!=0)return fail("remove directory");
    chimera_vfs_unmount("/");chimera_tmpfs_destroy(fs);puts("TMPFS TEST PASS");return 0;
}
