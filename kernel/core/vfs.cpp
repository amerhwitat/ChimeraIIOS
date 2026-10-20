#include "chimera/vfs.h"
namespace {
static bool add_overflow(uint64_t a,uint64_t b,uint64_t*out){if(!out||b>UINT64_MAX-a)return true;*out=a+b;return false;}
static int normalize(const char*in,char out[CHIMERA_VFS_PATH_MAX]){
 if(!in||!out)return CHIMERA_VFS_EINVAL;while(*in=='/')++in;uint32_t n=0;if(!*in)return CHIMERA_VFS_EINVAL;
 while(*in){if(*in=='\\')return CHIMERA_VFS_EINVAL;uint32_t seg=0;while(in[seg]&&in[seg]!='/')++seg;
  if(!seg||(seg==1&&in[0]=='.')||(seg==2&&in[0]=='.'&&in[1]=='.'))return CHIMERA_VFS_EINVAL;
  if(n&&n+1>=CHIMERA_VFS_PATH_MAX)return CHIMERA_VFS_EINVAL;if(n)out[n++]='/';
  if(seg>=CHIMERA_VFS_PATH_MAX-n)return CHIMERA_VFS_EINVAL;for(uint32_t i=0;i<seg;++i)out[n++]=in[i];in+=seg;
  if(*in=='/'){++in;if(!*in)return CHIMERA_VFS_EINVAL;}
 }out[n]=0;return CHIMERA_VFS_OK;
}
static bool equal(const char*a,const char*b){uint32_t i=0;while(a[i]&&b[i]&&a[i]==b[i])++i;return a[i]==b[i];}
static chimera_vfs_node*find(chimera_vfs*fs,const char*p){for(uint32_t i=0;i<fs->node_capacity;++i)if(fs->nodes[i].used&&equal(fs->nodes[i].path,p))return &fs->nodes[i];return nullptr;}
static bool allowed(const chimera_vfs_node*n,uint32_t uid,uint32_t gid,uint32_t bit){if(uid==0)return true;uint32_t shift=uid==n->uid?6u:(gid==n->gid?3u:0u);return ((n->mode>>shift)&bit)!=0;}
static int canonical(chimera_vfs*fs,const char*p,char out[CHIMERA_VFS_PATH_MAX]){if(!fs||!fs->initialized)return CHIMERA_VFS_EINVAL;return normalize(p,out);}
}
extern "C" int chimera_vfs_init(chimera_vfs*fs,chimera_vfs_node*nodes,uint32_t count,void*data,uint64_t data_size,uint64_t slot){
 if(!fs||!nodes||!data||!count||count>CHIMERA_VFS_MAX_FILES||!slot||data_size/slot<count)return CHIMERA_VFS_EINVAL;
 fs->nodes=nodes;fs->node_capacity=count;fs->data=static_cast<uint8_t*>(data);fs->data_capacity=data_size;fs->slot_size=slot;fs->initialized=0;
 for(uint32_t i=0;i<count;++i){nodes[i]={};nodes[i].data_offset=static_cast<uint64_t>(i)*slot;nodes[i].capacity=slot;}fs->initialized=1;return CHIMERA_VFS_OK;
}
extern "C" int chimera_vfs_create(chimera_vfs*fs,const char*path,uint32_t mode,uint32_t uid,uint32_t gid){
 char key[CHIMERA_VFS_PATH_MAX];int rc=canonical(fs,path,key);if(rc)return rc;if(find(fs,key))return CHIMERA_VFS_EEXIST;
 for(uint32_t i=0;i<fs->node_capacity;++i){chimera_vfs_node*n=&fs->nodes[i];if(n->used)continue;uint32_t j=0;while(key[j]&&j+1<CHIMERA_VFS_PATH_MAX){n->path[j]=key[j];++j;}n->path[j]=0;n->uid=uid;n->gid=gid;n->mode=mode&0777u;n->size=0;n->used=1;
  uint64_t end;if(add_overflow(n->data_offset,n->capacity,&end)||end>fs->data_capacity){n->used=0;n->path[0]=0;return CHIMERA_VFS_ENOSPC;}
  for(uint64_t k=0;k<n->capacity;++k)fs->data[n->data_offset+k]=0;return CHIMERA_VFS_OK;}return CHIMERA_VFS_ENOSPC;
}
extern "C" int chimera_vfs_stat_path(chimera_vfs*fs,const char*path,uint32_t uid,uint32_t gid,chimera_vfs_stat*out){
 if(!out)return CHIMERA_VFS_EINVAL;char key[CHIMERA_VFS_PATH_MAX];int rc=canonical(fs,path,key);if(rc)return rc;chimera_vfs_node*n=find(fs,key);if(!n)return CHIMERA_VFS_ENOENT;if(!allowed(n,uid,gid,4u))return CHIMERA_VFS_EACCES;
 out->size=n->size;out->capacity=n->capacity;out->uid=n->uid;out->gid=n->gid;out->mode=n->mode;return CHIMERA_VFS_OK;
}
extern "C" int64_t chimera_vfs_read(chimera_vfs*fs,const char*path,uint64_t off,void*buf,uint64_t len,uint32_t uid,uint32_t gid){
 if(len&&!buf)return CHIMERA_VFS_EINVAL;char key[CHIMERA_VFS_PATH_MAX];int rc=canonical(fs,path,key);if(rc)return rc;chimera_vfs_node*n=find(fs,key);if(!n)return CHIMERA_VFS_ENOENT;if(!allowed(n,uid,gid,4u))return CHIMERA_VFS_EACCES;if(off>=n->size||!len)return 0;
 uint64_t count=n->size-off;if(count>len)count=len;for(uint64_t i=0;i<count;++i)static_cast<uint8_t*>(buf)[i]=fs->data[n->data_offset+off+i];return static_cast<int64_t>(count);
}
extern "C" int64_t chimera_vfs_write(chimera_vfs*fs,const char*path,uint64_t off,const void*buf,uint64_t len,uint32_t uid,uint32_t gid){
 if(len&&!buf)return CHIMERA_VFS_EINVAL;char key[CHIMERA_VFS_PATH_MAX];int rc=canonical(fs,path,key);if(rc)return rc;chimera_vfs_node*n=find(fs,key);if(!n)return CHIMERA_VFS_ENOENT;if(!allowed(n,uid,gid,2u))return CHIMERA_VFS_EACCES;
 uint64_t end;if(add_overflow(off,len,&end)||end>n->capacity)return CHIMERA_VFS_EFBIG;if(off>n->size)for(uint64_t i=n->size;i<off;++i)fs->data[n->data_offset+i]=0;
 for(uint64_t i=0;i<len;++i)fs->data[n->data_offset+off+i]=static_cast<const uint8_t*>(buf)[i];if(end>n->size)n->size=end;return static_cast<int64_t>(len);
}
extern "C" int chimera_vfs_truncate(chimera_vfs*fs,const char*path,uint64_t size,uint32_t uid,uint32_t gid){
 char key[CHIMERA_VFS_PATH_MAX];int rc=canonical(fs,path,key);if(rc)return rc;chimera_vfs_node*n=find(fs,key);if(!n)return CHIMERA_VFS_ENOENT;if(!allowed(n,uid,gid,2u))return CHIMERA_VFS_EACCES;if(size>n->capacity)return CHIMERA_VFS_EFBIG;
 uint64_t old=n->size;for(uint64_t i=(size<old?size:old);i<(size>old?size:old);++i)fs->data[n->data_offset+i]=0;n->size=size;return CHIMERA_VFS_OK;
}
extern "C" int chimera_vfs_chmod(chimera_vfs*fs,const char*path,uint32_t mode,uint32_t uid,uint32_t gid){
 char key[CHIMERA_VFS_PATH_MAX];int rc=canonical(fs,path,key);if(rc)return rc;chimera_vfs_node*n=find(fs,key);if(!n)return CHIMERA_VFS_ENOENT;if(uid!=0&&uid!=n->uid)return CHIMERA_VFS_EACCES;(void)gid;n->mode=mode&0777u;return CHIMERA_VFS_OK;
}
extern "C" int chimera_vfs_chown(chimera_vfs*fs,const char*path,uint32_t owner_uid,uint32_t owner_gid,uint32_t caller_uid){
 char key[CHIMERA_VFS_PATH_MAX];int rc=canonical(fs,path,key);if(rc)return rc;chimera_vfs_node*n=find(fs,key);if(!n)return CHIMERA_VFS_ENOENT;if(caller_uid!=0)return CHIMERA_VFS_EACCES;n->uid=owner_uid;n->gid=owner_gid;return CHIMERA_VFS_OK;
}
extern "C" int chimera_vfs_unlink(chimera_vfs*fs,const char*path,uint32_t uid,uint32_t gid){
 char key[CHIMERA_VFS_PATH_MAX];int rc=canonical(fs,path,key);if(rc)return rc;chimera_vfs_node*n=find(fs,key);if(!n)return CHIMERA_VFS_ENOENT;if(uid!=0&&uid!=n->uid)return CHIMERA_VFS_EACCES;(void)gid;n->used=0;n->path[0]=0;n->size=0;n->uid=n->gid=n->mode=0;return CHIMERA_VFS_OK;
}
