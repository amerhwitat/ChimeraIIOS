#include <stdint.h>
#include <stddef.h>
#include "chimera/vfs.h"
namespace {
constexpr uint32_t MODE_TYPE = 0170000u, MODE_REG = 0100000u, MODE_DIR = 0040000u;
constexpr uint32_t OPEN_WRITE = 1u, SEEK_SET = 0u, SEEK_CUR = 1u, SEEK_END = 2u;
constexpr uint32_t TEMP_FILES = 16u, TEMP_BYTES = 4096u, PATH_BYTES = 256u;
struct File { const char *path; const uint8_t *data; uint32_t size; uint32_t mode; };
struct Fd { int file; uint32_t position; uint8_t used; uint8_t writable; };
struct Temp { char path[PATH_BYTES]; uint8_t data[TEMP_BYTES]; uint32_t size; uint8_t used; };
static File files[KORONOS_VFS_MAX_FILES]{};
static Fd fds[KORONOS_VFS_MAX_FDS]{};
static Temp temps[TEMP_FILES]{};
static uint32_t count=0;
static uint8_t mounted=0;
static uint8_t archive_busy=0;
static void zero(void *p,uint64_t n){uint8_t*d=(uint8_t*)p;for(uint64_t i=0;i<n;i++)d[i]=0;}
static uint32_t hex8(const uint8_t*p,bool*ok){uint32_t v=0;for(uint32_t i=0;i<8;i++){uint8_t c=p[i];uint32_t d;if(c>='0'&&c<='9')d=c-'0';else if(c>='a'&&c<='f')d=c-'a'+10;else if(c>='A'&&c<='F')d=c-'A'+10;else{*ok=false;return 0;}v=(v<<4)|d;}return v;}
static bool add(uint64_t a,uint64_t b,uint64_t*out){if(a>UINT64_MAX-b)return false;*out=a+b;return true;}
static bool align4(uint64_t n,uint64_t*out){uint64_t t;if(!add(n,3,&t))return false;*out=t&~3ull;return true;}
static bool normalize(const char*in,char*out){if(!in)return false;uint32_t i=0,o=0;while(in[i]=='/')i++;if(!in[i]){out[0]='/';out[1]=0;return true;}out[o++]='/';while(in[i]){uint32_t start=i;while(in[i]&&in[i]!='/'){if(o>=PATH_BYTES-2)return false;out[o++]=in[i++];}uint32_t n=i-start;if((n==1&&out[o-1]=='.')||(n==2&&out[o-2]=='.'&&out[o-1]=='.'))return false;if(in[i]=='/'){while(in[i]=='/')i++;if(in[i])out[o++]='/';}}out[o]=0;return o>0;}
static int find_file(const char*p){for(uint32_t i=0;i<count;i++){const char*a=files[i].path;uint32_t j=0;while(a[j]&&p[j]&&a[j]==p[j])j++;if(!a[j]&&!p[j])return (int)i;}return -1;}
static int find_temp(const char*p){for(uint32_t i=0;i<TEMP_FILES;i++)if(temps[i].used){uint32_t j=0;while(temps[i].path[j]&&p[j]&&temps[i].path[j]==p[j])j++;if(!temps[i].path[j]&&!p[j])return (int)i;}return -1;}
static int alloc_fd(int file,bool writable){for(uint32_t i=0;i<KORONOS_VFS_MAX_FDS;i++)if(!fds[i].used){fds[i]={file,0,1,(uint8_t)writable};return (int)i;}return -24;}
}
extern "C" int koronos_vfs_mount_cpio(const void*archive,uint64_t length){
 if(!archive||length<110||length>256ull*1024ull*1024ull||archive_busy)return -1;
 archive_busy=1;count=0;zero(files,sizeof(files));zero(fds,sizeof(fds));mounted=0;
 const uint8_t*b=(const uint8_t*)archive;uint64_t off=0;bool trailer=false;
 while(off+110<=length){
  const uint8_t*h=b+off;bool ok=true;
  const bool crc=h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&h[5]=='2';
  const bool newc=h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&h[5]=='1';
  if(!crc&&!newc)break;
  const uint32_t mode=hex8(h+14,&ok),filesize=hex8(h+54,&ok),namesize=hex8(h+94,&ok),check=hex8(h+102,&ok);
  uint64_t nameoff=0,dataoff=0,next=0;
  if(!ok||namesize<1||namesize>PATH_BYTES||!add(off,110,&nameoff)||!add(nameoff,namesize,&next)||!align4(next,&dataoff)||dataoff>length||filesize>length-dataoff)break;
  if(h[110+namesize-1]!=0)break;
  char path[PATH_BYTES];uint32_t n=namesize-1;
  if(n==10&&h[110]=='T'&&h[111]=='R'&&h[112]=='A'&&h[113]=='I'&&h[114]=='L'&&h[115]=='E'&&h[116]=='R'&&h[117]=='!'&&h[118]=='!'&&h[120]==0){trailer=true;off=dataoff+filesize;break;}
  if(n>=2&&h[110]=='.'&&h[111]=='/') {for(uint32_t i=0;i<n-2;i++)path[i]=(char)h[112+i];path[n-2]=0;}
  else {for(uint32_t i=0;i<n;i++)path[i]=(char)h[110+i];path[n]=0;}
  char normalized[PATH_BYTES];if(!normalize(path,normalized))break;
  const uint32_t type=mode&MODE_TYPE;
  if(type==MODE_REG||type==MODE_DIR){
   if(count>=KORONOS_VFS_MAX_FILES||find_file(normalized)>=0)break;
   if(type==MODE_DIR&&filesize!=0)break;
   if(crc){uint32_t sum=0;for(uint32_t i=0;i<filesize;i++)sum+=b[dataoff+i];if(sum!=check)break;}
   static char names[KORONOS_VFS_MAX_FILES][PATH_BYTES];
   uint32_t k=0;while(normalized[k]&&k<PATH_BYTES-1){names[count][k]=normalized[k];k++;}names[count][k]=0;
   files[count]={names[count],b+dataoff,filesize,mode};count++;
  }else if(type!=0&&type!=0120000u&&type!=0020000u&&type!=0060000u&&type!=0010000u){break;}
  uint64_t end=0;if(!add(dataoff,filesize,&end)||!align4(end,&off)||off>length)break;
 }
 if(!trailer||count==0){count=0;archive_busy=0;return -2;}
 mounted=1;archive_busy=0;return 0;
}
extern "C" int koronos_vfs_is_mounted(void){return mounted?1:0;}
extern "C" uint32_t koronos_vfs_file_count(void){return count;}
extern "C" int koronos_vfs_open(const char*path,uint32_t flags){
 if(!mounted||!path||(flags&~OPEN_WRITE))return -9;
 char normalized[PATH_BYTES];if(!normalize(path,normalized))return -22;
 if(normalized[0]=='/'&&normalized[1]=='t'&&normalized[2]=='m'&&normalized[3]=='p'&&(normalized[4]=='/'||normalized[4]==0)){
  int t=find_temp(normalized);if(t<0&&(flags&OPEN_WRITE)){for(uint32_t i=0;i<TEMP_FILES;i++)if(!temps[i].used){t=(int)i;temps[i].used=1;uint32_t j=0;while(normalized[j]&&j<PATH_BYTES-1){temps[i].path[j]=normalized[j];j++;}temps[i].path[j]=0;break;}}
  if(t>=0)return alloc_fd(-100-t,(flags&OPEN_WRITE)!=0);return -2;
 }
 int f=find_file(normalized);if(f<0||((files[f].mode&MODE_TYPE)!=MODE_REG))return -2;
 if(flags&OPEN_WRITE)return -30;
 return alloc_fd(f,false);
}
extern "C" int64_t koronos_vfs_read(int fd,void*buffer,uint64_t length){
 if(fd<0||fd>=(int)KORONOS_VFS_MAX_FDS||!fds[fd].used||(!buffer&&length))return -9;
 Fd&d=fds[fd];const uint8_t*data=nullptr;uint64_t size=0;
 if(d.file<=-100){Temp&t=temps[-100-d.file];data=t.data;size=t.size;}else{File&f=files[d.file];data=f.data;size=f.size;}
 if(d.position>=size)return 0;uint64_t n=length<size-d.position?length:size-d.position;
 uint8_t*out=(uint8_t*)buffer;for(uint64_t i=0;i<n;i++)out[i]=data[d.position+i];d.position+=(uint32_t)n;return (int64_t)n;
}
extern "C" int64_t koronos_vfs_write(int fd,const void*buffer,uint64_t length){
 if(fd<0||fd>=(int)KORONOS_VFS_MAX_FDS||!fds[fd].used||!fds[fd].writable||(!buffer&&length))return -9;
 Fd&d=fds[fd];if(d.file>-100)return -30;Temp&t=temps[-100-d.file];
 if(length>TEMP_BYTES-d.position)return -28;const uint8_t*in=(const uint8_t*)buffer;
 for(uint64_t i=0;i<length;i++)t.data[d.position+i]=in[i];d.position+=(uint32_t)length;if(d.position>t.size)t.size=d.position;return (int64_t)length;
}
extern "C" int64_t koronos_vfs_seek(int fd,int64_t offset,uint32_t whence){
 if(fd<0||fd>=(int)KORONOS_VFS_MAX_FDS||!fds[fd].used)return -9;
 Fd&d=fds[fd];uint64_t size=d.file<=-100?temps[-100-d.file].size:files[d.file].size;
 int64_t base=whence==SEEK_SET?0:(whence==SEEK_CUR?(int64_t)d.position:(whence==SEEK_END?(int64_t)size:-1));
 if(base<0||offset< -base||offset>INT32_MAX-base)return -22;d.position=(uint32_t)(base+offset);return (int64_t)d.position;
}
extern "C" int koronos_vfs_close(int fd){if(fd<0||fd>=(int)KORONOS_VFS_MAX_FDS||!fds[fd].used)return -9;fds[fd]={};return 0;}
