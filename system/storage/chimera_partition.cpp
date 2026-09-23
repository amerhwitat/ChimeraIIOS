#include "chimera_partition.hpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <algorithm>
#include <cstring>
#ifdef __linux__
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/fs.h>
#include <unistd.h>
#endif
namespace chimera::storage {
static uint16_t r16(const uint8_t*p){return p[0]|uint16_t(p[1])<<8;}
static uint32_t r32(const uint8_t*p){return r16(p)|uint32_t(r16(p+2))<<16;}
static uint64_t r64(const uint8_t*p){return r32(p)|uint64_t(r32(p+4))<<32;}
static void w16(uint8_t*p,uint16_t v){p[0]=v;p[1]=v>>8;}
static void w32(uint8_t*p,uint32_t v){w16(p,v);w16(p+2,v>>16);}
static bool size_of(const std::string&p,uint64_t&s){std::error_code e;s=std::filesystem::file_size(p,e);if(!e)return true;
#ifdef __linux__
int fd=open(p.c_str(),O_RDONLY|O_CLOEXEC);if(fd>=0){unsigned long long x=0;bool ok=ioctl(fd,BLKGETSIZE64,&x)==0;close(fd);if(ok){s=x;return true;}}
#endif
return false;}
static std::string guid(const uint8_t*p){std::ostringstream s;s<<std::hex<<std::setfill('0')<<std::setw(8)<<r32(p)<<"-"<<std::setw(4)<<r16(p+4)<<"-"<<std::setw(4)<<r16(p+6)<<"-";for(int i=8;i<10;i++)s<<std::setw(2)<<int(p[i]);s<<"-";for(int i=10;i<16;i++)s<<std::setw(2)<<int(p[i]);return s.str();}
static bool sector(std::ifstream&f,uint64_t n,std::array<uint8_t,512>&b){f.seekg(n*512);return bool(f.read((char*)b.data(),512));}
bool inspect(const std::string&p,Disk&d,std::string&e){
 uint64_t bytes;if(!size_of(p,bytes)){e="cannot determine target size";return false;}d={};d.bytes=bytes;std::ifstream f(p,std::ios::binary);if(!f){e="cannot open target";return false;}
 std::array<uint8_t,512>b{};if(!sector(f,0,b)){e="cannot read sector 0";return false;}
 if(sector(f,1,b)&&std::memcmp(b.data(),"EFI PART",8)==0){d.label="gpt";d.disk_guid=guid(b.data()+56);uint32_t count=r32(b.data()+80),esz=r32(b.data()+84);uint64_t lba=r64(b.data()+72);if(esz<128||esz>4096||count>4096){e="invalid GPT entry geometry";return false;}std::vector<uint8_t>x(size_t(count)*esz);f.seekg(lba*512);if(!f.read((char*)x.data(),x.size())){e="cannot read GPT entries";return false;}for(uint32_t i=0;i<count;i++){auto*q=x.data()+size_t(i)*esz;bool empty=true;for(int j=0;j<16;j++)if(q[j])empty=false;if(empty)continue;Partition z;z.number=i+1;z.start_lba=r64(q+32);auto last=r64(q+40);z.sectors=last>=z.start_lba?last-z.start_lba+1:0;z.type_guid=guid(q);for(int j=0;j<36;j++){uint16_t c=r16(q+56+j*2);if(c<128)z.name+=char(c);}d.partitions.push_back(z);}return true;}
 if(b[510]!=0x55||b[511]!=0xaa){d.label="unknown";return true;}d.label="mbr";for(int i=0;i<4;i++){auto*q=b.data()+446+i*16;auto s=r32(q+8),n=r32(q+12);if(s&&n)d.partitions.push_back({uint32_t(i+1),s,n,q[4],"","",q[0]==0x80});}return true;
}
bool confirmation_required(const std::string&p){return p.rfind("/dev/",0)==0||p.rfind("\\\\\\\\.\\\\",0)==0;}
bool write_mbr(const std::string&p,const std::vector<Partition>&v,std::string&e){std::fstream f(p,std::ios::in|std::ios::out|std::ios::binary);if(!f){e="target is not writable";return false;}std::array<uint8_t,512>b{};for(size_t i=0;i<v.size()&&i<4;i++){auto&q=v[i];auto*x=b.data()+446+i*16;x[4]=q.mbr_type;w32(x+8,uint32_t(q.start_lba));w32(x+12,uint32_t(q.sectors));x[0]=q.bootable?0x80:0;}b[510]=0x55;b[511]=0xaa;f.write((char*)b.data(),512);return bool(f)||(e="write failed",false);}
bool create_partition(const std::string&p,const std::string&,uint64_t start,uint64_t sectors,uint8_t type,const std::string&,const std::string&,std::string&e){Disk d;if(!inspect(p,d,e))return false;if(d.label!="mbr"){e="native write path currently requires an MBR target; use a GPT-aware migration tool before writing GPT";return false;}if(d.partitions.size()>=4){e="MBR has no free primary partition slot";return false;}for(auto&q:d.partitions)if(start<q.start_lba+q.sectors&&q.start_lba<start+sectors){e="partition overlaps existing partition";return false;}d.partitions.push_back({uint32_t(d.partitions.size()+1),start,sectors,type,"","",false});return write_mbr(p,d.partitions,e);}
bool delete_partition(const std::string&p,uint32_t n,std::string&e){Disk d;if(!inspect(p,d,e))return false;if(d.label!="mbr"){e="delete currently supports MBR targets";return false;}d.partitions.erase(std::remove_if(d.partitions.begin(),d.partitions.end(),[&](auto&q){return q.number==n;}),d.partitions.end());for(size_t i=0;i<d.partitions.size();i++)d.partitions[i].number=i+1;return write_mbr(p,d.partitions,e);}
bool wipe_partition_table(const std::string&p,std::string&e){std::fstream f(p,std::ios::in|std::ios::out|std::ios::binary);if(!f){e="target is not writable";return false;}std::array<uint8_t,512>z{};f.write((char*)z.data(),512);return bool(f)||(e="wipe failed",false);}
std::string format_bytes(uint64_t b){const char*u[]={"B","KiB","MiB","GiB","TiB"};double x=b;int i=0;while(x>=1024&&i<4){x/=1024;i++;}std::ostringstream s;s<<std::fixed<<std::setprecision(i?1:0)<<x<<" "<<u[i];return s.str();}
void print_disk(const Disk&d,std::string&o){std::ostringstream s;s<<"Disk "<<format_bytes(d.bytes)<<" label="<<d.label<<" sector=512\\n";if(!d.disk_guid.empty())s<<"GUID "<<d.disk_guid<<"\\n";s<<"#  start-LBA  sectors  size\\n";for(auto&q:d.partitions)s<<q.number<<"  "<<q.start_lba<<"  "<<q.sectors<<"  "<<format_bytes(q.sectors*512)<<"\\n";o=s.str();}
}