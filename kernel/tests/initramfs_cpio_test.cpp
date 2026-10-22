#include "chimera/initramfs_cpio.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
static void field(std::vector<uint8_t>& b,size_t off,uint32_t v) {
  static const char h[]="0123456789abcdef";
  for(int i=7;i>=0;--i){b[off+(size_t)i]=(uint8_t)h[v&15u];v>>=4;}
}
static void entry(std::vector<uint8_t>& b,const char* name,uint32_t mode,const char* data) {
  const size_t start=b.size(); b.resize(start+110,0);
  std::memcpy(b.data()+start,"070701",6);
  field(b,start+14,mode);
  const uint32_t n=(uint32_t)std::strlen(name)+1u;
  const uint32_t z=data?(uint32_t)std::strlen(data):0u;
  field(b,start+54,z); field(b,start+94,n); field(b,start+102,0);
  b.insert(b.end(),name,name+n);
  while(b.size()%4u)b.push_back(0);
  if(data)b.insert(b.end(),data,data+z);
  while(b.size()%4u)b.push_back(0);
}
int main() {
  std::vector<uint8_t> a;
  entry(a,"init",0100755u,"ELF");
  entry(a,"etc",0040755u,nullptr);
  entry(a,"TRAILER!!!",0,nullptr);
  chimera_cpio_summary s{};
  assert(chimera_cpio_validate_newc(a.data(),a.size(),&s)==CHIMERA_CPIO_OK);
  assert(s.entries==2u&&s.regular_files==1u&&s.directories==1u&&s.has_init==1u&&s.payload_bytes==3u);
  auto truncated=a; truncated.pop_back();
  assert(chimera_cpio_validate_newc(truncated.data(),truncated.size(),&s)!=CHIMERA_CPIO_OK);
  std::vector<uint8_t> traversal;
  entry(traversal,"../escape",0100644u,"x"); entry(traversal,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(traversal.data(),traversal.size(),&s)==CHIMERA_CPIO_E_PATH);
  const uint8_t gzip[]={0x1f,0x8b,0,0,0,0};
  assert(chimera_cpio_validate_newc(gzip,sizeof(gzip),&s)==CHIMERA_CPIO_E_COMPRESSION);
  assert(chimera_cpio_validate_newc(a.data(),CHIMERA_CPIO_MAX_ARCHIVE_BYTES+1ull,&s)==CHIMERA_CPIO_E_LIMIT);
  std::puts("bounded newc CPIO parser: valid archive, trailer/bounds, traversal and compression rejection passed");
}
