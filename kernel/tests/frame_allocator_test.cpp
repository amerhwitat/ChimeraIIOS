#include "chimera/frame_allocator.h"
#include "chimera/multiboot_modules.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
extern "C" uint32_t chimera_multiboot_module_count(void) { return 0; }
extern "C" const chimera_boot_module *chimera_multiboot_module(uint32_t) { return nullptr; }
struct __attribute__((packed)) MmapEntry { uint64_t address,length; uint32_t type,reserved; };
struct __attribute__((packed)) MmapTag { uint32_t type,size,entry_size,entry_version; MmapEntry entries[2]; };
struct __attribute__((packed)) EndTag { uint32_t type,size; };
struct __attribute__((packed,aligned(8))) BootInfo { uint32_t total_size,reserved; MmapTag mmap; EndTag end; };
static void make_map(BootInfo &info,uint64_t usable_base,uint64_t usable_size,uint64_t reserved_base,uint64_t reserved_size) {
 memset(&info,0,sizeof(info)); info.mmap.type=6; info.mmap.size=sizeof(MmapTag); info.mmap.entry_size=sizeof(MmapEntry);
 info.mmap.entries[0]={usable_base,usable_size,1,0}; info.mmap.entries[1]={reserved_base,reserved_size,2,0};
 info.end={0,sizeof(EndTag)}; info.total_size=sizeof(BootInfo);
}
int main() {
 BootInfo info{}; make_map(info,0x100000,0x3f00000,0x800000,0x100000);
 const uint64_t info_address=reinterpret_cast<uint64_t>(&info);
 assert(koronos_frame_allocator_init(info_address,0x100000,0x200000)==0);
 assert(koronos_frame_free_count()==15616);
 const uint64_t run=koronos_frame_alloc_contiguous(3); assert(run==0x200000);
 assert(koronos_frame_free_count()==15613); assert(koronos_frame_free_contiguous(run,3)==0);
 assert(koronos_frame_free_contiguous(run,3)==-2); assert(koronos_frame_free(run+1)==-1);
 assert(koronos_frame_free_count()==15616);
 const uint64_t one=koronos_frame_alloc(); assert(one==0x200000);
 assert(koronos_frame_free(one)==0); assert(koronos_frame_free(one)==-2);
 make_map(info,0x100000,0x3f00000,0x100000000ull,0x2000);
 info.mmap.entries[1].type=1; // usable RAM above the supported ceiling
 assert(koronos_frame_allocator_init(info_address,0x100000,0x200000)==-1);
 assert(koronos_frame_free_count()==0);
 make_map(info,UINT64_MAX-0x7ff,0x2000,0,0);
 assert(koronos_frame_allocator_init(info_address,0x100000,0x200000)==-1);
 assert(koronos_frame_free_count()==0);
 puts("frame allocator: reservations, contiguous ownership, double-free, alignment, 4-GiB ceiling and overflow checks passed");
 return 0;
}
