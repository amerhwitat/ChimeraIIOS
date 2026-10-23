#include "chimera/vfs.h"
#include <stddef.h>
#include <stdint.h>

namespace {
struct Mount {
    char path[CHIMERA_VFS_MAX_PATH + 1u];
    chimera_vfs_ops ops;
    void *context;
    uint32_t flags;
    uint32_t active_ops;
    bool active;
};
struct OpenFile {
    uint32_t pid;
    uint32_t mount_index;
    uint32_t flags;
    uint32_t generation;
    uint64_t offset;
    char path[CHIMERA_VFS_MAX_PATH + 1u];
    bool active;
};
static Mount mounts[CHIMERA_VFS_MAX_MOUNTS]{};
static OpenFile files[CHIMERA_VFS_MAX_OPEN_FILES]{};
static uint32_t next_generation = 1u;
static uint32_t initialized = 0u;
static uint8_t lock_word = 0u;
static void lock() { while (__atomic_test_and_set(&lock_word, __ATOMIC_ACQUIRE)) {} }
static void unlock() { __atomic_clear(&lock_word, __ATOMIC_RELEASE); }
static uint32_t length_of(const char *s) { uint32_t n=0; if(!s)return 0; while(n<=CHIMERA_VFS_MAX_PATH && s[n]) ++n; return n; }
static bool equal(const char *a,const char *b) { uint32_t i=0; while(a[i] && b[i] && a[i]==b[i]) ++i; return a[i]==b[i]; }
static void copy_string(char *d,const char *s,uint32_t n) { for(uint32_t i=0;i<n;i++)d[i]=s[i]; d[n]=0; }
static int normalize(const char *input,char *output) {
    if(!input || !output) return -22;
    const uint32_t n=length_of(input);
    if(!n || n>CHIMERA_VFS_MAX_PATH || input[0]!='/') return -22;
    uint32_t i=0,o=0;
    output[o++]='/';
    while(i<n) {
        while(i<n && input[i]=='/') ++i;
        if(i==n) break;
        const uint32_t start=i;
        while(i<n && input[i]!='/') ++i;
        const uint32_t part=i-start;
        if(!part || (part==1u && input[start]=='.') ||
           (part==2u && input[start]=='.' && input[start+1u]=='.')) return -22;
        if(o>1u) output[o++]='/';
        if(o+part>CHIMERA_VFS_MAX_PATH) return -36;
        copy_string(output+o,input+start,part);
        o+=part;
    }
    output[o]=0;
    return 0;
}
struct Resolved { uint32_t index; char relative[CHIMERA_VFS_MAX_PATH+1u]; };
static int resolve(const char *canonical,Resolved *out) {
    if(!canonical || !out) return -22;
    int best=-1; uint32_t best_len=0;
    lock();
    for(uint32_t i=0;i<CHIMERA_VFS_MAX_MOUNTS;i++) {
        if(!mounts[i].active) continue;
        const uint32_t n=length_of(mounts[i].path);
        bool match=true;
        for(uint32_t j=0;j<n;j++) if(canonical[j]!=mounts[i].path[j]) {match=false;break;}
        if(!match) continue;
        if(n>1u && canonical[n] && canonical[n]!='/') continue;
        if(n>=best_len) {best=(int)i;best_len=n;}
    }
    if(best>=0) {
        out->index=(uint32_t)best;
        const char *rest = canonical + best_len;
        if (equal(mounts[(uint32_t)best].path, "/")) {
            copy_string(out->relative, canonical, length_of(canonical));
        } else if (!*rest) {
            out->relative[0]='/'; out->relative[1]=0;
        } else {
            copy_string(out->relative, rest, length_of(rest));
        }
    }
    unlock();
    return best<0 ? -2 : 0;
}
static int resolve_path(const char *path,char *canonical,Resolved *r) {
    int rc=normalize(path,canonical); if(rc) return rc; return resolve(canonical,r);
}
static bool mount_readonly(const Mount &m) { return (m.flags & CHIMERA_VFS_MOUNT_RDONLY)!=0u; }
struct MountPin {
    uint32_t index;
    Mount mount;
    bool held;
    MountPin(const MountPin &) = delete;
    MountPin &operator=(const MountPin &) = delete;
    explicit MountPin(uint32_t i) : index(i), mount{}, held(false) {
        lock();
        if (i < CHIMERA_VFS_MAX_MOUNTS && mounts[i].active) {
            ++mounts[i].active_ops;
            mount = mounts[i];
            held = true;
        }
        unlock();
    }
    ~MountPin() {
        if (!held) return;
        lock();
        if (index < CHIMERA_VFS_MAX_MOUNTS && mounts[index].active && mounts[index].active_ops)
            --mounts[index].active_ops;
        unlock();
    }
};
static int check_existing(const Resolved &r,const char *path,chimera_vfs_stat *st) {
    MountPin pin(r.index);
    if (!pin.held) return -2;
    if (!pin.mount.ops.lookup) return -38;
    return pin.mount.ops.lookup(pin.mount.context,path,st);
}
}

extern "C" int chimera_vfs_init(void) {
    lock();
    if (initialized) { unlock(); return 0; }
    for(uint32_t i=0;i<CHIMERA_VFS_MAX_MOUNTS;i++) mounts[i]={};
    for(uint32_t i=0;i<CHIMERA_VFS_MAX_OPEN_FILES;i++) files[i]={};
    next_generation=1u; initialized=1u;
    unlock(); return 0;
}
extern "C" int chimera_vfs_normalize_path(const char *input,char output[CHIMERA_VFS_MAX_PATH+1u]) { return normalize(input,output); }
extern "C" int chimera_vfs_mount(const char *mountpoint,const chimera_vfs_ops *ops,void *context,uint32_t flags) {
    char path[CHIMERA_VFS_MAX_PATH+1u]; int rc=normalize(mountpoint,path); if(rc)return rc;
    if(!ops || !ops->lookup || (flags & ~CHIMERA_VFS_MOUNT_RDONLY)) return -22;
    lock(); if(!initialized){unlock();return -19;}
    int free_slot=-1;
    for(uint32_t i=0;i<CHIMERA_VFS_MAX_MOUNTS;i++){
        if(mounts[i].active && equal(mounts[i].path,path)){unlock();return -17;}
        if(!mounts[i].active && free_slot<0)free_slot=(int)i;
    }
    if(free_slot<0){unlock();return -28;}
    Mount &m=mounts[(uint32_t)free_slot]; for(uint32_t i=0;i<=CHIMERA_VFS_MAX_PATH;i++)m.path[i]=path[i];
    m.ops=*ops;m.context=context;m.flags=flags;m.active_ops=0u;m.active=true;unlock();return 0;
}
extern "C" int chimera_vfs_unmount(const char *mountpoint) {
    char path[CHIMERA_VFS_MAX_PATH+1u];int rc=normalize(mountpoint,path);if(rc)return rc;
    lock();int found=-1;
    for(uint32_t i=0;i<CHIMERA_VFS_MAX_MOUNTS;i++)if(mounts[i].active&&equal(mounts[i].path,path))found=(int)i;
    if(found<0){unlock();return -2;}
    if (mounts[(uint32_t)found].active_ops) { unlock(); return -16; }
    for(uint32_t i=0;i<CHIMERA_VFS_MAX_OPEN_FILES;i++)if(files[i].active&&files[i].mount_index==(uint32_t)found){unlock();return -16;}
    mounts[(uint32_t)found].active=false;unlock();return 0;
}
extern "C" int64_t chimera_vfs_open(uint32_t pid,const char *path,uint32_t flags,uint32_t mode) {
    if(!pid || (flags&CHIMERA_VFS_O_ACCMODE)>CHIMERA_VFS_O_RDWR ||
       (flags & ~(CHIMERA_VFS_O_ACCMODE|CHIMERA_VFS_O_CREAT|CHIMERA_VFS_O_EXCL|CHIMERA_VFS_O_TRUNC|CHIMERA_VFS_O_APPEND)))return -22;
    char canonical[CHIMERA_VFS_MAX_PATH+1u];Resolved r{};int rc=resolve_path(path,canonical,&r);if(rc)return rc;
    MountPin pin(r.index);
    if (!pin.held) return -2;
    Mount m = pin.mount;
    const uint32_t access = flags & CHIMERA_VFS_O_ACCMODE;
    if (mount_readonly(m) && (access != CHIMERA_VFS_O_RDONLY ||
        (flags & (CHIMERA_VFS_O_CREAT | CHIMERA_VFS_O_TRUNC)))) return -30;
    if ((flags & CHIMERA_VFS_O_TRUNC) && access == CHIMERA_VFS_O_RDONLY) return -22;
    chimera_vfs_stat st{};rc=check_existing(r,r.relative,&st);
    if(rc==-2 && (flags&CHIMERA_VFS_O_CREAT)){
        if(mount_readonly(m))return -30;
        if(!m.ops.create)return -38;
        rc=m.ops.create(m.context,r.relative,CHIMERA_VFS_REGULAR,mode);if(rc)return rc;
        rc=check_existing(r,r.relative,&st);
    } else if(rc==0 && (flags&CHIMERA_VFS_O_CREAT) && (flags&CHIMERA_VFS_O_EXCL)) return -17;
    if(rc)return rc;
    if(st.type==CHIMERA_VFS_DIRECTORY && (flags&CHIMERA_VFS_O_ACCMODE)!=CHIMERA_VFS_O_RDONLY)return -21;
    if((flags&CHIMERA_VFS_O_TRUNC) && (flags&CHIMERA_VFS_O_ACCMODE)!=CHIMERA_VFS_O_RDONLY){
        if(mount_readonly(m))return -30;
        if(!m.ops.truncate)return -38;
        rc=m.ops.truncate(m.context,r.relative,0u);if(rc)return rc;st.size=0;
    }
    lock();for(uint32_t i=0;i<CHIMERA_VFS_MAX_OPEN_FILES;i++)if(!files[i].active){
        OpenFile &f=files[i];f.pid=pid;f.mount_index=r.index;f.flags=flags;f.offset=(flags&CHIMERA_VFS_O_APPEND)?st.size:0u;
        f.generation=next_generation++;if(!next_generation)next_generation=1u;
        copy_string(f.path,r.relative,length_of(r.relative));f.active=true;unlock();return (int64_t)i+3;
    }unlock();return -24;
}
extern "C" int64_t chimera_vfs_read(uint32_t pid,int64_t fd,void *buffer,uint64_t length) {
    if(!pid||fd<3||fd>=CHIMERA_VFS_MAX_OPEN_FILES+3u||(!buffer&&length))return -22;
    lock();OpenFile f=files[(uint32_t)(fd-3)];if(!f.active||f.pid!=pid){unlock();return -9;}
    if((f.flags&CHIMERA_VFS_O_ACCMODE)==CHIMERA_VFS_O_WRONLY){unlock();return -9;}
    unlock();
    MountPin pin(f.mount_index);
    if (!pin.held || !pin.mount.ops.read) return -38;
    const Mount &m = pin.mount;
    uint64_t n=0;int rc=m.ops.read(m.context,f.path,f.offset,buffer,length,&n);if(rc)return rc;if(n>length)return -5;
    lock();OpenFile &live=files[(uint32_t)(fd-3)];if(!live.active||live.pid!=pid||live.generation!=f.generation){unlock();return -9;}
    if(live.offset>UINT64_MAX-n){unlock();return -75;}live.offset+=n;unlock();return (int64_t)n;
}
extern "C" int64_t chimera_vfs_write(uint32_t pid,int64_t fd,const void *buffer,uint64_t length) {
    if(!pid||fd<3||fd>=CHIMERA_VFS_MAX_OPEN_FILES+3u||(!buffer&&length))return -22;
    lock();OpenFile f=files[(uint32_t)(fd-3)];if(!f.active||f.pid!=pid){unlock();return -9;}
    if((f.flags&CHIMERA_VFS_O_ACCMODE)==CHIMERA_VFS_O_RDONLY){unlock();return -9;}
    unlock();
    MountPin pin(f.mount_index);
    if (!pin.held) return -9;
    const Mount &m = pin.mount;
    if(mount_readonly(m))return -30;if(!m.ops.write)return -38;
    uint64_t n=0;int rc=m.ops.write(m.context,f.path,f.offset,buffer,length,&n);if(rc)return rc;if(n>length)return -5;
    lock();OpenFile &live=files[(uint32_t)(fd-3)];if(!live.active||live.pid!=pid||live.generation!=f.generation){unlock();return -9;}
    if(live.offset>UINT64_MAX-n){unlock();return -75;}live.offset+=n;unlock();return (int64_t)n;
}
extern "C" int64_t chimera_vfs_seek(uint32_t pid,int64_t fd,int64_t offset,uint32_t whence) {
    if(!pid||fd<3||fd>=CHIMERA_VFS_MAX_OPEN_FILES+3u)return -9;
    lock();OpenFile &f=files[(uint32_t)(fd-3)];if(!f.active||f.pid!=pid){unlock();return -9;}
    uint64_t base=0;if(whence==1u)base=f.offset;else if(whence==2u){Mount m=mounts[f.mount_index];chimera_vfs_stat st{};int rc=m.ops.lookup?m.ops.lookup(m.context,f.path,&st):-38;if(rc){unlock();return rc;}base=st.size;}else if(whence!=0u){unlock();return -22;}
    uint64_t next;if(offset<0){uint64_t delta=(uint64_t)(-(offset+1))+1u;if(delta>base){unlock();return -22;}next=base-delta;}else{if(base>UINT64_MAX-(uint64_t)offset){unlock();return -75;}next=base+(uint64_t)offset;}
    if (next > INT64_MAX) { unlock(); return -75; }
    f.offset=next;unlock();return (int64_t)next;
}
extern "C" int chimera_vfs_close(uint32_t pid,int64_t fd) {
    if(!pid||fd<3||fd>=CHIMERA_VFS_MAX_OPEN_FILES+3u)return -9;
    lock();OpenFile &f=files[(uint32_t)(fd-3)];if(!f.active||f.pid!=pid){unlock();return -9;}f={};unlock();return 0;
}
extern "C" int chimera_vfs_close_process(uint32_t pid) {
    if (!pid) return -22;
    int closed = 0;
    lock();
    for (uint32_t i = 0; i < CHIMERA_VFS_MAX_OPEN_FILES; ++i) {
        if (files[i].active && files[i].pid == pid) { files[i] = {}; ++closed; }
    }
    unlock();
    return closed;
}
extern "C" int chimera_vfs_stat_path(const char *path,chimera_vfs_stat *out) {
    if(!out)return -22;char canonical[CHIMERA_VFS_MAX_PATH+1u];Resolved r{};int rc=resolve_path(path,canonical,&r);if(rc)return rc;return check_existing(r,r.relative,out);
}
extern "C" int chimera_vfs_mkdir(const char *path,uint32_t mode) {
    char canonical[CHIMERA_VFS_MAX_PATH+1u];Resolved r{};int rc=resolve_path(path,canonical,&r);if(rc)return rc;
    MountPin pin(r.index);if(!pin.held)return -2;const Mount &m=pin.mount;
    if(mount_readonly(m))return -30;if(!m.ops.mkdir)return -38;return m.ops.mkdir(m.context,r.relative,mode);
}
extern "C" int chimera_vfs_unlink(const char *path,uint32_t directory) {
    char canonical[CHIMERA_VFS_MAX_PATH+1u];Resolved r{};int rc=resolve_path(path,canonical,&r);if(rc)return rc;
    MountPin pin(r.index);if(!pin.held)return -2;const Mount &m=pin.mount;
    if(mount_readonly(m))return -30;if(!m.ops.unlink)return -38;return m.ops.unlink(m.context,r.relative,directory?1u:0u);
}
extern "C" int chimera_vfs_rename(const char *old_path,const char *new_path) {
    char old_c[CHIMERA_VFS_MAX_PATH+1u],new_c[CHIMERA_VFS_MAX_PATH+1u];Resolved old_r{},new_r{};
    int rc=resolve_path(old_path,old_c,&old_r);if(rc)return rc;rc=resolve_path(new_path,new_c,&new_r);if(rc)return rc;
    if(old_r.index!=new_r.index)return -18;
    MountPin pin(old_r.index);if(!pin.held)return -2;const Mount &m=pin.mount;
    if(mount_readonly(m))return -30;if(!m.ops.rename)return -38;return m.ops.rename(m.context,old_r.relative,new_r.relative);
}
extern "C" int chimera_vfs_sync(void) {
    for (uint32_t i = 0; i < CHIMERA_VFS_MAX_MOUNTS; ++i) {
        MountPin pin(i);
        if (!pin.held || !pin.mount.ops.sync) continue;
        const int rc = pin.mount.ops.sync(pin.mount.context);
        if (rc) return rc;
    }
    return 0;
}
