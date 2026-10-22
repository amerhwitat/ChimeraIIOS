#include "chimera/ramfs.h"
#include "chimera/initramfs_cpio.h"
#include <stddef.h>
#include <stdint.h>
struct chimera_ramfs_node { char *name; uint32_t name_length,type,explicit_entry; uint64_t size; uint8_t *data; chimera_ramfs_node *parent,*children,*next; };
namespace {
static bool add_ok(uint64_t a,uint64_t b,uint64_t limit,uint64_t*out){if(a>limit||b>limit-a)return false;*out=a+b;return true;}
static bool align4(uint64_t v,uint64_t limit,uint64_t*out){if(v>UINT64_MAX-3u)return false;uint64_t n=(v+3u)&~uint64_t(3u);if(n>limit)return false;*out=n;return true;}
static uint32_t hex8(const uint8_t*p,bool*ok){uint32_t v=0;for(uint32_t i=0;i<8;i++){uint8_t c=p[i];uint32_t d;if(c>='0'&&c<='9')d=c-'0';else if(c>='a'&&c<='f')d=c-'a'+10u;else if(c>='A'&&c<='F')d=c-'A'+10u;else{*ok=false;return 0;}v=(v<<4)|d;}return v;}
static void copy_bytes(void*d,const void*s,uint64_t n){auto*a=(uint8_t*)d;const auto*b=(const uint8_t*)s;for(uint64_t i=0;i<n;i++)a[i]=b[i];}
static bool same(const char*a,const char*b,uint32_t n){for(uint32_t i=0;i<n;i++)if(a[i]!=b[i])return false;return true;}
static void destroy_node(chimera_ramfs_node*n,const chimera_ramfs_allocator*a){if(!n)return;auto*c=n->children;while(c){auto*next=c->next;destroy_node(c,a);c=next;}if(n->data)a->free(n->data,a->context);if(n->name)a->free(n->name,a->context);a->free(n,a->context);}
static chimera_ramfs_node*new_node(const char*name,uint32_t len,uint32_t type,chimera_ramfs_node*parent,const chimera_ramfs_allocator*a){auto*n=(chimera_ramfs_node*)a->alloc(sizeof(chimera_ramfs_node),a->context);if(!n)return nullptr;n->name=nullptr;n->name_length=len;n->type=type;n->explicit_entry=0;n->size=0;n->data=nullptr;n->parent=parent;n->children=nullptr;n->next=nullptr;n->name=(char*)a->alloc((uint64_t)len+1u,a->context);if(!n->name){a->free(n,a->context);return nullptr;}for(uint32_t i=0;i<len;i++)n->name[i]=name[i];n->name[len]=0;if(parent){n->next=parent->children;parent->children=n;}return n;}
static chimera_ramfs_node*find_child(chimera_ramfs_node*p,const char*name,uint32_t len){for(auto*n=p->children;n;n=n->next)if(n->name_length==len&&same(n->name,name,len))return n;return nullptr;}
static bool component_ok(const char*p,uint32_t n){if(!n||(n==1&&p[0]=='.')||(n==2&&p[0]=='.'&&p[1]=='.'))return false;for(uint32_t i=0;i<n;i++)if((uint8_t)p[i]<0x20u||p[i]=='\\'||p[i]=='/')return false;return true;}
static void unlink_node(chimera_ramfs_node*n){if(!n||!n->parent)return;auto**p=&n->parent->children;while(*p&&*p!=n)p=&(*p)->next;if(*p==n)*p=n->next;n->parent=nullptr;n->next=nullptr;}
static int insert_path(chimera_ramfs_node*root,const char*path,uint32_t length,uint32_t type,const uint8_t*payload,uint32_t bytes,const chimera_ramfs_allocator*a,uint64_t*total,uint32_t*node_count,uint32_t max_nodes){
 if(length==1&&path[0]=='.'&&type==1){if(root->explicit_entry)return CHIMERA_RAMFS_E_DUPLICATE;root->explicit_entry=1;return 0;}
 if(!length||path[0]=='/'||path[length-1]=='/')return CHIMERA_RAMFS_E_PATH;auto*cur=root;uint32_t start=0;
 for(uint32_t i=0;i<=length;i++){if(i<length&&path[i]!='/')continue;uint32_t n=i-start; if(!component_ok(path+start,n))return CHIMERA_RAMFS_E_PATH;bool final=i==length;uint32_t wanted=final?type:1u;auto*child=find_child(cur,path+start,n);
  if(child){if(child->type!=wanted)return CHIMERA_RAMFS_E_CONFLICT;if(final){if(child->explicit_entry)return CHIMERA_RAMFS_E_DUPLICATE;if(type==2u&&child->children)return CHIMERA_RAMFS_E_CONFLICT;child->explicit_entry=1;if(type==2u&&bytes){child->data=(uint8_t*)a->alloc(bytes,a->context);if(!child->data){child->explicit_entry=0;return CHIMERA_RAMFS_E_NOMEM;}copy_bytes(child->data,payload,bytes);}child->size=bytes;*total+=bytes;return 0;}}
  else{if(*node_count>=max_nodes)return CHIMERA_RAMFS_E_LIMIT;child=new_node(path+start,n,wanted,cur,a);if(!child)return CHIMERA_RAMFS_E_NOMEM;++*node_count;if(final){child->explicit_entry=1;if(type==2u&&bytes){child->data=(uint8_t*)a->alloc(bytes,a->context);if(!child->data){unlink_node(child);destroy_node(child,a);--*node_count;return CHIMERA_RAMFS_E_NOMEM;}copy_bytes(child->data,payload,bytes);}child->size=bytes;*total+=bytes;return 0;}}
  if(child->type!=1u)return CHIMERA_RAMFS_E_CONFLICT;cur=child;start=i+1u;
 }return CHIMERA_RAMFS_E_PATH;
}
}
extern "C" void chimera_ramfs_destroy(chimera_ramfs_node*r,const chimera_ramfs_allocator*a){if(r&&a&&a->free)destroy_node(r,a);}
extern "C" int chimera_ramfs_extract_newc(const void*input,uint64_t size,const chimera_ramfs_allocator*a,const chimera_ramfs_limits*requested,chimera_ramfs_node**out){
 if(out)*out=nullptr;if(!input||!a||!a->alloc||!a->free||!out||!requested)return CHIMERA_RAMFS_E_ARGUMENT;
 chimera_ramfs_limits lim=*requested;if(!lim.max_entries||lim.max_entries>CHIMERA_RAMFS_MAX_ENTRIES)lim.max_entries=CHIMERA_RAMFS_MAX_ENTRIES;if(!lim.max_path_bytes||lim.max_path_bytes>CHIMERA_RAMFS_MAX_PATH)lim.max_path_bytes=CHIMERA_RAMFS_MAX_PATH;if(!lim.max_file_bytes||lim.max_file_bytes>CHIMERA_RAMFS_MAX_FILE_BYTES)lim.max_file_bytes=CHIMERA_RAMFS_MAX_FILE_BYTES;if(!lim.max_total_bytes||lim.max_total_bytes>CHIMERA_RAMFS_MAX_TOTAL_BYTES)lim.max_total_bytes=CHIMERA_RAMFS_MAX_TOTAL_BYTES;
 if(size<110u||size>CHIMERA_RAMFS_MAX_TOTAL_BYTES)return CHIMERA_RAMFS_E_LIMIT;chimera_cpio_summary preflight{};if(chimera_cpio_validate_newc(input,size,&preflight)!=CHIMERA_CPIO_OK)return CHIMERA_RAMFS_E_HEADER;auto*b=(const uint8_t*)input;uint64_t off=0,total=0;uint32_t entries=0,node_count=1;bool trailer=false;auto*root=new_node("",0,1,nullptr,a);if(!root)return CHIMERA_RAMFS_E_NOMEM;
 while(off<size){uint64_t he=0;if(!add_ok(off,110u,size,&he)){destroy_node(root,a);return CHIMERA_RAMFS_E_BOUNDS;}const uint8_t*h=b+off;bool ok=true;if(!(h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&(h[5]=='1'||h[5]=='2'))){destroy_node(root,a);return CHIMERA_RAMFS_E_HEADER;}
  bool crc=h[5]=='2';uint32_t mode=hex8(h+14,&ok),nlink=hex8(h+38,&ok),filesize=hex8(h+54,&ok),namesize=hex8(h+94,&ok),check=hex8(h+102,&ok);if(!ok||namesize<1u||namesize>lim.max_path_bytes+1u){destroy_node(root,a);return CHIMERA_RAMFS_E_HEADER;}
  uint64_t ne=0,na=0,de=0,da=0;if(!add_ok(he,namesize,size,&ne)||!align4(ne,size,&na)||!add_ok(na,filesize,size,&de)||!align4(de,size,&da)){destroy_node(root,a);return CHIMERA_RAMFS_E_BOUNDS;}const uint8_t*name=b+he;if(name[namesize-1u]){destroy_node(root,a);return CHIMERA_RAMFS_E_PATH;}for(uint32_t i=0;i+1u<namesize;i++)if(!name[i]){destroy_node(root,a);return CHIMERA_RAMFS_E_PATH;}
  bool is_trailer=namesize==11u;static const char tr[]="TRAILER!!!";if(is_trailer)for(uint32_t i=0;i<10u;i++)if(name[i]!=(uint8_t)tr[i])is_trailer=false;if(is_trailer){if(filesize||check){destroy_node(root,a);return CHIMERA_RAMFS_E_TRAILER;}trailer=true;off=da;break;}
  if(++entries>lim.max_entries||filesize>lim.max_file_bytes||filesize>lim.max_total_bytes-total){destroy_node(root,a);return CHIMERA_RAMFS_E_LIMIT;}if(crc){uint32_t sum=0;for(uint32_t i=0;i<filesize;i++)sum+=b[na+i];if(sum!=check){destroy_node(root,a);return CHIMERA_RAMFS_E_CHECKSUM;}}else if(check){destroy_node(root,a);return CHIMERA_RAMFS_E_CHECKSUM;}
  uint32_t ft=mode&0170000u,type=ft==0040000u?1u:(ft==0100000u?2u:0u);if(type==2u&&nlink>1u){destroy_node(root,a);return CHIMERA_RAMFS_E_TYPE;}if(!type){destroy_node(root,a);return CHIMERA_RAMFS_E_TYPE;}uint32_t plen=namesize-1u;if(plen&&name[plen-1u]=='/'){if(type!=1u){destroy_node(root,a);return CHIMERA_RAMFS_E_PATH;}--plen;}if(plen>lim.max_path_bytes){destroy_node(root,a);return CHIMERA_RAMFS_E_LIMIT;}
  int rc=insert_path(root,(const char*)name,plen,type,b+na,filesize,a,&total,&node_count,lim.max_entries);if(rc){destroy_node(root,a);return rc;}off=da;
 }
 if(!trailer||off>size){destroy_node(root,a);return CHIMERA_RAMFS_E_TRAILER;}for(uint64_t i=off;i<size;i++)if(b[i]){destroy_node(root,a);return CHIMERA_RAMFS_E_TRAILER;}*out=root;return CHIMERA_RAMFS_OK;
}
extern "C" const chimera_ramfs_node*chimera_ramfs_lookup(const chimera_ramfs_node*r,const char*path){if(!r||!path)return nullptr;while(*path=='/')++path;if(!*path||(*path=='.'&&path[1]==0))return r;auto*cur=(chimera_ramfs_node*)r;const char*start=path;for(const char*p=path;;++p){if(*p!='/'&&*p)continue;uint32_t n=(uint32_t)(p-start);if(!component_ok(start,n))return nullptr;cur=find_child(cur,start,n);if(!cur)return nullptr;if(!*p)return cur;if(cur->type!=1u)return nullptr;start=p+1;}}
extern "C" int chimera_ramfs_read(const chimera_ramfs_node*n,uint64_t off,void*dst,uint64_t len,uint64_t*out){if(out)*out=0;if(!n||!out||(!dst&&len))return CHIMERA_RAMFS_E_ARGUMENT;if(n->type!=2u)return CHIMERA_RAMFS_E_TYPE;if(off>=n->size||!len)return 0;uint64_t count=n->size-off;if(count>len)count=len;copy_bytes(dst,n->data+off,count);*out=count;return 0;}
extern "C" uint64_t chimera_ramfs_file_size(const chimera_ramfs_node*n){return n?n->size:0;}
extern "C" int chimera_ramfs_is_directory(const chimera_ramfs_node*n){return n&&n->type==1u;}
