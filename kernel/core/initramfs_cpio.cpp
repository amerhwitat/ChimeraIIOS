#include "chimera/initramfs_cpio.h"
#include <stddef.h>
#include <stdint.h>
namespace {
static uint32_t hex8(const uint8_t *p, bool *ok) {
  uint32_t v=0;
  for (uint32_t i=0;i<8;i++) {
    const uint8_t c=p[i]; uint32_t d;
    if (c>='0'&&c<='9') d=c-'0';
    else if (c>='a'&&c<='f') d=c-'a'+10u;
    else if (c>='A'&&c<='F') d=c-'A'+10u;
    else { *ok=false; return 0; }
    v=(v<<4)|d;
  }
  return v;
}
static bool add_ok(uint64_t a,uint64_t b,uint64_t limit,uint64_t *out) {
  if (a>limit || b>limit-a) return false;
  *out=a+b; return true;
}
static bool align4(uint64_t v,uint64_t limit,uint64_t *out) {
  if (v>UINT64_MAX-3u) return false;
  const uint64_t a=(v+3u)&~uint64_t(3u);
  if (a>limit) return false;
  *out=a; return true;
}
static bool safe_path(const uint8_t *p,uint32_t n,bool directory) {
  if (!p||n<2||n>CHIMERA_CPIO_MAX_PATH+1u||p[n-1]!=0) return false;
  if (p[0]=='/' || p[0]==0) return false;
  uint32_t end=n-1u;
  /* CPIO producers commonly encode directories as "path/". Accept that
     spelling only for directory entries; compare paths canonically below. */
  if (end>0u&&p[end-1u]=='/') {
    if (!directory) return false;
    --end;
  }
  if (end==0u) return false;
  uint32_t component=0;
  for (uint32_t i=0;i<end;i++) {
    if (p[i]=='\\') return false;
    if (p[i]=='/') {
      if (!component) return false;
      if (component==1u&&p[i-1]=='.') return false;
      if (component==2u&&p[i-1]=='.'&&p[i-2]=='.') return false;
      component=0;
    } else {
      if (p[i]<0x20u) return false;
      ++component;
    }
  }
  if (!component) return false;
  if (component==1u&&p[end-1u]=='.') return false;
  if (component==2u&&p[end-1u]=='.'&&p[end-2u]=='.') return false;
  return true;
}
static bool duplicate_name(const uint8_t *b,uint64_t end,const uint8_t *name,uint32_t name_size,uint32_t current_mode) {
  uint64_t off=0;
  while (off<end) {
    if (end-off<110u) return true;
    const uint8_t *h=b+off;
    bool ok=true;
    const uint32_t prior_mode=hex8(h+14,&ok), file_size=hex8(h+54,&ok), prior_name_size=hex8(h+94,&ok);
    if (!ok || prior_name_size==0u) return true;
    uint64_t name_end=0,name_aligned=0,data_end=0,next=0;
    if (!add_ok(off,110u,end,&name_end) ||
        !add_ok(name_end,prior_name_size,end,&name_end) ||
        !align4(name_end,end,&name_aligned) ||
        !add_ok(name_aligned,file_size,end,&data_end) ||
        !align4(data_end,end,&next) || next>end) return true;
    const uint8_t *prior=b+off+110u;
    uint32_t prior_effective=prior_name_size-1u;
    uint32_t current_effective=name_size-1u;
    if (prior_effective>0u&&prior[prior_effective-1u]=='/'&&
        (prior_mode&0170000u)==0040000u) --prior_effective;
    if (current_effective>0u&&name[current_effective-1u]=='/'&&
        (current_mode&0170000u)==0040000u) --current_effective;
    uint32_t common=0;
    while (common<prior_effective && common<current_effective &&
           prior[common]==name[common]) ++common;
    if (common==prior_effective && common==current_effective) return true;
    const bool prior_is_dir=(prior_mode&0170000u)==0040000u;
    const bool current_is_dir=(current_mode&0170000u)==0040000u;
    if (common==prior_effective && common<current_effective &&
        name[common]=='/' && !prior_is_dir) return true;
    if (common==current_effective && common<prior_effective &&
        prior[common]=='/' && !current_is_dir) return true;
    off=next;
  }
  return false;
}
}
extern "C" int chimera_cpio_validate_newc(const void *input,uint64_t size,chimera_cpio_summary *out) {
  if (!input||!out) return CHIMERA_CPIO_E_ARGUMENT;
  if (size>CHIMERA_CPIO_MAX_ARCHIVE_BYTES) return CHIMERA_CPIO_E_LIMIT;
  if (size>=2u) { const auto *prefix=static_cast<const uint8_t*>(input); if (prefix[0]==0x1fu&&prefix[1]==0x8bu) return CHIMERA_CPIO_E_COMPRESSION; }
  if (size<110u) return CHIMERA_CPIO_E_ARGUMENT;
  const auto *b=static_cast<const uint8_t*>(input);
  chimera_cpio_summary s{}; s.archive_bytes=size;
  uint64_t off=0; bool trailer=false;
  while (off<size) {
    uint64_t header_end=0;
    if (!add_ok(off,110u,size,&header_end)) return CHIMERA_CPIO_E_BOUNDS;
    const uint8_t *h=b+off;
    const bool crc=(h[5]=='2');
    if (!(h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&(h[5]=='1'||crc)))
      return CHIMERA_CPIO_E_HEADER;
    bool ok=true;
    const uint32_t mode=hex8(h+14,&ok), file_size=hex8(h+54,&ok),
      name_size=hex8(h+94,&ok), check=hex8(h+102,&ok);
    if (!ok||name_size<1u||name_size>CHIMERA_CPIO_MAX_PATH+1u)
      return CHIMERA_CPIO_E_HEADER;
    /* newc (070701) defines c_check as zero; only crc (070702) carries
       the unsigned byte-sum checksum. Do not silently accept mixed formats. */
    if (!crc && check!=0u) return CHIMERA_CPIO_E_CHECKSUM;
    uint64_t name_end=0,name_aligned=0,data_end=0,data_aligned=0;
    if (!add_ok(header_end,name_size,size,&name_end)||
        !align4(name_end,size,&name_aligned)||
        !add_ok(name_aligned,file_size,size,&data_end)||
        !align4(data_end,size,&data_aligned)) return CHIMERA_CPIO_E_BOUNDS;
    const uint8_t *name=b+header_end;
    if (name[name_size-1u]!=0) return CHIMERA_CPIO_E_PATH;
    /* CPIO names are NUL-terminated strings. Reject embedded NULs so the
       validated byte path cannot alias a shorter path in VFS consumers. */
    for (uint32_t i=0;i+1u<name_size;i++)
      if (name[i]==0u) return CHIMERA_CPIO_E_PATH;
    if (name_size==11u) {
      static const char end_name[]="TRAILER!!!";
      bool is_trailer=true;
      for (uint32_t i=0;i<10u;i++) if (name[i]!=(uint8_t)end_name[i]) is_trailer=false;
      if (is_trailer) {
        if (file_size!=0u) return CHIMERA_CPIO_E_TRAILER;
        /* CRC-format trailers have an empty payload, so c_check must be zero.
           Validate it before the trailer early-exit below. */
        if (crc && check!=0u) return CHIMERA_CPIO_E_CHECKSUM;
        trailer=true; off=data_aligned; break;
      }
    }
    if (!safe_path(name,name_size,(mode&0170000u)==0040000u)) return CHIMERA_CPIO_E_PATH;
    if (duplicate_name(b,off,name,name_size,mode)) return CHIMERA_CPIO_E_PATH;
    if (++s.entries>CHIMERA_CPIO_MAX_ENTRIES) return CHIMERA_CPIO_E_LIMIT;
    const uint32_t type=mode&0170000u;
    /* Directory payloads are non-canonical and can be interpreted differently
       by validators and extractors. Reject them before any future extraction. */
    if (type==0040000u && file_size!=0u) return CHIMERA_CPIO_E_TYPE;
    if (type==0100000u) ++s.regular_files;
    else if (type==0040000u) ++s.directories;
    else if (type!=0120000u) return CHIMERA_CPIO_E_TYPE;
    if (type==0120000u) {
      if (file_size==0u||file_size>CHIMERA_CPIO_MAX_PATH) return CHIMERA_CPIO_E_PATH;
      const uint8_t *target=b+name_aligned;
      if (target[0]=='/'||target[0]==0) return CHIMERA_CPIO_E_PATH;
      for (uint32_t i=0;i<file_size;i++) if (target[i]==0||target[i]=='\\') return CHIMERA_CPIO_E_PATH;
      for (uint32_t i=0;i<file_size;) {
        uint32_t j=i; while(j<file_size&&target[j]!='/') ++j;
        const uint32_t n=j-i;
        /* Reject empty components (double or trailing slashes) rather than
           letting different consumers normalize a link target differently. */
        if (n==0u) return CHIMERA_CPIO_E_PATH;
        if ((n==1u&&target[i]=='.')||(n==2u&&target[i]=='.'&&target[i+1]=='.')) return CHIMERA_CPIO_E_PATH;
        if (j==file_size) break;
        i=j+1u;
        if (i==file_size) return CHIMERA_CPIO_E_PATH;
      }
    }
    if (crc) {
      uint32_t sum=0;
      for (uint32_t i=0;i<file_size;i++) sum=(sum+b[name_aligned+i])&0xffffffffu;
      if (sum!=check) return CHIMERA_CPIO_E_CHECKSUM;
    }
    if (UINT64_MAX-s.payload_bytes<file_size) return CHIMERA_CPIO_E_BOUNDS;
    s.payload_bytes+=file_size;
    const bool top_init = name_size==5u&&name[0]=='i'&&name[1]=='n'&&name[2]=='i'&&name[3]=='t'&&name[4]==0;
    const bool sbin_init = name_size==10u&&name[0]=='s'&&name[1]=='b'&&name[2]=='i'&&name[3]=='n'&&name[4]=='/'&&name[5]=='i'&&name[6]=='n'&&name[7]=='i'&&name[8]=='t'&&name[9]==0;
    if ((top_init || sbin_init) && type==0100000u) s.has_init=1u;
    off=data_aligned;
  }
  if (!trailer) return CHIMERA_CPIO_E_TRAILER;
  /* Padding after TRAILER!!! is allowed, but nonzero trailing bytes are not. */
  for (uint64_t i=off;i<size;i++) if (b[i]!=0) return CHIMERA_CPIO_E_TRAILER;
  *out=s;
  return CHIMERA_CPIO_OK;
}
