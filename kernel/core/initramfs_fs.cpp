#include "chimera/initramfs_fs.h"
#include "chimera/initramfs_newc.h"

namespace {
enum NodeType : uint32_t { NODE_DIR=1, NODE_FILE=2, NODE_SYMLINK=3 };
struct Node {
    char name[KORONOS_INITRAMFS_NAME_MAX + 1u];
    const uint8_t *data;
    uint64_t size;
    uint32_t mode, uid, gid, type, parent;
    uint32_t tmpfs_offset, tmpfs_capacity;
    uint8_t writable, used;
};
static Node nodes[KORONOS_INITRAMFS_MAX_NODES];
static uint32_t node_count = 0;
static bool mounted = false;
static uint32_t tmpfs_root = 0;
static uint32_t tmpfs_used = 0;
static uint8_t tmpfs_data[1024u * 1024u];
static constexpr uint32_t TMPFS_FILE_CAPACITY = 4096u;

static void clear_nodes() {
    for (uint32_t i=0;i<KORONOS_INITRAMFS_MAX_NODES;i++) nodes[i] = {};
    node_count = 0;
    mounted = false;
    tmpfs_root = 0;
    tmpfs_used = 0;
}
static uint32_t find_child(uint32_t parent,const char *name,uint32_t length) {
    for(uint32_t i=1;i<=node_count;i++) {
        if(!nodes[i].used || nodes[i].parent!=parent) continue;
        uint32_t n=0; while(n<=KORONOS_INITRAMFS_NAME_MAX && nodes[i].name[n]) ++n;
        if(n!=length) continue;
        uint32_t j=0; for(;j<length && nodes[i].name[j]==name[j];++j) {}
        if(j==length) return i;
    }
    return 0;
}
static uint32_t add_node(uint32_t parent,const char *name,uint32_t length,uint32_t type,
                         uint32_t mode,uint32_t uid,uint32_t gid,
                         const uint8_t *data,uint64_t size) {
    if(length==0 || length>KORONOS_INITRAMFS_NAME_MAX) return 0;
    uint32_t existing=find_child(parent,name,length);
    if(existing) {
        Node &n=nodes[existing];
        if(n.type!=NODE_DIR || type==NODE_DIR) {
            if(n.type!=type) return 0;
            if(type!=NODE_DIR) return 0;
        }
        n.mode=mode; n.uid=uid; n.gid=gid; n.data=data; n.size=size;
        return existing;
    }
    if(node_count+1u>=KORONOS_INITRAMFS_MAX_NODES) return 0;
    const uint32_t id=++node_count;
    Node &n=nodes[id]; n={};
    for(uint32_t i=0;i<length;i++) n.name[i]=name[i];
    n.name[length]=0; n.parent=parent; n.type=type; n.mode=mode;
    n.uid=uid; n.gid=gid; n.data=data; n.size=size; n.used=1;
    return id;
}
static int add_entry(void *,const koronos_newc_entry *entry) {
    if(!entry || !entry->name) return -1;
    const char *path=entry->name;
    uint32_t length=entry->name_size;
    uint32_t pos=0;
    if(length==1u && path[0]=='.') return 0;
    if(length==2u && path[0]=='.' && path[1]=='/') return 0;
    if(length>=2 && path[0]=='.' && path[1]=='/') pos=2;
    if(pos==length) return 0; // archive root directory entry
    uint32_t parent=0;
    while(pos<length) {
        if(parent!=0 && nodes[parent].type!=NODE_DIR) return -5;
        uint32_t end=pos;
        while(end<length && path[end]!='/') ++end;
        if(end==pos) return -2;
        const bool last=(end==length);
        uint32_t type=NODE_DIR;
        if(last) {
            const uint32_t mode_type=entry->mode & KORONOS_NEWC_TYPE_MASK;
            if(mode_type==KORONOS_NEWC_REG) type=NODE_FILE;
            else if(mode_type==KORONOS_NEWC_SYMLINK) type=NODE_SYMLINK;
            else if(mode_type!=KORONOS_NEWC_DIR) return -3;
        }
        const uint32_t mode=last?entry->mode:KORONOS_NEWC_DIR|0755u;
        const uint8_t *data=last?entry->data:nullptr;
        const uint64_t size=last?entry->file_size:0;
        const uint32_t id=add_node(parent,path+pos,end-pos,type,mode,
                                   last?entry->uid:0,last?entry->gid:0,data,size);
        if(!id) return -4;
        parent=id;
        pos=end+1u;
    }
    return 0;
}
static bool valid_path(const char *path,uint32_t *start) {
    if(!path || !start) return false;
    uint32_t i=0;
    if(path[0]=='/') i=1;
    if(path[i]=='.' && path[i+1]=='/') i+=2;
    *start=i;
    return true;
}
}
extern "C" void koronos_initramfs_unmount(void) { clear_nodes(); }
extern "C" int koronos_initramfs_mount(const void *archive,uint64_t size) {
    clear_nodes();
    nodes[0].used=1; nodes[0].type=NODE_DIR; nodes[0].mode=KORONOS_NEWC_DIR|0755u;
    node_count=0;
    koronos_newc_result result{};
    if(koronos_newc_walk(archive,size,add_entry,nullptr,&result)!=0) {
        clear_nodes(); return -1;
    }
    uint32_t tmp = find_child(0,"tmp",3u);
    if (tmp && nodes[tmp].type != NODE_DIR) { clear_nodes(); return -2; }
    if (!tmp) tmp = add_node(0,"tmp",3u,NODE_DIR,KORONOS_NEWC_DIR|01777u,0,0,nullptr,0);
    if (!tmp) { clear_nodes(); return -3; }

    /* /tmp is a RAM mount, not a writable view of the archive. Mask every
       archive-provided child so stale or attacker-controlled initramfs files
       cannot leak into the volatile namespace. Descendants become unreachable
       when their direct parent is detached. */
    for (uint32_t i=1;i<=node_count;i++) {
        if (nodes[i].used && nodes[i].parent==tmp) {
            nodes[i].used=0;
            nodes[i].data=nullptr;
            nodes[i].size=0;
            nodes[i].writable=0;
        }
    }
    nodes[tmp].mode=KORONOS_NEWC_DIR|01777u;
    nodes[tmp].data=nullptr;
    nodes[tmp].size=0;
    tmpfs_root = tmp;
    mounted=true; return 0;
}
extern "C" int koronos_initramfs_lookup(const char *path,uint32_t *out) {
    if(!mounted || !path || !out) return -1;
    uint32_t pos=0;
    if(!valid_path(path,&pos)) return -2;
    uint32_t current=0;
    while(path[pos]) {
        uint32_t end=pos; while(path[end] && path[end]!='/') ++end;
        if(end==pos) return -3;
        if(end-pos>KORONOS_INITRAMFS_NAME_MAX) return -4;
        current=find_child(current,path+pos,end-pos);
        if(!current) return -5;
        pos=end;
        if(path[pos]=='/') ++pos;
    }
    *out=current; return 0;
}
extern "C" int koronos_initramfs_stat_node(uint32_t id,koronos_initramfs_stat *out) {
    if(!mounted || !out || id>=KORONOS_INITRAMFS_MAX_NODES || !nodes[id].used) return -1;
    const Node &n=nodes[id]; out->mode=n.mode; out->uid=n.uid; out->gid=n.gid;
    out->type=n.type; out->size=n.size; return 0;
}
extern "C" int koronos_initramfs_read(uint32_t id,uint64_t offset,void *buffer,
                                       uint64_t length,uint64_t *read_count) {
    if(read_count) *read_count=0;
    if(!mounted || !buffer || !read_count || id>=KORONOS_INITRAMFS_MAX_NODES ||
       !nodes[id].used || nodes[id].type!=NODE_FILE) return -1;
    const Node &n=nodes[id];
    if(offset>=n.size || length==0) return 0;
    uint64_t count=length;
    if(count>n.size-offset) count=n.size-offset;
    uint8_t *dst=static_cast<uint8_t*>(buffer);
    for(uint64_t i=0;i<count;i++) dst[i]=n.data[offset+i];
    *read_count=count; return 0;
}
extern "C" uint32_t koronos_initramfs_node_count(void) {
    if (!mounted) return 0;
    uint32_t count=0;
    for (uint32_t i=0;i<=node_count;i++) if (nodes[i].used) ++count;
    return count;
}
extern "C" int koronos_tmpfs_create(const char *path,uint32_t *out) {
    if (!mounted || !path || !out || !tmpfs_root) return -1;
    const char prefix[]="/tmp/";
    uint32_t i=0; while(prefix[i] && path[i]==prefix[i]) ++i;
    if (prefix[i] || i!=5u) return -2;
    uint32_t length=0; while(path[i+length]) ++length;
    if (!length || length>KORONOS_INITRAMFS_NAME_MAX || tmpfs_used+TMPFS_FILE_CAPACITY>sizeof(tmpfs_data)) return -3;
    if ((length==1u && path[i]=='.') ||
        (length==2u && path[i]=='.' && path[i+1u]=='.')) return -4;
    for(uint32_t j=0;j<length;j++) if(path[i+j]=='/' || path[i+j]=='\\') return -4;
    if(find_child(tmpfs_root,path+i,length)) return -5;
    const uint32_t id=add_node(tmpfs_root,path+i,length,NODE_FILE, KORONOS_NEWC_REG|0666u,
                               0,0,tmpfs_data+tmpfs_used,0);
    if(!id) return -6;
    nodes[id].writable=1;
    nodes[id].tmpfs_offset=tmpfs_used;
    nodes[id].tmpfs_capacity=TMPFS_FILE_CAPACITY;
    tmpfs_used+=TMPFS_FILE_CAPACITY;
    *out=id; return 0;
}
extern "C" int koronos_tmpfs_write(uint32_t id,uint64_t offset,const void *buffer,
                                     uint64_t length,uint64_t *written) {
    if(written) *written=0;
    if(!mounted || !buffer || !written || id>=KORONOS_INITRAMFS_MAX_NODES ||
       !nodes[id].used || nodes[id].type!=NODE_FILE || !nodes[id].writable) return -1;
    Node &n=nodes[id];
    if(offset>n.tmpfs_capacity || length>n.tmpfs_capacity-offset) return -2;
    const uint8_t *src=static_cast<const uint8_t*>(buffer);
    uint8_t *dst=tmpfs_data+n.tmpfs_offset+offset;
    for(uint64_t i=0;i<length;i++) dst[i]=src[i];
    if(offset+length>n.size) n.size=offset+length;
    *written=length; return 0;
}
