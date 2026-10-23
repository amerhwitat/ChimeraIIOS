#include "chimera/iso9660.h"
#include <stdint.h>

struct chimera_iso9660 {
    const chimera_block_device *device;
    uint32_t volume_blocks, root_extent, root_size;
    uint32_t active;
};
namespace {
static chimera_iso9660 pool[4]{};
struct Record { uint32_t extent,size; uint8_t flags,name_len; const uint8_t *name; };
static uint16_t le16(const uint8_t*p){return (uint16_t)p[0]|((uint16_t)p[1]<<8);}
static uint32_t le32(const uint8_t*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static bool both16(const uint8_t*p){return p[0]==p[2]&&p[1]==p[3];}
static bool both32(const uint8_t*p){return p[0]==p[4]&&p[1]==p[5]&&p[2]==p[6]&&p[3]==p[7];}
static bool valid_extent(const chimera_iso9660*fs,uint32_t extent,uint32_t size){
 if(!fs||extent>=fs->volume_blocks)return false;
 uint64_t start=(uint64_t)extent*CHIMERA_ISO9660_SECTOR_SIZE;
 return start<=fs->device->capacity_bytes&&size<=fs->device->capacity_bytes-start&&
        (uint64_t)size<=(uint64_t)(fs->volume_blocks-extent)*CHIMERA_ISO9660_SECTOR_SIZE;
}
static int parse_record(const uint8_t*p,uint32_t avail,Record*out){
 if(!p||!out||avail<34u||p[0]<34u||p[0]>avail)return -5;
 uint8_t len=p[0],nl=p[32];if((uint32_t)33u+nl>len||!both32(p+2)||!both32(p+10))return -5;
 if((p[25]&0x80u)!=0u)return -95;
 out->extent=le32(p+2)+p[1];out->size=le32(p+10);out->flags=p[25];out->name_len=nl;out->name=p+33;return 0;
}
static bool same_char(uint8_t a,char b){if(a>='a'&&a<='z')a=(uint8_t)(a-'a'+'A');if(b>='a'&&b<='z')b=(char)(b-'a'+'A');return a==(uint8_t)b;}
static bool name_match(const Record&r,const char*name,uint32_t n){
 uint32_t rn=r.name_len;for(uint32_t i=0;i<rn;i++)if(r.name[i]==';'){rn=i;break;}
 while(rn&&r.name[rn-1]=='.')--rn;if(rn!=n)return false;
 for(uint32_t i=0;i<n;i++)if(!same_char(r.name[i],name[i]))return false;return true;
}
static int find_child(chimera_iso9660*fs,uint32_t extent,uint32_t size,const char*name,uint32_t n,Record*out){
 if(!valid_extent(fs,extent,size))return -5;uint8_t sector[CHIMERA_ISO9660_SECTOR_SIZE];uint64_t consumed=0;
 while(consumed<size){
  uint32_t chunk=(size-consumed>sizeof(sector))?sizeof(sector):(uint32_t)(size-consumed);
  int rc=chimera_block_read(fs->device,(uint64_t)extent*CHIMERA_ISO9660_SECTOR_SIZE+consumed,sector,chunk);if(rc)return rc;
  uint32_t pos=0;while(pos<chunk){if(sector[pos]==0)break;Record r{};rc=parse_record(sector+pos,chunk-pos,&r);if(rc)return rc;
   if(!(r.name_len==1u&&(r.name[0]==0u||r.name[0]==1u))&&name_match(r,name,n)){*out=r;return 0;}
   pos+=sector[pos];
  }consumed+=chunk;
 }return -2;
}
static int walk(chimera_iso9660*fs,const char*path,Record*out){
 if(!fs||!path||!out||path[0]!='/')return -22;uint32_t extent=fs->root_extent,size=fs->root_size,i=1;
 if(!path[i]){*out={extent,size,2u,0u,nullptr};return 0;}
 while(path[i]){
  uint32_t start=i;while(path[i]&&path[i]!='/'){uint8_t c=(uint8_t)path[i];if(c<0x20u||c=='\\'||c==':')return -22;++i;}
  uint32_t n=i-start;if(!n||(n==1u&&path[start]=='.')||(n==2u&&path[start]=='.'&&path[start+1]=='.'))return -22;
  Record r{};int rc=find_child(fs,extent,size,path+start,n,&r);if(rc)return rc;
  if(path[i]&&!(r.flags&2u))return -20;extent=r.extent;size=r.size;*out=r;
  if(path[i]=='/'){++i;if(!path[i])return -22;}
 }
 return valid_extent(fs,extent,size)?0:-5;
}
static int lookup(void*ctx,const char*path,chimera_vfs_stat*out){
 if(!out)return -22;Record r{};int rc=walk((chimera_iso9660*)ctx,path,&r);if(rc)return rc;
 out->size=r.size;out->type=(r.flags&2u)?CHIMERA_VFS_DIRECTORY:CHIMERA_VFS_REGULAR;out->mode=(r.flags&2u)?0555u:0444u;return 0;
}
static int read_file(void*ctx,const char*path,uint64_t off,void*buf,uint64_t len,uint64_t*done){
 if(!done||(!buf&&len))return -22;*done=0;auto*fs=(chimera_iso9660*)ctx;Record r{};int rc=walk(fs,path,&r);if(rc)return rc;
 if(r.flags&2u)return -21;if(off>=r.size||!len)return 0;if(!valid_extent(fs,r.extent,r.size))return -5;
 uint64_t amount=r.size-off;if(amount>len)amount=len;rc=chimera_block_read(fs->device,(uint64_t)r.extent*CHIMERA_ISO9660_SECTOR_SIZE+off,buf,amount);if(rc)return rc;*done=amount;return 0;
}
static const chimera_vfs_ops ops={lookup,read_file,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr};
}
extern "C" int chimera_iso9660_mount(const chimera_block_device*d,chimera_iso9660**out){
 if(!d||!out||d->abi!=CHIMERA_BLOCK_DEVICE_ABI||!d->read)return -22;*out=nullptr;
 if(d->capacity_bytes<18ull*CHIMERA_ISO9660_SECTOR_SIZE)return -5;
 uint8_t sec[CHIMERA_ISO9660_SECTOR_SIZE];bool found=false;uint32_t blocks=0,re=0,rs=0;
 for(uint32_t lba=16;lba<80u;lba++){
  int rc=chimera_block_read(d,(uint64_t)lba*CHIMERA_ISO9660_SECTOR_SIZE,sec,sizeof(sec));if(rc)return rc;
  if(sec[1]!='C'||sec[2]!='D'||sec[3]!='0'||sec[4]!='0'||sec[5]!='1')return -95;
  if(sec[0]==255u)break;
  if(sec[0]==1u){
   if(!both32(sec+80)||!both16(sec+128)||le16(sec+128)!=CHIMERA_ISO9660_SECTOR_SIZE)return -5;
   blocks=le32(sec+80);Record root{};rc=parse_record(sec+156,sec[156],&root);if(rc)return rc;
   if(!(root.flags&2u)||!root.size||root.extent>=blocks)return -5;re=root.extent;rs=root.size;found=true;break;
  }
 }
 if(!found||!blocks||(uint64_t)blocks*CHIMERA_ISO9660_SECTOR_SIZE>d->capacity_bytes)return -5;
 for(uint32_t i=0;i<4u;i++)if(!pool[i].active){pool[i]={d,blocks,re,rs,1u};*out=&pool[i];return 0;}
 return -28;
}
extern "C" void chimera_iso9660_unmount(chimera_iso9660*fs){if(!fs)return;for(uint32_t i=0;i<4u;i++)if(&pool[i]==fs){pool[i].active=0;pool[i].device=nullptr;return;}}
extern "C" const chimera_vfs_ops*chimera_iso9660_vfs_ops(void){return &ops;}
