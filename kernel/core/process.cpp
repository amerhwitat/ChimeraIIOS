#include "../include/chimera/process.h"
#include "chimera/nbit.h"
#include "chimera/ipc.h"

namespace {
constexpr uint32_t MAX_SEGMENTS = 16;
constexpr uint64_t PAGE = 4096;
constexpr uint64_t USER_TOP = 0x0000800000000000ull;
constexpr uint32_t PT_LOAD = 1, PF_W = 2, PF_X = 1;
struct Slot { chimera_process_image image{}; bool used = false; };
Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1, count = 0;
static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return false;
    *out = a + b; return true;
}
static uint64_t down(uint64_t x) { return x & ~(PAGE - 1); }
static bool up(uint64_t x, uint64_t *out) {
    if (x > UINT64_MAX - (PAGE - 1)) return false;
    *out = (x + PAGE - 1) & ~(PAGE - 1); return true;
}
static bool in(uint64_t off, uint64_t len, uint64_t size) {
    uint64_t end = 0; return add_ok(off, len, &end) && end <= size;
}
static int find_slot(uint32_t pid) {
    for (uint32_t i=0;i<CHIMERA_PROCESS_MAX;++i)
        if(slots[i].used&&slots[i].image.pid==pid)return (int)i;
    return -1;
}
static void retire_mode(uint32_t pid) {
    chimera_ipc_process_exit(pid);
    chimera_nbit_process_unregister(pid);
}
}
extern "C" int chimera_process_init(void) {
    for (uint32_t i=0;i<CHIMERA_PROCESS_MAX;++i) {
        if(slots[i].used)retire_mode(slots[i].image.pid);
        slots[i]={};
    }
    next_pid=1;count=0;return 0;
}
/* Validates and records a load plan; this loader currently accepts ELF64 only. */
extern "C" int chimera_process_admit_elf(const void *image,uint64_t size,
                                          uint16_t machine,uint64_t stack,
                                          chimera_process_image *out) {
    if(!image||!out||stack<PAGE||stack>=USER_TOP)return -1;
    if(size<sizeof(koronos_elf64_ehdr))return -2;
    const auto *h=static_cast<const koronos_elf64_ehdr*>(image);
    if(!koronos_elf64_valid(h)||h->e_type!=KORONOS_ET_EXEC||h->e_version!=1||
       h->e_ehsize!=sizeof(koronos_elf64_ehdr)||h->e_machine!=machine||
       h->e_phentsize!=sizeof(koronos_elf64_phdr)||h->e_phnum==0||(h->e_phoff&7u)!=0)return -2;
    uint64_t phbytes=(uint64_t)h->e_phnum*sizeof(koronos_elf64_phdr);
    if(!in(h->e_phoff,phbytes,size))return -2;
    const auto *ph=reinterpret_cast<const koronos_elf64_phdr*>(static_cast<const uint8_t*>(image)+h->e_phoff);
    chimera_process_image p{};p.entry=h->e_entry;p.user_stack_top=down(stack);
    uint32_t n=0;uint64_t low=UINT64_MAX,high=0;bool entry_executable=false;
    for(uint16_t i=0;i<h->e_phnum;++i){
        const auto &s=ph[i];if(s.p_type!=PT_LOAD)continue;
        if(s.p_memsz<s.p_filesz||!in(s.p_offset,s.p_filesz,size)||(s.p_flags&~7u)!=0)return -3;
        uint64_t end=0;
        if(s.p_memsz==0||!add_ok(s.p_vaddr,s.p_memsz,&end)||s.p_vaddr<PAGE||
           s.p_vaddr>=USER_TOP||end>USER_TOP||s.p_vaddr>=stack||end>stack)return -4;
        if(s.p_align>1&&((s.p_align&(s.p_align-1))!=0))return -5;
        if(s.p_align>1&&(s.p_vaddr%s.p_align)!=(s.p_offset%s.p_align))return -5;
        if(n>=MAX_SEGMENTS||(s.p_flags&(PF_W|PF_X))==(PF_W|PF_X))return -6;
        const uint64_t seglow=down(s.p_vaddr);uint64_t seghigh=0;
        if(!up(end,&seghigh))return -8;
        for(uint32_t j=0;j<n;++j){
            const auto &old=p.segments[j];uint64_t oldend=0;
            if(!add_ok(old.virtual_address,old.memory_size,&oldend)||!up(oldend,&oldend))return -8;
            if(seglow<oldend&&old.virtual_address<seghigh)return -6;
        }
        auto &d=p.segments[n++];d.file_offset=s.p_offset;d.virtual_address=seglow;
        d.file_size=s.p_filesz;
        if(!add_ok(s.p_memsz,s.p_vaddr-seglow,&d.memory_size))return -8;
        d.flags=s.p_flags;d.align=s.p_align?s.p_align:PAGE;d.page_offset=s.p_vaddr-seglow;
        if(seglow<low)low=seglow;if(seghigh>high)high=seghigh;
        if((s.p_flags&PF_X)&&p.entry>=s.p_vaddr&&p.entry<end)entry_executable=true;
    }
    if(!n||!entry_executable)return -9;
    p.segment_count=n;p.image_low=low;p.image_high=high;
    for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;++i)if(!slots[i].used){
        p.pid=next_pid++;if(!next_pid)next_pid=1;p.state=CHIMERA_PROCESS_ADMITTED;
        chimera_nbit_process_context mode{};
        if(chimera_nbit_process_init(&mode,p.pid,64u,0u)!=0)return -11;
        slots[i].image=p;slots[i].used=true;++count;*out=p;return (int)p.pid;
    }
    return -10;
}
extern "C" int chimera_process_get(uint32_t pid,chimera_process_image *out) {
    if(!out||!pid)return -1;int i=find_slot(pid);
    if(i<0)return -2;*out=slots[(uint32_t)i].image;return 0;
}
extern "C" int chimera_process_set_execution_mode(uint32_t pid,uint32_t bits,uint32_t target) {
    int i=find_slot(pid);if(i<0)return -1;
    const auto state=slots[(uint32_t)i].image.state;
    if(state==CHIMERA_PROCESS_EXITED||state==CHIMERA_PROCESS_FAULTED)return -2;
    chimera_nbit_process_context mode{};
    return chimera_nbit_process_init(&mode,pid,bits,target);
}
extern "C" int chimera_process_set_state(uint32_t pid,chimera_process_state state) {
    if(!pid||state<CHIMERA_PROCESS_ADMITTED||state>CHIMERA_PROCESS_FAULTED)return -1;
    int i=find_slot(pid);if(i<0)return -2;
    slots[(uint32_t)i].image.state=state;
    if(state==CHIMERA_PROCESS_EXITED||state==CHIMERA_PROCESS_FAULTED)retire_mode(pid);
    return 0;
}
extern "C" uint32_t chimera_process_count(void){return count;}
extern "C" int chimera_process_discard_admitted(uint32_t pid) {
    if(!pid)return -1;int i=find_slot(pid);if(i<0)return -3;
    if(slots[(uint32_t)i].image.state!=CHIMERA_PROCESS_ADMITTED)return -2;
    retire_mode(pid);slots[(uint32_t)i]={};if(count)--count;return 0;
}
