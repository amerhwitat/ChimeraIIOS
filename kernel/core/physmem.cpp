#include "chimera/physmem.h"

namespace {
constexpr uint32_t PAGE_SHIFT=12u;
constexpr uint32_t PAGE_COUNT=(uint32_t)(CHIMERA_PHYSMEM_LIMIT_BYTES/CHIMERA_PHYSMEM_PAGE_SIZE);
constexpr uint32_t MAP_BYTES=PAGE_COUNT/8u;
constexpr uint32_t MB2_TAG_END=0u, MB2_TAG_MODULE=3u, MB2_TAG_MMAP=6u;
constexpr uint32_t MB2_MEMORY_AVAILABLE=1u;
struct Tag { uint32_t type,size; };
struct MmapHeader { uint32_t entry_size,entry_version; };
struct MmapEntry { uint64_t address,length; uint32_t type,reserved; };
static uint8_t free_map[MAP_BYTES];
static uint8_t allocated_map[MAP_BYTES];
static volatile uint32_t lock_word=0;
static volatile uint32_t initialized=0;
static uint32_t cursor=256u;
static uint64_t free_count=0;
static void lock(){while(__sync_lock_test_and_set(&lock_word,1u)){}}
static void unlock(){__sync_lock_release(&lock_word);}
static bool bit_get(const uint8_t *map,uint32_t n){return (map[n>>3]&(uint8_t)(1u<<(n&7u)))!=0;}
static void bit_set(uint8_t *map,uint32_t n,bool on){const uint8_t mask=(uint8_t)(1u<<(n&7u));if(on)map[n>>3]|=mask;else map[n>>3]&=(uint8_t)~mask;}
static void zero(void *ptr,uint64_t n){auto*p=(uint8_t*)ptr;for(uint64_t i=0;i<n;i++)p[i]=0;}
static void reserve_range(uint64_t start,uint64_t end){
 if(end<=start)return;
 if(start>=CHIMERA_PHYSMEM_LIMIT_BYTES)return;
 if(end>CHIMERA_PHYSMEM_LIMIT_BYTES)end=CHIMERA_PHYSMEM_LIMIT_BYTES;
 uint64_t first=start>>PAGE_SHIFT,last=(end+CHIMERA_PHYSMEM_PAGE_SIZE-1u)>>PAGE_SHIFT;
 if(last>PAGE_COUNT)last=PAGE_COUNT;
 for(uint64_t p=first;p<last;p++)if(bit_get(free_map,(uint32_t)p)){bit_set(free_map,(uint32_t)p,false);if(free_count) --free_count;}
}
static void available_range(uint64_t start,uint64_t length){
 if(!length||start>=CHIMERA_PHYSMEM_LIMIT_BYTES||length>UINT64_MAX-start)return;
 uint64_t end=start+length;if(end>CHIMERA_PHYSMEM_LIMIT_BYTES)end=CHIMERA_PHYSMEM_LIMIT_BYTES;
 uint64_t first=(start+CHIMERA_PHYSMEM_PAGE_SIZE-1u)>>PAGE_SHIFT,last=end>>PAGE_SHIFT;
 for(uint64_t p=first;p<last;p++){uint32_t n=(uint32_t)p;if(!bit_get(free_map,n)&&!bit_get(allocated_map,n)){bit_set(free_map,n,true);++free_count;}}
}
static bool tag_range_ok(uint64_t base,uint32_t total,uint64_t offset,uint32_t size){
 return size>=sizeof(Tag)&&offset<=total&&size<=total-offset&&base<=UINT64_MAX-offset;
}
}

extern "C" int chimera_physmem_init(uint64_t info,uint64_t kernel_base,uint64_t kernel_end){
 lock();initialized=0;free_count=0;cursor=256u;zero(free_map,sizeof(free_map));zero(allocated_map,sizeof(allocated_map));unlock();
 if(!info)return -1;
 const auto *bytes=(const uint8_t*)(uintptr_t)info;
 const uint32_t total=*(const uint32_t*)(const void*)bytes;
 if(total<16u||total>16u*1024u*1024u)return -2;
 bool found_mmap=false;
 uint64_t off=8u;
 while(off+sizeof(Tag)<=total){
  const Tag *tag=(const Tag*)(const void*)(bytes+off);
  if(!tag_range_ok(info,total,off,tag->size))return -3;
  if(tag->type==MB2_TAG_END)break;
  if(tag->type==MB2_TAG_MMAP){
   if(tag->size<sizeof(Tag)+sizeof(MmapHeader))return -4;
   const auto *mh=(const MmapHeader*)(const void*)(bytes+off+sizeof(Tag));
   if(mh->entry_size<sizeof(MmapEntry))return -5;
   const uint32_t payload=tag->size-(uint32_t)sizeof(Tag)-(uint32_t)sizeof(MmapHeader);
   if(payload%mh->entry_size)return -6;
   for(uint32_t pos=0;pos<payload;pos+=mh->entry_size){
    const auto *e=(const MmapEntry*)(const void*)((const uint8_t*)mh+sizeof(MmapHeader)+pos);
    if(e->type==MB2_MEMORY_AVAILABLE)available_range(e->address,e->length);
   }
   found_mmap=true;
  }
  uint64_t next=(off+tag->size+7u)&~7ull;
  if(next<=off||next>total)break;
  off=next;
 }
 if(!found_mmap){lock();zero(free_map,sizeof(free_map));free_count=0;unlock();return -7;}
 reserve_range(0,0x100000u);
 reserve_range(kernel_base,kernel_end);
 reserve_range(info,(uint64_t)info+total);
 off=8u;
 while(off+sizeof(Tag)<=total){
  const Tag *tag=(const Tag*)(const void*)(bytes+off);
  if(!tag_range_ok(info,total,off,tag->size))break;
  if(tag->type==MB2_TAG_END)break;
  if(tag->type==MB2_TAG_MODULE&&tag->size>=16u){
   const uint32_t start=*(const uint32_t*)(const void*)(bytes+off+8u);
   const uint32_t end=*(const uint32_t*)(const void*)(bytes+off+12u);
   if(end>=start)reserve_range(start,end);
  }
  uint64_t next=(off+tag->size+7u)&~7ull;if(next<=off||next>total)break;off=next;
 }
 lock();initialized=1;unlock();return 0;
}
extern "C" int chimera_physmem_alloc_page(uint64_t *out){
 if(!out||!initialized)return -1;
 lock();
 for(uint32_t scanned=0;scanned<PAGE_COUNT;scanned++){
  uint32_t n=cursor++;if(cursor>=PAGE_COUNT)cursor=256u;
  if(bit_get(free_map,n)){
   bit_set(free_map,n,false);bit_set(allocated_map,n,true);if(free_count)--free_count;
   *out=(uint64_t)n<<PAGE_SHIFT;unlock();return 0;
  }
 }
 unlock();return -2;
}
extern "C" int chimera_physmem_free_page(uint64_t address){
 if(!initialized||address==0||(address&(CHIMERA_PHYSMEM_PAGE_SIZE-1u))||address>=CHIMERA_PHYSMEM_LIMIT_BYTES)return -1;
 uint32_t n=(uint32_t)(address>>PAGE_SHIFT);lock();
 if(!bit_get(allocated_map,n)){unlock();return -2;}
 bit_set(allocated_map,n,false);bit_set(free_map,n,true);++free_count;unlock();return 0;
}
extern "C" uint64_t chimera_physmem_free_pages(void){lock();uint64_t n=free_count;unlock();return n;}
extern "C" uint64_t chimera_physmem_total_pages(void){return PAGE_COUNT;}
extern "C" int chimera_physmem_ready(void){return initialized?1:0;}
