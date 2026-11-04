#include "chimera/registry.h"
namespace {
static uint16_t r16(const uint8_t*p){return (uint16_t)p[0]|((uint16_t)p[1]<<8);}
static uint32_t r32(const uint8_t*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static uint64_t r64(const uint8_t*p){return (uint64_t)r32(p)|((uint64_t)r32(p+4)<<32);}
static bool valid_path(const uint8_t*p,uint16_t n){
 if(!p||!n||p[0]=='/'||p[n-1]=='/')return false;
 uint16_t segment=0;
 for(uint16_t i=0;i<n;++i){uint8_t x=p[i];if(x=='/'){if(!segment||(segment==1&&p[i-1]=='.')||(segment==2&&p[i-1]=='.'&&p[i-2]=='.'))return false;segment=0;continue;}
  if(!((x>='a'&&x<='z')||(x>='0'&&x<='9')||x=='.'||x=='_'||x=='-'))return false;++segment;}
 return !((segment==1&&p[n-1]=='.')||(segment==2&&p[n-1]=='.'&&p[n-2]=='.'));
}
static bool path_eq(const uint8_t*p,uint16_t n,const char*s){uint16_t i=0;for(;i<n&&s[i];++i)if(p[i]!=(uint8_t)s[i])return false;return i==n&&s[i]==0;}
}
extern "C" uint32_t koronos_registry_crc32(const uint8_t*p,uint32_t n){uint32_t c=0xffffffffu;if(!p&&n)return 0;for(uint32_t i=0;i<n;++i){c^=p[i];for(uint32_t b=0;b<8;++b)c=(c>>1)^(0xedb88320u&(0u-(c&1u)));}return ~c;}
extern "C" int koronos_registry_validate(const void*raw,uint32_t n,koronos_registry_view*out){
 static const uint8_t m[8]={'C','H','M','R','G','0','1',0};if(!raw||!out||n<40)return 0;const uint8_t*p=(const uint8_t*)raw;
 for(uint32_t i=0;i<8;++i)if(p[i]!=m[i])return 0;
 uint32_t count=r32(p+20);if(r16(p+8)!=1||r16(p+10)!=0||r32(p+12)!=40||r32(p+16)!=n||count>4096||r32(p+36)!=koronos_registry_crc32(p,36)||r32(p+32)!=koronos_registry_crc32(p+40,n-40))return 0;
 uint32_t off=40;for(uint32_t i=0;i<count;++i){if(off>n||n-off<8)return 0;uint16_t pl=r16(p+off);uint8_t ty=p[off+2],fl=p[off+3];uint32_t vl=r32(p+off+4);off+=8;
 if(!pl||pl>255||fl||ty<1||ty>5||vl>(1u<<20)||(uint64_t)off+pl+vl>n)return 0;
 if(!valid_path(p+off,pl))return 0;
 uint32_t prev=40;for(uint32_t j=0;j<i;++j){uint16_t oldpl=r16(p+prev);uint32_t oldvl=r32(p+prev+4);if(oldpl==pl){bool same=true;for(uint32_t k=0;k<pl;++k)if(p[prev+8+k]!=p[off+k]){same=false;break;}if(same)return 0;}prev+=(uint32_t)8+oldpl+oldvl;}
 const uint8_t*v=p+off+pl;
 if((ty==3&&(vl!=1||v[0]>1))||(ty==1&&vl!=4)||(ty==2&&vl!=8))return 0;off+=(uint32_t)pl+vl;}
 if(off!=n)return 0;out->data=p;out->size=n;out->entry_count=count;out->generation=r64(p+24);return 1;
}
extern "C" int koronos_registry_find(const koronos_registry_view*v,const char*s,uint8_t t,const uint8_t**value,uint32_t*size){
 if(!v||!v->data||!s||!value||!size)return 0;uint32_t off=40;for(uint32_t i=0;i<v->entry_count;++i){const uint8_t*p=v->data;uint16_t pl=r16(p+off);uint8_t ty=p[off+2];uint32_t vl=r32(p+off+4);off+=8;
 if(path_eq(p+off,pl,s)&&(!t||t==ty)){*value=p+off+pl;*size=vl;return 1;}off+=(uint32_t)pl+vl;}return 0;
}
extern "C" int koronos_registry_read_u64(const koronos_registry_view*v,const char*s,uint64_t*out){const uint8_t*p=nullptr;uint32_t n=0;if(!out||!koronos_registry_find(v,s,0,&p,&n))return 0;if(n==4){*out=r32(p);return 1;}if(n==8){*out=r64(p);return 1;}return 0;}
extern "C" int koronos_registry_read_bool(const koronos_registry_view*v,const char*s,uint8_t*out){const uint8_t*p=nullptr;uint32_t n=0;if(!out||!koronos_registry_find(v,s,KORONOS_REG_BOOL,&p,&n)||n!=1||p[0]>1)return 0;*out=p[0];return 1;}
