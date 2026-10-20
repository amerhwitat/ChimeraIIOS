#include "chimera/vfs.h"
#include <cassert>
#include <cstring>
int main() {
    assert(chimera_vfs_init()==0);
    assert(chimera_vfs_mkdir("/tmp")==0);
    assert(chimera_vfs_create("/tmp/a")==0);
    const char data[]="filesystem";
    assert(chimera_vfs_write("/tmp/a",0,data,sizeof(data))==(long long)sizeof(data));
    char out[32]={};
    assert(chimera_vfs_read("/tmp/a",0,out,sizeof(out))==(long long)sizeof(data));
    assert(std::memcmp(out,data,sizeof(data))==0);
    assert(chimera_vfs_read("/tmp/a",4,out,3)==3 && std::memcmp(out,"sys",3)==0);
    assert(chimera_vfs_write("/tmp/a",20,"x",1)==1);
    std::memset(out,0,sizeof(out));
    assert(chimera_vfs_read("/tmp/a",sizeof(data),out,13)==13);
    assert(out[0]==0 && out[12]=='x');
    assert(chimera_vfs_truncate("/tmp/a",4)==0);
    chimera_vfs_stat st{};
    assert(chimera_vfs_stat_path("/tmp/a",&st)==0 && st.size==4);
    assert(chimera_vfs_create("/tmp/../escape")==-22);
    assert(chimera_vfs_create("/missing/file")==-1);
    assert(chimera_vfs_unlink("/tmp")==-39);
    assert(chimera_vfs_rename("/tmp/a","/tmp/b")==0);
    assert(chimera_vfs_stat_path("/tmp/a",&st)==-2);
    assert(chimera_vfs_unlink("/tmp/b")==0);
    assert(chimera_vfs_unlink("/tmp")==0);
    assert(chimera_vfs_node_count()==0);
    return 0;
}
