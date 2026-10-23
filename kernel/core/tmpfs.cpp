#include "chimera/tmpfs.h"
#include <stddef.h>
#include <stdint.h>

#if defined(_MSC_VER)
#include <intrin.h>
#endif

struct TmpNode {
    char *name;
    uint32_t name_length;
    uint32_t type;
    uint32_t mode;
    uint64_t size;
    uint8_t *data;
    TmpNode *parent;
    TmpNode *children;
    TmpNode *next;
};
struct chimera_tmpfs {
    chimera_ramfs_allocator allocator;
    chimera_tmpfs_limits limits;
    TmpNode *root;
    uint32_t entries;
    uint64_t total_bytes;
    uint8_t lock_word;
};

namespace {
#if defined(_MSC_VER)
static void fs_lock(chimera_tmpfs *fs) {
    while (_InterlockedExchange8(reinterpret_cast<volatile char *>(&fs->lock_word), 1) != 0) {}
}
static void fs_unlock(chimera_tmpfs *fs) {
    (void)_InterlockedExchange8(reinterpret_cast<volatile char *>(&fs->lock_word), 0);
}
#else
static void fs_lock(chimera_tmpfs *fs) { while (__atomic_test_and_set(&fs->lock_word, __ATOMIC_ACQUIRE)) {} }
static void fs_unlock(chimera_tmpfs *fs) { __atomic_clear(&fs->lock_word, __ATOMIC_RELEASE); }
#endif
static uint32_t str_len(const char *s,uint32_t limit) { if(!s)return limit+1u;uint32_t n=0;while(n<=limit&&s[n])++n;return n; }
static void copy_bytes(void *dst,const void *src,uint64_t n) { auto*d=static_cast<uint8_t*>(dst);const auto*s=static_cast<const uint8_t*>(src);for(uint64_t i=0;i<n;i++)d[i]=s[i]; }
static void zero_bytes(void *dst,uint64_t n) { auto*d=static_cast<uint8_t*>(dst);for(uint64_t i=0;i<n;i++)d[i]=0; }
static bool same(const char*a,const char*b,uint32_t n){for(uint32_t i=0;i<n;i++)if(a[i]!=b[i])return false;return true;}
static bool equal(const char*a,const char*b){uint32_t i=0;while(a[i]&&b[i]&&a[i]==b[i])++i;return a[i]==b[i];}
static TmpNode *alloc_node(chimera_tmpfs *fs,const char *name,uint32_t len,uint32_t type,uint32_t mode,TmpNode *parent){
    auto*n=static_cast<TmpNode*>(fs->allocator.alloc(sizeof(TmpNode),fs->allocator.context));if(!n)return nullptr;
    n->name=nullptr;n->name_length=len;n->type=type;n->mode=mode;n->size=0;n->data=nullptr;n->parent=parent;n->children=nullptr;n->next=nullptr;
    n->name=static_cast<char*>(fs->allocator.alloc((uint64_t)len+1u,fs->allocator.context));
    if(!n->name){fs->allocator.free(n,fs->allocator.context);return nullptr;}
    copy_bytes(n->name,name,len);n->name[len]=0;return n;
}
static void free_node(chimera_tmpfs *fs,TmpNode*n){
    if (!n) return;
    TmpNode *c = n->children;
    while (c) { TmpNode *next = c->next; free_node(fs, c); c = next; }
    if(n->data)fs->allocator.free(n->data,fs->allocator.context);
    if(n->name)fs->allocator.free(n->name,fs->allocator.context);
    fs->allocator.free(n,fs->allocator.context);
}
static bool canonical(const char *path,uint32_t max_path){
    if (!path || path[0] != '/') return false;
    uint32_t n = str_len(path, max_path);
    if (!n || n > max_path) return false;
    for(uint32_t i=0;i<n;){while(path[i]=='/')++i;if(!path[i])break;uint32_t s=i;while(path[i]&&path[i]!='/')++i;uint32_t l=i-s;
        if((l==1u&&path[s]=='.')||(l==2u&&path[s]=='.'&&path[s+1u]=='.'))return false;
    }return true;
}
static TmpNode *find_node(chimera_tmpfs*fs,const char*path){
    if(!canonical(path,fs->limits.max_path_bytes))return nullptr;
    TmpNode*cur=fs->root;uint32_t i=0;while(path[i]=='/')++i;
    while(path[i]){
        uint32_t s=i;while(path[i]&&path[i]!='/')++i;uint32_t l=i-s;
        TmpNode*found=nullptr;for(TmpNode*c=cur->children;c;c=c->next)if(c->name_length==l&&same(c->name,path+s,l)){found=c;break;}
        if (!found) return nullptr;
        cur = found;
        while (path[i] == '/') ++i;
    }return cur;
}
static bool split_parent(chimera_tmpfs*fs,const char*path,TmpNode**parent,const char**base,uint32_t*base_len){
    if(!canonical(path,fs->limits.max_path_bytes)||equal(path,"/"))return false;
    uint32_t n=str_len(path,fs->limits.max_path_bytes),s=n;while(s&&path[s-1u]!='/')--s;
    *base=path+s;*base_len=n-s;
    if(s<=1u)*parent=fs->root;
    else {char tmp[CHIMERA_VFS_MAX_PATH+1u];uint32_t len=s-1u;copy_bytes(tmp,path,len);tmp[len]=0;*parent=find_node(fs,tmp);}
    return *parent&&(*parent)->type==CHIMERA_VFS_DIRECTORY&&*base_len;
}
static TmpNode *find_child(TmpNode*p,const char*name,uint32_t len){for(TmpNode*c=p->children;c;c=c->next)if(c->name_length==len&&same(c->name,name,len))return c;return nullptr;}
static void attach(TmpNode*p,TmpNode*n){n->parent=p;n->next=p->children;p->children=n;}
static bool detach(TmpNode*p,TmpNode*n){TmpNode**at=&p->children;while(*at){if(*at==n){*at=n->next;n->next=nullptr;return true;}at=&(*at)->next;}return false;}
static int create_node(chimera_tmpfs*fs,const char*path,uint32_t type,uint32_t mode){
    if(type!=CHIMERA_VFS_REGULAR&&type!=CHIMERA_VFS_DIRECTORY)return -22;
    TmpNode*p=nullptr;const char*base=nullptr;uint32_t len=0;if(!split_parent(fs,path,&p,&base,&len))return -22;
    if(len>fs->limits.max_path_bytes||find_child(p,base,len))return -17;
    if(fs->entries>=fs->limits.max_entries)return -28;
    TmpNode*n=alloc_node(fs,base,len,type,mode,p);if(!n)return -12;attach(p,n);++fs->entries;return 0;
}
static int tmp_lookup(void*ctx,const char*path,chimera_vfs_stat*out){
    auto*fs=static_cast<chimera_tmpfs*>(ctx);if(!fs||!out)return -22;fs_lock(fs);TmpNode*n=find_node(fs,path);
    if(!n){fs_unlock(fs);return -2;}out->size=n->size;out->type=n->type;out->mode=n->mode;fs_unlock(fs);return 0;
}
static int tmp_read(void*ctx,const char*path,uint64_t off,void*buf,uint64_t len,uint64_t*out){
    auto*fs=static_cast<chimera_tmpfs*>(ctx);if(!fs||!out||(!buf&&len))return -22;fs_lock(fs);TmpNode*n=find_node(fs,path);
    if(!n){fs_unlock(fs);return -2;}if(n->type!=CHIMERA_VFS_REGULAR){fs_unlock(fs);return -21;}
    uint64_t amount=off>=n->size?0:n->size-off;if(amount>len)amount=len;if(amount)copy_bytes(buf,n->data+off,amount);*out=amount;fs_unlock(fs);return 0;
}
static int tmp_write(void*ctx,const char*path,uint64_t off,const void*buf,uint64_t len,uint64_t*out){
    auto*fs=static_cast<chimera_tmpfs*>(ctx);if(!fs||!out||(!buf&&len))return -22;fs_lock(fs);TmpNode*n=find_node(fs,path);
    if(!n){fs_unlock(fs);return -2;}if(n->type!=CHIMERA_VFS_REGULAR){fs_unlock(fs);return -21;}
    if(!len){*out=0;fs_unlock(fs);return 0;}if(off>UINT64_MAX-len){fs_unlock(fs);return -75;}
    uint64_t new_size=off+len;if(new_size<n->size)new_size=n->size;
    if(new_size>fs->limits.max_file_bytes){fs_unlock(fs);return -27;}
    uint64_t total=fs->total_bytes-n->size;if(total>fs->limits.max_total_bytes||new_size>fs->limits.max_total_bytes-total){fs_unlock(fs);return -28;}
    auto*data=static_cast<uint8_t*>(fs->allocator.alloc(new_size,fs->allocator.context));if(!data){fs_unlock(fs);return -12;}
    zero_bytes(data,new_size);if(n->size)copy_bytes(data,n->data,n->size);copy_bytes(data+off,buf,len);
    if (n->data) fs->allocator.free(n->data, fs->allocator.context);
    n->data = data;
    n->size = new_size;
    fs->total_bytes = total + new_size;
    *out = len;
    fs_unlock(fs);
    return 0;
}
static int tmp_create(void*ctx,const char*path,uint32_t type,uint32_t mode){auto*fs=static_cast<chimera_tmpfs*>(ctx);if(!fs)return -22;fs_lock(fs);int rc=create_node(fs,path,type,mode);fs_unlock(fs);return rc;}
static int tmp_truncate(void*ctx,const char*path,uint64_t size){
    auto*fs=static_cast<chimera_tmpfs*>(ctx);if(!fs)return -22;fs_lock(fs);TmpNode*n=find_node(fs,path);
    if(!n){fs_unlock(fs);return -2;}if(n->type!=CHIMERA_VFS_REGULAR){fs_unlock(fs);return -21;}
    if(size>fs->limits.max_file_bytes){fs_unlock(fs);return -27;}uint64_t total=fs->total_bytes-n->size;
    if(total>fs->limits.max_total_bytes||size>fs->limits.max_total_bytes-total){fs_unlock(fs);return -28;}
    uint8_t*data=nullptr;if(size){data=static_cast<uint8_t*>(fs->allocator.alloc(size,fs->allocator.context));if(!data){fs_unlock(fs);return -12;}zero_bytes(data,size);uint64_t copy=n->size<size?n->size:size;if(copy)copy_bytes(data,n->data,copy);}
    if (n->data) fs->allocator.free(n->data, fs->allocator.context);
    n->data = data;
    n->size = size;
    fs->total_bytes = total + size;
    fs_unlock(fs);
    return 0;
}
static int tmp_mkdir(void*ctx,const char*path,uint32_t mode){auto*fs=static_cast<chimera_tmpfs*>(ctx);if(!fs)return -22;fs_lock(fs);int rc=create_node(fs,path,CHIMERA_VFS_DIRECTORY,mode);fs_unlock(fs);return rc;}
static int tmp_unlink(void*ctx,const char*path,uint32_t directory){
    auto*fs=static_cast<chimera_tmpfs*>(ctx);if(!fs)return -22;fs_lock(fs);TmpNode*p=nullptr;const char*base=nullptr;uint32_t len=0;
    if(!split_parent(fs,path,&p,&base,&len)){fs_unlock(fs);return -22;}TmpNode*n=find_child(p,base,len);
    if(!n){fs_unlock(fs);return -2;}if((n->type==CHIMERA_VFS_DIRECTORY)!=(directory!=0u)){fs_unlock(fs);return n->type==CHIMERA_VFS_DIRECTORY?-21:-20;}
    if(n->type==CHIMERA_VFS_DIRECTORY&&n->children){fs_unlock(fs);return -39;}
    if(!detach(p,n)){fs_unlock(fs);return -5;}fs->total_bytes-=n->size;--fs->entries;free_node(fs,n);fs_unlock(fs);return 0;
}
static int tmp_rename(void*ctx,const char*oldp,const char*newp){
    auto*fs=static_cast<chimera_tmpfs*>(ctx);if(!fs)return -22;fs_lock(fs);TmpNode*old_parent=nullptr;const char*old_base=nullptr;uint32_t old_len=0;
    TmpNode*new_parent=nullptr;const char*new_base=nullptr;uint32_t new_len=0;
    if(!split_parent(fs,oldp,&old_parent,&old_base,&old_len)||!split_parent(fs,newp,&new_parent,&new_base,&new_len)){fs_unlock(fs);return -22;}
    TmpNode*n=find_child(old_parent,old_base,old_len);if(!n){fs_unlock(fs);return -2;}if(find_child(new_parent,new_base,new_len)){fs_unlock(fs);return -17;}
    if(new_len>fs->limits.max_path_bytes){fs_unlock(fs);return -36;}
    if(n->type==CHIMERA_VFS_DIRECTORY){for(TmpNode*p=new_parent;p;p=p->parent)if(p==n){fs_unlock(fs);return -22;}}
    auto*name=static_cast<char*>(fs->allocator.alloc((uint64_t)new_len+1u,fs->allocator.context));if(!name){fs_unlock(fs);return -12;}
    copy_bytes(name,new_base,new_len);name[new_len]=0;
    if(!detach(old_parent,n)){fs->allocator.free(name,fs->allocator.context);fs_unlock(fs);return -5;}
    fs->allocator.free(n->name,fs->allocator.context);n->name=name;n->name_length=new_len;attach(new_parent,n);fs_unlock(fs);return 0;
}
static int tmp_sync(void*){return 0;}
static const chimera_vfs_ops ops={tmp_lookup,tmp_read,tmp_write,tmp_create,tmp_truncate,tmp_mkdir,tmp_unlink,tmp_rename,tmp_sync};
}

extern "C" int chimera_tmpfs_create(const chimera_ramfs_allocator *allocator,const chimera_tmpfs_limits *limits,chimera_tmpfs **out){
    if (out) *out = nullptr;
    if (!allocator || !allocator->alloc || !allocator->free || !limits || !out ||
       !limits->max_entries||limits->max_entries>CHIMERA_RAMFS_MAX_ENTRIES||
       !limits->max_path_bytes||limits->max_path_bytes>CHIMERA_VFS_MAX_PATH||
       !limits->max_file_bytes||!limits->max_total_bytes||limits->max_file_bytes>limits->max_total_bytes)return -22;
    auto*fs=static_cast<chimera_tmpfs*>(allocator->alloc(sizeof(chimera_tmpfs),allocator->context));if(!fs)return -12;
    fs->allocator=*allocator;fs->limits=*limits;fs->root=nullptr;fs->entries=0;fs->total_bytes=0;fs->lock_word=0;
    fs->root=alloc_node(fs,"/",1u,CHIMERA_VFS_DIRECTORY,0755u,nullptr);if(!fs->root){allocator->free(fs,allocator->context);return -12;}
    fs->entries=1u;*out=fs;return 0;
}
extern "C" void chimera_tmpfs_destroy(chimera_tmpfs*fs){if(!fs)return;const auto a=fs->allocator;free_node(fs,fs->root);a.free(fs,a.context);}
extern "C" const chimera_vfs_ops *chimera_tmpfs_vfs_ops(void){return &ops;}
