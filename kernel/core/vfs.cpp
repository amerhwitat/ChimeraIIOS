#include "chimera/vfs.h"
#include <stddef.h>

namespace {
struct Node {
    char path[CHIMERA_VFS_PATH_MAX];
    uint8_t data[CHIMERA_VFS_FILE_MAX];
    uint32_t size;
    uint32_t type;
    bool used;
};
Node nodes[CHIMERA_VFS_MAX_NODES];
volatile uint32_t vfs_lock = 0;
uint32_t node_count = 0;
bool initialized = false;

void lock() { while (__sync_lock_test_and_set(&vfs_lock, 1u)) {} }
void unlock() { __sync_lock_release(&vfs_lock); }
uint64_t len(const char *s) { uint64_t n=0; if (s) while (s[n]) ++n; return n; }
bool eq(const char *a, const char *b) {
    if (!a || !b) return false;
    uint64_t i=0; while (a[i] && b[i] && a[i]==b[i]) ++i;
    return a[i]==b[i];
}
void copy(char *d, const char *s, uint64_t n) { for (uint64_t i=0;i<n;++i) d[i]=s[i]; }
void zero(void *p, uint64_t n) { auto *b=static_cast<uint8_t*>(p); for(uint64_t i=0;i<n;++i)b[i]=0; }
bool valid_path(const char *p, uint64_t *n_out) {
    if (!p || p[0]!='/' ) return false;
    const uint64_t n=len(p);
    if (!n || n>=CHIMERA_VFS_PATH_MAX) return false;
    if (n==1) { *n_out=n; return true; }
    uint64_t segment=0;
    for (uint64_t i=1;i<=n;++i) {
        const char c=p[i];
        if (c=='/' || c==0) {
            const uint64_t size=i-segment-1;
            if (!size) return false;
            if ((size==1 && p[segment+1]=='.') ||
                (size==2 && p[segment+1]=='.' && p[segment+2]=='.')) return false;
            segment=i;
        }
    }
    *n_out=n; return true;
}
int find(const char *p) {
    for (uint32_t i=0;i<CHIMERA_VFS_MAX_NODES;++i)
        if (nodes[i].used && eq(nodes[i].path,p)) return static_cast<int>(i);
    return -1;
}
int free_slot() {
    for (uint32_t i=0;i<CHIMERA_VFS_MAX_NODES;++i) if(!nodes[i].used)return static_cast<int>(i);
    return -1;
}
bool parent_exists(const char *p, uint64_t n) {
    if (n==1) return true;
    uint64_t cut=n;
    while (cut>1 && p[cut-1]!='/') --cut;
    if (cut<=1) return find("/")<0; // root is implicit
    char parent[CHIMERA_VFS_PATH_MAX];
    const uint64_t plen=cut-1;
    copy(parent,p,plen); parent[plen]=0;
    const int ix=find(parent);
    return ix>=0 && nodes[ix].type==CHIMERA_VFS_DIRECTORY;
}
bool child_exists(const char *parent, const char *candidate) {
    const uint64_t plen=len(parent);
    for(uint32_t i=0;i<CHIMERA_VFS_MAX_NODES;++i) {
        if(!nodes[i].used || !nodes[i].path) continue;
        const char *p=nodes[i].path;
        if(!eq(p,candidate) && p[0]=='/' ) {
            uint64_t n=len(p);
            if(n>plen && p[plen]=='/' ) {
                bool prefix=true;
                for(uint64_t j=0;j<plen;++j) if(p[j]!=parent[j]) {prefix=false;break;}
                if(prefix) return true;
            }
        }
    }
    return false;
}
int add_node(const char *p, uint64_t n, uint32_t type) {
    if (find(p)>=0 || !parent_exists(p,n)) return -1;
    const int slot=free_slot(); if(slot<0)return -2;
    Node &node=nodes[slot]; zero(&node,sizeof(node)); copy(node.path,p,n); node.path[n]=0;
    node.type=type; node.used=true; ++node_count; return 0;
}
}

extern "C" int chimera_vfs_init(void) {
    lock();
    zero(nodes,sizeof(nodes)); node_count=0; initialized=true;
    unlock(); return 0;
}
extern "C" int chimera_vfs_mkdir(const char *path) {
    uint64_t n=0; if(!valid_path(path,&n) || n==1)return -22;
    lock(); if(!initialized){unlock();return -19;}
    const int rc=add_node(path,n,CHIMERA_VFS_DIRECTORY); unlock(); return rc;
}
extern "C" int chimera_vfs_create(const char *path) {
    uint64_t n=0; if(!valid_path(path,&n) || n==1)return -22;
    lock(); if(!initialized){unlock();return -19;}
    const int rc=add_node(path,n,CHIMERA_VFS_REGULAR); unlock(); return rc;
}
extern "C" int chimera_vfs_stat_path(const char *path, chimera_vfs_stat *out) {
    uint64_t n=0; if(!out || !valid_path(path,&n))return -22;
    lock(); if(!initialized){unlock();return -19;}
    if(n==1){out->type=CHIMERA_VFS_DIRECTORY;out->size=0;unlock();return 0;}
    const int i=find(path); if(i<0){unlock();return -2;}
    out->type=nodes[i].type;out->size=nodes[i].size;unlock();return 0;
}
extern "C" int64_t chimera_vfs_read(const char *path,uint64_t offset,void *buffer,uint64_t length) {
    uint64_t n=0; if(!valid_path(path,&n) || (!buffer && length))return -22;
    lock(); if(!initialized){unlock();return -19;}
    const int i=find(path); if(i<0){unlock();return -2;}
    Node &node=nodes[i]; if(node.type!=CHIMERA_VFS_REGULAR){unlock();return -21;}
    if(offset>=node.size || !length){unlock();return 0;}
    uint64_t amount=node.size-offset; if(amount>length)amount=length;
    copy(static_cast<char*>(buffer),reinterpret_cast<const char*>(node.data+offset),amount);
    unlock();return static_cast<int64_t>(amount);
}
extern "C" int64_t chimera_vfs_write(const char *path,uint64_t offset,const void *buffer,uint64_t length) {
    uint64_t n=0; if(!valid_path(path,&n) || (!buffer && length))return -22;
    if(offset>CHIMERA_VFS_FILE_MAX || length>CHIMERA_VFS_FILE_MAX-offset)return -27;
    lock(); if(!initialized){unlock();return -19;}
    const int i=find(path); if(i<0){unlock();return -2;}
    Node &node=nodes[i]; if(node.type!=CHIMERA_VFS_REGULAR){unlock();return -21;}
    if(offset>node.size)zero(node.data+node.size,offset-node.size);
    const auto *src=static_cast<const uint8_t*>(buffer);
    for(uint64_t j=0;j<length;++j)node.data[offset+j]=src[j];
    const uint64_t end=offset+length;if(end>node.size)node.size=static_cast<uint32_t>(end);
    unlock();return static_cast<int64_t>(length);
}
extern "C" int chimera_vfs_truncate(const char *path,uint64_t length) {
    uint64_t n=0;if(!valid_path(path,&n) || length>CHIMERA_VFS_FILE_MAX)return -22;
    lock();if(!initialized){unlock();return -19;}
    const int i=find(path);if(i<0){unlock();return -2;}
    Node &node=nodes[i];if(node.type!=CHIMERA_VFS_REGULAR){unlock();return -21;}
    if(length>node.size)zero(node.data+node.size,length-node.size);
    else zero(node.data+length,node.size-length);
    node.size=static_cast<uint32_t>(length);unlock();return 0;
}
extern "C" int chimera_vfs_unlink(const char *path) {
    uint64_t n=0;if(!valid_path(path,&n) || n==1)return -22;
    lock();if(!initialized){unlock();return -19;}
    const int i=find(path);if(i<0){unlock();return -2;}
    if(nodes[i].type==CHIMERA_VFS_DIRECTORY && child_exists(path,path)){unlock();return -39;}
    zero(&nodes[i],sizeof(Node));--node_count;unlock();return 0;
}
extern "C" int chimera_vfs_rename(const char *old_path,const char *new_path) {
    uint64_t a=0,b=0;if(!valid_path(old_path,&a)||!valid_path(new_path,&b)||a==1||b==1)return -22;
    if(b>=CHIMERA_VFS_PATH_MAX)return -36;
    lock();if(!initialized){unlock();return -19;}
    const int i=find(old_path);if(i<0){unlock();return -2;}
    if(find(new_path)>=0 || !parent_exists(new_path,b)){unlock();return -17;}
    if(nodes[i].type==CHIMERA_VFS_DIRECTORY) {
        // Do not permit moving a directory beneath itself.
        if(b>a) { bool prefix=true;for(uint64_t j=0;j<a;++j)if(old_path[j]!=new_path[j]){prefix=false;break;}
            if(prefix && new_path[a]=='/') {unlock();return -22;} }
        if(child_exists(old_path,old_path)){unlock();return -95;} // directory tree rename is not yet atomic/supported
    }
    zero(nodes[i].path,sizeof(nodes[i].path));copy(nodes[i].path,new_path,b);nodes[i].path[b]=0;
    unlock();return 0;
}
extern "C" uint32_t chimera_vfs_node_count(void) { lock();const uint32_t n=node_count;unlock();return n; }
