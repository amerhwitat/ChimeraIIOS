#include "chimera/initramfs_ingest.h"
#include "chimera/gzip.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
using Bytes=std::vector<uint8_t>;
static void field(Bytes& b,size_t off,uint32_t v){static const char h[]="0123456789abcdef";for(int i=7;i>=0;--i){b[off+(size_t)i]=(uint8_t)h[v&15u];v>>=4;}}
static void entry(Bytes& b,const char* name,uint32_t mode,const char* data){size_t s=b.size();b.resize(s+110,(uint8_t)'0');std::memcpy(b.data()+s,"070701",6);field(b,s+14,mode);uint32_t n=(uint32_t)std::strlen(name)+1,z=data?(uint32_t)std::strlen(data):0;field(b,s+54,z);field(b,s+94,n);b.insert(b.end(),name,name+n);while(b.size()%4)b.push_back(0);if(data)b.insert(b.end(),data,data+z);while(b.size()%4)b.push_back(0);}
static uint32_t crc32(const uint8_t*p,size_t n){uint32_t c=0xffffffffu;for(size_t j=0;j<n;++j){c^=p[j];for(int i=0;i<8;++i)c=(c>>1)^((c&1)?0xedb88320u:0u);}return c^0xffffffffu;}
static void le32(Bytes&b,uint32_t v){for(int i=0;i<4;++i)b.push_back((uint8_t)(v>>(8*i)));}
static Bytes gzip_stored(const Bytes& raw){assert(raw.size()<65536);Bytes b={0x1f,0x8b,8,0,0,0,0,0,0,255,1,(uint8_t)raw.size(),(uint8_t)(raw.size()>>8),(uint8_t)~raw.size(),(uint8_t)(~raw.size()>>8)};b.insert(b.end(),raw.begin(),raw.end());le32(b,crc32(raw.data(),raw.size()));le32(b,(uint32_t)raw.size());return b;}
static Bytes archive(const char*name,const char*payload){Bytes a;entry(a,".",0040755u,nullptr);entry(a,name,0100755u,payload);entry(a,"TRAILER!!!",0,nullptr);return a;}
int main(){const Bytes raw=archive("init","native-init");uint8_t workspace[4096]{};uint64_t size=0;chimera_cpio_summary s{};
const int raw_rc=chimera_initramfs_prepare_newc(raw.data(),raw.size(),workspace,sizeof(workspace),&size,&s);if(raw_rc!=CHIMERA_CPIO_OK){std::fprintf(stderr,"raw CPIO ingest failed: rc=%d size=%llu archive=%llu entries=%u init=%u\\n",raw_rc,(unsigned long long)size,(unsigned long long)raw.size(),s.entries,s.has_init);}assert(raw_rc==CHIMERA_CPIO_OK);assert(size==raw.size()&&s.entries==2u&&s.has_init==1u);
const Bytes compressed=gzip_stored(raw);std::memset(workspace,0,sizeof(workspace));assert(chimera_initramfs_prepare_newc(compressed.data(),compressed.size(),workspace,sizeof(workspace),&size,&s)==CHIMERA_CPIO_OK);assert(size==raw.size()&&std::memcmp(workspace,raw.data(),raw.size())==0&&s.has_init==1u);
assert(chimera_initramfs_prepare_newc(compressed.data(),compressed.size(),workspace,64,&size,&s)==CHIMERA_CPIO_E_LIMIT);
Bytes bad=compressed;bad[bad.size()-8]^=1;assert(chimera_initramfs_prepare_newc(bad.data(),bad.size(),workspace,sizeof(workspace),&size,&s)==CHIMERA_CPIO_E_COMPRESSION&&size==0);
const Bytes traversal=archive("../outside","x");const Bytes evil=gzip_stored(traversal);assert(chimera_initramfs_prepare_newc(evil.data(),evil.size(),workspace,sizeof(workspace),&size,&s)==CHIMERA_CPIO_E_PATH);

// Duplicate normalized paths must fail closed.
Bytes duplicate;entry(duplicate,"same",0100644u,"a");entry(duplicate,"same",0100644u,"b");entry(duplicate,"TRAILER!!!",0,nullptr);
chimera_cpio_summary checked{};assert(chimera_cpio_validate_newc(duplicate.data(),duplicate.size(),&checked)==CHIMERA_CPIO_E_PATH);
// A regular file cannot also be a parent directory of another entry.
Bytes prefix;entry(prefix,"node",0100644u,"x");entry(prefix,"node/child",0100644u,"y");entry(prefix,"TRAILER!!!",0,nullptr);
assert(chimera_cpio_validate_newc(prefix.data(),prefix.size(),&checked)==CHIMERA_CPIO_E_PATH);
// Directory prefixes are valid when the parent entry is explicitly a directory.
Bytes directory;entry(directory,"node/",0040755u,nullptr);entry(directory,"node/child",0100644u,"y");entry(directory,"TRAILER!!!",0,nullptr);
assert(chimera_cpio_validate_newc(directory.data(),directory.size(),&checked)==CHIMERA_CPIO_OK);
// Reject symlink targets that try to escape the archive root.
Bytes symlink;entry(symlink,"link",0120777u,"../outside");entry(symlink,"TRAILER!!!",0,nullptr);
assert(chimera_cpio_validate_newc(symlink.data(),symlink.size(),&checked)==CHIMERA_CPIO_E_PATH);
// A truncated gzip stream and concatenated gzip members are not accepted.
Bytes truncated=compressed;truncated.pop_back();assert(chimera_initramfs_prepare_newc(truncated.data(),truncated.size(),workspace,sizeof(workspace),&size,&s)==CHIMERA_CPIO_E_COMPRESSION);
Bytes concatenated=compressed;concatenated.insert(concatenated.end(),compressed.begin(),compressed.end());
assert(chimera_initramfs_prepare_newc(concatenated.data(),concatenated.size(),workspace,sizeof(workspace),&size,&s)==CHIMERA_CPIO_E_COMPRESSION);
std::puts("bounded initramfs ingestion: raw/gzip, capacity, CRC and traversal checks passed");}
