#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include "chimera/vfs.h"
static uint8_t archive[4096];
static size_t used=0;
static void pad4(){while(used&3u)archive[used++]=0;}
static void entry(const char*name,uint32_t mode,const char*data){
 char h[111];std::memset(h,'0',110);std::memcpy(h,"070701",6);
 auto hex=[&](unsigned off,uint32_t v){std::snprintf(h+off,9,"%08x",v);};
 hex(6,1);hex(14,mode);hex(22,0);hex(30,0);hex(38,1);hex(46,0);
 uint32_t n=(uint32_t)std::strlen(name)+1,z=(uint32_t)std::strlen(data);
 hex(54,z);hex(62,0);hex(70,0);hex(78,0);hex(86,0);hex(94,n);hex(102,0);
 std::memcpy(archive+used,h,110);used+=110;std::memcpy(archive+used,name,n);used+=n;pad4();
 if(z){std::memcpy(archive+used,data,z);used+=z;}pad4();
}
int main(){
 entry("./etc/os-release",0100644,"NAME=Chimera\nVERSION=2\n");
 entry("TRAILER!!!",0,"");
 assert(koronos_vfs_mount_cpio(archive,used)==0);
 assert(koronos_vfs_is_mounted()==1&&koronos_vfs_file_count()==1);
 int fd=koronos_vfs_open("/etc/os-release",0);assert(fd>=0);
 char out[64]{};assert(koronos_vfs_read(fd,out,sizeof(out))==23);
 assert(std::strcmp(out,"NAME=Chimera\nVERSION=2\n")==0);
 assert(koronos_vfs_seek(fd,5,0)==5);std::memset(out,0,sizeof(out));
 assert(koronos_vfs_read(fd,out,4)==4&&std::strcmp(out,"Chim")==0);
 assert(koronos_vfs_close(fd)==0);
 int tmp=koronos_vfs_open("/tmp/session",1);assert(tmp>=0);
 assert(koronos_vfs_write(tmp,"ready",5)==5);
 assert(koronos_vfs_seek(tmp,0,0)==0);
 std::memset(out,0,sizeof(out));assert(koronos_vfs_read(tmp,out,5)==5);
 assert(std::strcmp(out,"ready")==0);assert(koronos_vfs_close(tmp)==0);
 assert(koronos_vfs_open("/etc/../etc/os-release",0)<0);
 return 0;
}
