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
static void crc_entry(std::vector<uint8_t>& b,const char* name,uint32_t mode,const char* data) {
  const size_t start=b.size(); b.resize(start+110,0);
  std::memcpy(b.data()+start,"070702",6);
  field(b,start+14,mode);
  const uint32_t n=(uint32_t)std::strlen(name)+1u;
  const uint32_t z=data?(uint32_t)std::strlen(data):0u;
  field(b,start+54,z); field(b,start+94,n);
  uint32_t sum=0; if(data) for(uint32_t i=0;i<z;i++) sum+=static_cast<uint8_t>(data[i]);
  field(b,start+102,sum);
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
  std::vector<uint8_t> sbin_init;
  entry(sbin_init,"sbin/init",0100755u,"ELF");
  entry(sbin_init,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(sbin_init.data(),sbin_init.size(),&s)==CHIMERA_CPIO_OK);
  assert(s.has_init==1u);
  std::vector<uint8_t> symlink_init;
  entry(symlink_init,"init",0120777u,"safe-target");
  entry(symlink_init,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(symlink_init.data(),symlink_init.size(),&s)==CHIMERA_CPIO_OK);
  assert(s.has_init==0u);
  std::vector<uint8_t> traversal;
  entry(traversal,"../escape",0100644u,"x"); entry(traversal,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(traversal.data(),traversal.size(),&s)==CHIMERA_CPIO_E_PATH);
  std::vector<uint8_t> embedded_nul;
  entry(embedded_nul,"init",0100755u,"ELF");
  entry(embedded_nul,"TRAILER!!!",0,nullptr);
  /* Turn the fourth visible name byte into NUL while retaining the final NUL. */
  embedded_nul[112]=0;
  assert(chimera_cpio_validate_newc(embedded_nul.data(),embedded_nul.size(),&s)==CHIMERA_CPIO_E_PATH);
  std::vector<uint8_t> duplicate;
  entry(duplicate,"init",0100755u,"ELF");
  entry(duplicate,"init",0100755u,"ELF");
  entry(duplicate,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(duplicate.data(),duplicate.size(),&s)==CHIMERA_CPIO_E_PATH);
  std::vector<uint8_t> conflict;
  entry(conflict,"node",0100644u,"x");
  entry(conflict,"node/child",0100644u,"y");
  entry(conflict,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(conflict.data(),conflict.size(),&s)==CHIMERA_CPIO_E_PATH);
  std::vector<uint8_t> crc_archive;
  crc_entry(crc_archive,"init",0100755u,"ELF");
  crc_entry(crc_archive,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(crc_archive.data(),crc_archive.size(),&s)==CHIMERA_CPIO_OK);
  auto bad_crc=crc_archive;
  /* First entry's check field is at header offset 102. */
  bad_crc[102]='0'; bad_crc[103]='0'; bad_crc[104]='0'; bad_crc[105]='0';
  bad_crc[106]='0'; bad_crc[107]='0'; bad_crc[108]='0'; bad_crc[109]='0';
  assert(chimera_cpio_validate_newc(bad_crc.data(),bad_crc.size(),&s)==CHIMERA_CPIO_E_CHECKSUM);
  std::vector<uint8_t> slash_dir;
  entry(slash_dir,"usr/",0040755u,nullptr);
  entry(slash_dir,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(slash_dir.data(),slash_dir.size(),&s)==CHIMERA_CPIO_OK);
  std::vector<uint8_t> canonical_duplicate;
  entry(canonical_duplicate,"usr",0040755u,nullptr);
  entry(canonical_duplicate,"usr/",0040755u,nullptr);
  entry(canonical_duplicate,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(canonical_duplicate.data(),canonical_duplicate.size(),&s)==CHIMERA_CPIO_E_PATH);
  std::vector<uint8_t> symlink_escape;
  entry(symlink_escape,"link",0120777u,"../outside");
  entry(symlink_escape,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(symlink_escape.data(),symlink_escape.size(),&s)==CHIMERA_CPIO_E_PATH);
  std::vector<uint8_t> symlink_absolute;
  entry(symlink_absolute,"link",0120777u,"/etc/passwd");
  entry(symlink_absolute,"TRAILER!!!",0,nullptr);
  assert(chimera_cpio_validate_newc(symlink_absolute.data(),symlink_absolute.size(),&s)==CHIMERA_CPIO_E_PATH);
  const uint8_t gzip[]={0x1f,0x8b,0,0,0,0};
  assert(chimera_cpio_validate_newc(gzip,sizeof(gzip),&s)==CHIMERA_CPIO_E_COMPRESSION);
  assert(chimera_cpio_validate_newc(a.data(),CHIMERA_CPIO_MAX_ARCHIVE_BYTES+1ull,&s)==CHIMERA_CPIO_E_LIMIT);
  std::puts("bounded newc CPIO parser: valid archive, trailer/bounds, traversal and compression rejection passed");
}
