#include "chimera/vfs.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
int main(){
 chimera_vfs fs{};chimera_vfs_node nodes[4]{};uint8_t data[256]{};
 assert(chimera_vfs_init(&fs,nodes,4,data,sizeof(data),64)==0);
 assert(chimera_vfs_create(&fs,"/home/user/note.txt",0640,1000,100)==0);
 assert(chimera_vfs_create(&fs,"home/user/note.txt",0600,1000,100)==CHIMERA_VFS_EEXIST);
 const char initial[]="hello";assert(chimera_vfs_write(&fs,"/home/user/note.txt",0,initial,5,1000,100)==5);
 char buf[16]{};assert(chimera_vfs_read(&fs,"home/user/note.txt",0,buf,sizeof(buf),1000,100)==5);assert(!strcmp(buf,"hello"));
 const char patch[]="A";assert(chimera_vfs_write(&fs,"home/user/note.txt",1,patch,1,1000,100)==1);
 assert(chimera_vfs_read(&fs,"home/user/note.txt",0,buf,sizeof(buf),1000,100)==5);assert(!strcmp(buf,"hAllo"));
 assert(chimera_vfs_read(&fs,"home/user/note.txt",0,buf,1,2000,200)==CHIMERA_VFS_EACCES);
 assert(chimera_vfs_write(&fs,"home/user/note.txt",0,patch,1,2000,200)==CHIMERA_VFS_EACCES);
 assert(chimera_vfs_chmod(&fs,"home/user/note.txt",0600,1000,100)==0);
 assert(chimera_vfs_chown(&fs,"home/user/note.txt",2000,200,1000)==CHIMERA_VFS_EACCES);
 assert(chimera_vfs_chown(&fs,"home/user/note.txt",2000,200,0)==0);
 chimera_vfs_stat st{};assert(chimera_vfs_stat_path(&fs,"home/user/note.txt",0,0,&st)==0);
 assert(st.uid==2000&&st.gid==200&&st.size==5&&st.mode==0600);
 assert(chimera_vfs_truncate(&fs,"home/user/note.txt",2,2000,200)==0);
 assert(chimera_vfs_read(&fs,"home/user/note.txt",0,buf,sizeof(buf),2000,200)==2);
 assert(chimera_vfs_write(&fs,"home/user/note.txt",63,initial,5,2000,200)==CHIMERA_VFS_EFBIG);
 assert(chimera_vfs_create(&fs,"../escape",0600,0,0)==CHIMERA_VFS_EINVAL);
 assert(chimera_vfs_unlink(&fs,"home/user/note.txt",1000,100)==CHIMERA_VFS_EACCES);
 assert(chimera_vfs_unlink(&fs,"home/user/note.txt",2000,200)==0);
 assert(chimera_vfs_stat_path(&fs,"home/user/note.txt",0,0,&st)==CHIMERA_VFS_ENOENT);
 return 0;
}