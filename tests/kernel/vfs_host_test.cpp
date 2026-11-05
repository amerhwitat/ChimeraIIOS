#include "chimera/vfs.h"
#include <assert.h>
#include <string.h>
int main() {
    assert(koronos_vfs_init()==0);
    assert(koronos_vfs_mount_tmpfs()==0);
    int r=koronos_vfs_open("/etc/os-release",KORONOS_VFS_O_RDONLY);
    assert(r>=0);
    char release[128]={};
    int64_t n=koronos_vfs_read(r,release,sizeof(release)-1);
    assert(n>0 && strstr(release,"ID=koronos")!=nullptr);
    assert(koronos_vfs_close(r)==0);
    int w=koronos_vfs_open("/tmp/vfs-test",KORONOS_VFS_O_RDWR|KORONOS_VFS_O_CREAT);
    assert(w>=0);
    const char payload[]="native-vfs";
    assert(koronos_vfs_write(w,payload,sizeof(payload)-1)==(int64_t)sizeof(payload)-1);
    assert(koronos_vfs_seek(w,0,0)==0);
    char readback[sizeof(payload)]={};
    assert(koronos_vfs_read(w,readback,sizeof(payload)-1)==(int64_t)sizeof(payload)-1);
    assert(memcmp(payload,readback,sizeof(payload)-1)==0);
    assert(koronos_vfs_close(w)==0);
    assert(koronos_vfs_open("/tmp/../etc/os-release",KORONOS_VFS_O_RDONLY)<0);
    assert(koronos_vfs_open("/etc/os-release",KORONOS_VFS_O_WRONLY)<0);
    koronos_vfs_snapshot s{};
    assert(koronos_vfs_get_snapshot(&s)==0 && !s.root_mounted && s.tmp_mounted);
    return 0;
}
