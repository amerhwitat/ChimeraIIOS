#include "chimera/iso9660.h"
#include <stddef.h>
#include <stdint.h>

struct chimera_iso9660 {
    const chimera_block_device *device;
    uint32_t volume_blocks;
    uint32_t root_extent;
    uint32_t root_size;
};

namespace {
struct Record { uint32_t extent, size; uint8_t flags; uint8_t name_len; const uint8_t *name; };
static uint16_t le16(const uint8_t *p) { return (uint16_t)p[0] | ((uint16_t)p[1] << 8); }
static uint32_t le32(const uint8_t *p) { return (uint32_t)p[0] | ((uint32_t)p[1]<<8) | ((uint32_t)p[2]<<16) | ((uint32_t)p[3]<<24); }
static bool both16(const uint8_t *p) { return p[0] == p[2] && p[1] == p[3]; }
static bool both32(const uint8_t *p) { return p[0] == p[4] && p[1] == p[5] && p[2] == p[6] && p[3] == p[7]; }
static bool valid_extent(const chimera_iso9660 *fs, uint32_t extent, uint32_t size) {
    if (!fs || extent >= fs->volume_blocks) return false;
    const uint64_t start = (uint64_t)extent * CHIMERA_ISO9660_SECTOR_SIZE;
    return size <= fs->device->capacity_bytes - start &&
           (uint64_t)size <= (uint64_t)(fs->volume_blocks - extent) * CHIMERA_ISO9660_SECTOR_SIZE;
}
static int read_record(const uint8_t *p, uint32_t available, Record *out) {
    if (!p || !out || available < 34u || p[0] < 34u || p[0] > available) return -5;
    const uint8_t len = p[0], nl = p[32];
    if ((uint32_t)33u + nl > len || !both32(p+2) || !both32(p+10)) return -5;
    if (nl == 1u && (p[33] == 0u || p[33] == 1u)) {
        out->extent=le32(p+2)+p[1]; out->size=le32(p+10); out->flags=p[25]; out->name_len=nl; out->name=p+33; return 0;
    }
    if (p[25] & 0x80u) return -95; /* multi-extent not implemented */
    out->extent=le32(p+2)+p[1]; out->size=le32(p+10); out->flags=p[25]; out->name_len=nl; out->name=p+33;
    return 0;
}
static bool eq_char(uint8_t a, char b) {
    if (a >= 'a' && a <= 'z') a = (uint8_t)(a - 'a' + 'A');
    if (b >= 'a' && b <= 'z') b = (char)(b - 'a' + 'A');
    return a == (uint8_t)b;
}
static bool match_name(const Record &r, const char *part, uint32_t n) {
    uint32_t rn=r.name_len;
    while (rn && r.name[rn-1u]==' ') --rn;
    /* Strip ISO ;version suffix and trailing dot for common ISO names. */
    for (uint32_t i=0;i<rn;i++) if (r.name[i]==';') { rn=i; break; }
    while (rn && r.name[rn-1u]=='.') --rn;
    if (rn != n) return false;
    for (uint32_t i=0;i<n;i++) if (!eq_char(r.name[i],part[i])) return false;
    return true;
}
static int find_in_dir(chimera_iso9660 *fs, uint32_t extent, uint32_t size,
                       const char *name, uint32_t name_len, Record *found) {
    if (!valid_extent(fs,extent,size)) return -5;
    uint8_t buf[CHIMERA_ISO9660_SECTOR_SIZE];
    uint64_t consumed=0;
    while (consumed < size) {
        const uint64_t sector_off=(uint64_t)extent*CHIMERA_ISO9660_SECTOR_SIZE + consumed;
        const uint32_t chunk=(size-consumed > sizeof(buf)) ? sizeof(buf) : (uint32_t)(size-consumed);
        int rc=chimera_block_read(fs->device,sector_off,buf,chunk); if(rc)return rc;
        uint32_t pos=0;
        while(pos<chunk) {
            if(buf[pos]==0) break; /* directory records do not cross sector boundaries */
            Record r{}; rc=read_record(buf+pos,chunk-pos,&r); if(rc)return rc;
            if(r.name_len==1u && (r.name[0]==0u || r.name[0]==1u)) { pos += buf[pos]; continue; }
            if(match_name(r,name,name_len)) { *found=r; return 0; }
            pos += buf[pos];
        }
        consumed += chunk;
    }
    return -2;
}
static int walk(chimera_iso9660 *fs, const char *path, Record *out) {
    if(!fs||!path||!out||path[0]!='/') return -22;
    uint32_t extent=fs->root_extent, size=fs->root_size;
    uint32_t i=1;
    if(!path[i]) { out->extent=extent;out->size=size;out->flags=2u;out->name_len=1;out->name=nullptr;return 0; }
    while(path[i]) {
        uint32_t start=i;
        while(path[i] && path[i]!='/') {
            if ((uint8_t)path[i] < 0x20u || path[i]=='\\' || path[i]==':' ) return -22;
            ++i;
        }
        uint32_t n=i-start;
        if(!n || (n==1u&&path[start]=='.') || (n==2u&&path[start]=='.'&&path[start+1]=='.')) return -22;
        Record r{}; int rc=find_in_dir(fs,extent,size,path+start,n,&r); if(rc)return rc;
        if(path[i] && !(r.flags&2u)) return -20;
        extent=r.extent; size=r.size; *out=r;
        if(path[i]=='/') { ++i; if(!path[i]) return -22; }
    }
    return valid_extent(fs,extent,size)?0:-5;
}
static int lookup(void *ctx,const char *path,chimera_vfs_stat *out) {
    if(!out)return -22;Record r{};int rc=walk((chimera_iso9660*)ctx,path,&r);if(rc)return rc;
    out->size=r.size;out->type=(r.flags&2u)?CHIMERA_VFS_DIRECTORY:CHIMERA_VFS_REGULAR;out->mode=(r.flags&2u)?0555u:0444u;return 0;
}
static int read_file(void *ctx,const char *path,uint64_t off,void *buf,uint64_t len,uint64_t *done) {
    if(!done||(!buf&&len))return -22;*done=0;Record r{};int rc=walk((chimera_iso9660*)ctx,path,&r);if(rc)return rc;
    if(r.flags&2u)return -21;if(off>=r.size||!len)return 0;
    uint64_t amount=r.size-off;if(amount>len)amount=len;
    if(!valid_extent((chimera_iso9660*)ctx,r.extent,r.size))return -5;
    rc=chimera_block_read(((chimera_iso9660*)ctx)->device,(uint64_t)r.extent*CHIMERA_ISO9660_SECTOR_SIZE+off,buf,amount);
    if(rc)return rc;*done=amount;return 0;
}
static const chimera_vfs_ops ops={lookup,read_file,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr};
}
extern "C" int chimera_iso9660_mount(const chimera_block_device *device,chimera_iso9660 **out) {
    if(!device||!out||device->abi!=CHIMERA_BLOCK_DEVICE_ABI||!device->read) return -22;
    *out=nullptr;
    if(device->capacity_bytes < 18ull*CHIMERA_ISO9660_SECTOR_SIZE) return -5;
    uint8_t sector[CHIMERA_ISO9660_SECTOR_SIZE]; bool found=false;
    uint32_t volume_blocks=0,root_extent=0,root_size=0;
    for(uint32_t lba=16;lba<80u;lba++) {
        int rc=chimera_block_read(device,(uint64_t)lba*CHIMERA_ISO9660_SECTOR_SIZE,sector,sizeof(sector));if(rc)return rc;
        if(sector[1]!='C'||sector[2]!='D'||sector[3]!='0'||sector[4]!='0'||sector[5]!='1')return -95;
        if(sector[0]==255u)break;
        if(sector[0]==1u) {
            if(!both32(sector+80)||!both16(sector+128)||le16(sector+128)!=CHIMERA_ISO9660_SECTOR_SIZE)return -5;
            volume_blocks=le32(sector+80);
            Record root{};int rr=read_record(sector+156,sector[156],&root);if(rr)return rr;
            if(!(root.flags&2u)||!root.size||root.extent>=volume_blocks)return -5;
            root_extent=root.extent;root_size=root.size;found=true;break;
        }
        /* Supplementary/Joliet descriptors are deliberately not treated as PVD. */
    }
    if(!found||!volume_blocks||((uint64_t)volume_blocks*CHIMERA_ISO9660_SECTOR_SIZE)>device->capacity_bytes)return -5;
    chimera_iso9660 *fs=(chimera_iso9660*)::operator new(sizeof(chimera_iso9660),::std::nothrow);if(!fs)return -12;
    fs->device=device;fs->volume_blocks=volume_blocks;fs->root_extent=root_extent;fs->root_size=root_size;
    *out=fs;return 0;
}
extern "C" void chimera_iso9660_unmount(chimera_iso9660 *fs) { if(fs)::operator delete(fs); }
extern "C" const chimera_vfs_ops *chimera_iso9660_vfs_ops(void) { return &ops; }
