#include "chimera/vfs.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

struct TestFs { char data[64]; uint64_t size; bool exists; };
static int lookup(void *ctx,const char *path,chimera_vfs_stat *out){
    auto *fs=static_cast<TestFs*>(ctx);if(!fs||!out)return -22;
    if(strcmp(path,"/") == 0){out->size=0;out->type=CHIMERA_VFS_DIRECTORY;out->mode=0755;return 0;}
    if(strcmp(path,"/note")!=0||!fs->exists)return -2;
    out->size=fs->size;out->type=CHIMERA_VFS_REGULAR;out->mode=0644;return 0;
}
static int read_file(void *ctx,const char *path,uint64_t off,void *dst,uint64_t len,uint64_t *out){
    auto *fs=static_cast<TestFs*>(ctx);if(strcmp(path,"/note")||!fs->exists)return -2;
    *out=off>=fs->size?0:fs->size-off;if(*out>len)*out=len;memcpy(dst,fs->data+off,(size_t)*out);return 0;
}
static int write_file(void *ctx,const char *path,uint64_t off,const void *src,uint64_t len,uint64_t *out){
    auto *fs=static_cast<TestFs*>(ctx);if(strcmp(path,"/note")||!fs->exists)return -2;
    if(off>sizeof(fs->data)||len>sizeof(fs->data)-off)return -28;memcpy(fs->data+off,src,(size_t)len);if(off+len>fs->size)fs->size=off+len;*out=len;return 0;
}
static int create_file(void *ctx,const char *path,uint32_t type,uint32_t mode){
    (void)mode;auto *fs=static_cast<TestFs*>(ctx);if(strcmp(path,"/note")||fs->exists||type!=CHIMERA_VFS_REGULAR)return -17;fs->exists=true;fs->size=0;return 0;
}
static int truncate_file(void *ctx,const char *path,uint64_t size){
    auto *fs=static_cast<TestFs*>(ctx);if(strcmp(path,"/note")||!fs->exists||size>sizeof(fs->data))return -22;fs->size=size;return 0;
}
static int mkdir_file(void *,const char *,uint32_t){return -38;}
static int unlink_file(void *ctx,const char *path,uint32_t dir){(void)dir;auto *fs=static_cast<TestFs*>(ctx);if(strcmp(path,"/note")||!fs->exists)return -2;fs->exists=false;fs->size=0;return 0;}
static int rename_file(void *,const char *,const char *){return -38;}
static int sync_file(void *){return 0;}
static int fail(const char *m){fprintf(stderr,"VFS TEST FAIL: %s\n",m);return 1;}
int main(){
    TestFs fs{};const chimera_vfs_ops ops{lookup,read_file,write_file,create_file,truncate_file,mkdir_file,unlink_file,rename_file,sync_file};
    if(chimera_vfs_init()!=0)return fail("init");
    if(chimera_vfs_mount("/",&ops,&fs,0)!=0)return fail("root mount");
    if(chimera_vfs_mount("/",&ops,&fs,0)!=-17)return fail("duplicate mount must reject");
    if(chimera_vfs_open(7,"/../escape",CHIMERA_VFS_O_RDONLY,0)>=0)return fail("path traversal accepted");
    int64_t fd=chimera_vfs_open(7,"/note",CHIMERA_VFS_O_CREAT|CHIMERA_VFS_O_RDWR,0644);
    if(fd<3)return fail("create/open");
    const char msg[]="vfs-write-read";if(chimera_vfs_write(7,fd,msg,sizeof(msg))!=(int64_t)sizeof(msg))return fail("write");
    if(chimera_vfs_seek(7,fd,0,0)!=0)return fail("seek");
    char out[32]{};if(chimera_vfs_read(7,fd,out,sizeof(msg))!=(int64_t)sizeof(msg))return fail("read");
    if(memcmp(msg,out,sizeof(msg)))return fail("readback mismatch");
    if(chimera_vfs_close(8,fd)!=-9)return fail("cross-pid close accepted");
    if(chimera_vfs_close(7,fd)!=0)return fail("close");
    if(chimera_vfs_mount("/readonly",&ops,&fs,CHIMERA_VFS_MOUNT_RDONLY)!=0)return fail("readonly mount");
    if(chimera_vfs_open(7,"/readonly/note",CHIMERA_VFS_O_CREAT|CHIMERA_VFS_O_RDWR,0644)!=-30)return fail("readonly mount mutation accepted");
    fd=chimera_vfs_open(7,"/note",CHIMERA_VFS_O_RDONLY,0);if(fd<3)return fail("reopen");
    if(chimera_vfs_unmount("/")!=-16)return fail("open descriptor did not pin mount");
    if(chimera_vfs_close_process(7)!=1)return fail("process exit did not reclaim its descriptor");
    if(chimera_vfs_close(7,fd)!=-9)return fail("closed process descriptor remained usable");
    if(chimera_vfs_unmount("/")!=0)return fail("unmount");
    puts("VFS TEST PASS");return 0;
}
