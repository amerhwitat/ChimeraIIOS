#include <stdint.h>
#include "chimera/user_mode.h"
#include "chimera/physmem.h"
#include "chimera/process.h"
#include "chimera/interrupt.h"

extern "C" void chimera_x86_64_enter_user(uint64_t entry, uint64_t stack_top)
    __attribute__((noreturn));

namespace {
constexpr uint64_t PRESENT=1ull, WRITE=2ull, USER=4ull, HUGE=0x80ull;
constexpr uint64_t NX=1ull<<63;
constexpr uint64_t PAGE=4096ull, HUGE_PAGE=0x200000ull;
constexpr uint64_t USER_LOW=0x0000004000000000ull;
constexpr uint64_t USER_HIGH=0x0000004000400000ull;
constexpr uint32_t PT_POOL_COUNT=32, USER_PD_POOL_COUNT=8;
alignas(4096) uint64_t pml4[512];
alignas(4096) uint64_t pdpt[512];
alignas(4096) uint64_t pd[4][512];
alignas(4096) uint64_t pt_pool[PT_POOL_COUNT][512];
alignas(4096) uint64_t user_pd_pool[USER_PD_POOL_COUNT][512];
uint32_t pt_pool_used=0, user_pd_pool_used=0;
bool nx_available=false;
alignas(16) uint8_t kernel_entry_stack[65536];

struct __attribute__((packed)) tss64 {
    uint32_t reserved0;
    uint64_t rsp0, rsp1, rsp2;
    uint64_t reserved1;
    uint64_t ist1, ist2, ist3, ist4, ist5, ist6, ist7;
    uint64_t reserved2;
    uint16_t reserved3;
    uint16_t iomap_base;
};
tss64 tss{};

alignas(16) uint64_t gdt[7];
struct __attribute__((packed)) descriptor_ptr { uint16_t limit; uint64_t base; };
descriptor_ptr gdtr{};

static void load_gdt_and_tss() {
    gdt[0]=0;
    gdt[1]=0x00AF9A000000FFFFull; // ring-0 long-mode code
    gdt[2]=0x00CF92000000FFFFull; // ring-0 data
    gdt[3]=0x00CFF2000000FFFFull; // ring-3 data, selector 0x1B
    gdt[4]=0x00AFFA000000FFFFull; // ring-3 long-mode code, selector 0x23
    tss.rsp0=(uint64_t)(kernel_entry_stack+sizeof(kernel_entry_stack));
    tss.iomap_base=sizeof(tss);
    const uint64_t base=(uint64_t)&tss;
    const uint64_t limit=sizeof(tss)-1;
    gdt[5]=(limit&0xFFFFull)|((base&0xFFFFFFull)<<16)|
           (0x89ull<<40)|(((limit>>16)&0xFull)<<48)|
           (((base>>24)&0xFFull)<<56);
    gdt[6]=base>>32;
    gdtr.limit=sizeof(gdt)-1;
    gdtr.base=(uint64_t)gdt;
    __asm__ volatile("lgdt (%0)" : : "r"(&gdtr) : "memory");
    const uint16_t selector=0x28;
    __asm__ volatile("ltr %0" : : "r"(selector) : "memory");
}

static void initialize_page_tables() {
    for(uint32_t i=0;i<512;i++) { pml4[i]=0; pdpt[i]=0; }
    for(uint32_t i=0;i<4;i++) {
        pdpt[i]=((uint64_t)&pd[i][0])|PRESENT|WRITE;
        for(uint32_t j=0;j<512;j++)
            pd[i][j]=((uint64_t)i*0x40000000ull+(uint64_t)j*HUGE_PAGE)|PRESENT|WRITE|HUGE;
    }
    pml4[0]=((uint64_t)pdpt)|PRESENT|WRITE;
    for(uint32_t i=0;i<PT_POOL_COUNT;i++)
        for(uint32_t j=0;j<512;j++) pt_pool[i][j]=0;
    for(uint32_t i=0;i<USER_PD_POOL_COUNT;i++)
        for(uint32_t j=0;j<512;j++) user_pd_pool[i][j]=0;
    pt_pool_used=0;
    user_pd_pool_used=0;

    uint32_t b=0,c=0,d=0;
    uint32_t leaf=0x80000001u;
    c=0;
    __asm__ volatile("cpuid" : "+a"(leaf), "=b"(b), "+c"(c), "=d"(d));
    nx_available=(d&(1u<<20))!=0;
    if(nx_available) {
        uint32_t lo=0,hi=0;
        __asm__ volatile("rdmsr" : "=a"(lo), "=d"(hi) : "c"(0xC0000080u));
        lo|=(1u<<11); // EFER.NXE
        __asm__ volatile("wrmsr" : : "a"(lo), "d"(hi), "c"(0xC0000080u));
    }
    (void)b;
    const uint64_t root=(uint64_t)pml4;
    __asm__ volatile("mov %0, %%cr3" : : "r"(root) : "memory");
}

static uint64_t *get_pte(uint64_t va, bool create) {
    if(va>=0x0000800000000000ull) return nullptr;
    const uint32_t pml4_i=(uint32_t)((va>>39)&0x1FFu);
    const uint32_t pdpt_i=(uint32_t)((va>>30)&0x1FFu);
    const uint32_t pd_i=(uint32_t)((va>>21)&0x1FFu);
    const uint32_t pt_i=(uint32_t)((va>>12)&0x1FFu);
    if(pml4_i!=0) return nullptr;
    pml4[0]|=USER;
    if(!(pdpt[pdpt_i]&PRESENT)) {
        if(!create||pdpt_i<4||user_pd_pool_used>=USER_PD_POOL_COUNT) return nullptr;
        uint64_t *new_pd=user_pd_pool[user_pd_pool_used++];
        for(uint32_t i=0;i<512;i++) new_pd[i]=0;
        pdpt[pdpt_i]=((uint64_t)new_pd)|PRESENT|WRITE|USER;
    } else {
        pdpt[pdpt_i]|=USER;
    }
    uint64_t *directory=(uint64_t*)(uintptr_t)(pdpt[pdpt_i]&0x000FFFFFFFFFF000ull);
    uint64_t &pde=directory[pd_i];
    if(pde&HUGE) {
        if(!create) return nullptr;
        if(pt_pool_used>=PT_POOL_COUNT) return nullptr;
        uint64_t *pt=pt_pool[pt_pool_used++];
        const uint64_t base=pde&0x000FFFFFFFE00000ull;
        const uint64_t inherited=pde&(PRESENT|WRITE);
        for(uint32_t i=0;i<512;i++) pt[i]=(base+(uint64_t)i*PAGE)|inherited;
        pde=((uint64_t)pt)|PRESENT|WRITE|USER;
    } else if(!(pde&PRESENT)) {
        if(!create||pt_pool_used>=PT_POOL_COUNT) return nullptr;
        uint64_t *pt=pt_pool[pt_pool_used++];
        for(uint32_t i=0;i<512;i++) pt[i]=0;
        pde=((uint64_t)pt)|PRESENT|WRITE|USER;
    } else {
        pde|=USER;
    }
    uint64_t *pt=(uint64_t*)(uintptr_t)(pde&0x000FFFFFFFFFF000ull);
    return &pt[pt_i];
}

static int alloc_page(void*,uint64_t *physical,void **alias) {
    if(!physical||!alias) return -1;
    if(chimera_physmem_alloc_page(physical)!=0) return -2;
    if(*physical>=0x100000000ull) { chimera_physmem_free_page(*physical); return -3; }
    *alias=(void*)(uintptr_t)(*physical); // identity alias under the active bootstrap map
    return 0;
}
static int map_page(void*,uint64_t va,uint64_t physical,uint32_t permissions) {
    if((va&(PAGE-1))||(physical&(PAGE-1))||physical>=0x100000000ull||
       va<USER_LOW||va>=USER_HIGH) return -1;
    uint64_t *pte=get_pte(va,true);
    if(!pte||(*pte&USER)) return -2;
    uint64_t flags=PRESENT|USER;
    if(permissions&CHIMERA_ELF_WRITE) flags|=WRITE;
    if(nx_available&&!(permissions&CHIMERA_ELF_EXEC)) flags|=NX;
    *pte=(physical&0x000FFFFFFFFFF000ull)|flags;
    __asm__ volatile("invlpg (%0)" : : "r"((uintptr_t)va) : "memory");
    return 0;
}
static void unmap_page(void*,uint64_t va) {
    uint64_t *pte=get_pte(va,false);
    if(pte&&(*pte&USER)) {
        *pte=0;
        __asm__ volatile("invlpg (%0)" : : "r"((uintptr_t)va) : "memory");
    }
}
static void free_page(void*,uint64_t physical) { (void)chimera_physmem_free_page(physical); }
static int enter_user(void*,uint64_t entry,uint64_t stack,uint32_t pid) {
    if(chimera_process_set_state(pid,CHIMERA_PROCESS_RUNNING)!=0) return -1;
    chimera_x86_64_enter_user(entry,stack);
}
const chimera_elf_loader_ops loader_ops={nullptr,alloc_page,map_page,unmap_page,free_page,enter_user};
}

extern "C" int chimera_x86_64_user_mode_init(void) {
#if !defined(__x86_64__)
    return -100;
#else
    if(!chimera_physmem_ready()) return -1;
    initialize_page_tables();
    /* User ELF mappings require hardware NX enforcement. Do not silently run
       with executable data/stack pages when EFER.NXE is unavailable. */
    if(!nx_available) return -3;
    load_gdt_and_tss();
    if(chimera_interrupt_init()!=0) return -2;
    return 0;
#endif
}
extern "C" const chimera_elf_loader_ops *chimera_x86_64_user_loader_ops(void) {
    return &loader_ops;
}
extern "C" int chimera_x86_64_user_range_valid(uint64_t address,uint64_t length) {
    if(address<USER_LOW||address>=USER_HIGH||
       length>512u||length>USER_HIGH-address) return 0;
    if(length==0) return 1;
    const uint64_t end=address+length;
    uint64_t page=address&~(PAGE-1);
    const uint64_t last=(end-1u)&~(PAGE-1);
    for(;;) {
        uint64_t *pte=get_pte(page,false);
        if(!pte||!(*pte&PRESENT)||!(*pte&USER)) return 0;
        if(page==last) break;
        page+=PAGE;
    }
    return 1;
}
