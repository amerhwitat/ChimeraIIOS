#include "../include/chimera/process.h"
#include "../include/chimera/process_loader.h"
#include "../include/chimera/process_fd.h"
namespace { constexpr uint32_t MAX_SEGMENTS=16; constexpr uint64_t PAGE=4096; constexpr uint32_t PT_LOAD=1,PF_X=1,PF_W=2,PF_R=4; struct Slot { chimera_process_image image{}; bool used=false; }; Slot slots[CHIMERA_PROCESS_MAX]; uint32_t next_pid=1,count=0; static bool add_ok(uint64_t a,uint64_t b,uint64_t*o){if(a>UINT64_MAX-b)return false;*o=a+b;return true;} static uint64_t down(uint64_t x){return x&~(PAGE-1);} static bool up(uint64_t x,uint64_t*o){if(x>UINT64_MAX-(PAGE-1))return false;*o=(x+PAGE-1)&~(PAGE-1);return true;} static bool in(uint64_t o,uint64_t n,uint64_t z){uint64_t e=0;return add_ok(o,n,&e)&&e<=z;} }
extern "C" int chimera_process_init(void){for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)slots[i]={};next_pid=1;count=0;(void)koronos_process_fd_init();return 0;}
extern "C" int chimera_process_admit_elf(const void *image, uint64_t size,
                                                uint16_t machine, uint64_t stack,
                                                chimera_process_image *out) {
    if (!image || !out || size < sizeof(koronos_elf64_ehdr)) return -1;

    koronos_elf64_ehdr h{};
    __builtin_memcpy(&h, image, sizeof(h));
    if (!koronos_elf64_valid(&h) || h.e_ehsize < sizeof(h) ||
        h.e_type != KORONOS_ET_EXEC || h.e_machine != machine ||
        h.e_phentsize != sizeof(koronos_elf64_phdr) || h.e_phnum == 0 ||
        h.e_phnum > MAX_SEGMENTS) return -2;

    const uint64_t phbytes = (uint64_t)h.e_phnum * h.e_phentsize;
    if (!in(h.e_phoff, phbytes, size)) return -3;
    if (stack < CHIMERA_ELF_USER_MIN + PAGE ||
        stack >= CHIMERA_ELF_USER_LIMIT || (stack & (PAGE - 1u))) return -4;

    const auto *bytes = static_cast<const uint8_t *>(image);
    chimera_process_image p{};
    p.entry = h.e_entry;
    p.user_stack_top = stack;
    uint32_t n = 0;
    uint64_t low = UINT64_MAX, high = 0;
    bool entry_x = false;

    for (uint16_t i = 0; i < h.e_phnum; ++i) {
        koronos_elf64_phdr seg{};
        __builtin_memcpy(&seg, bytes + h.e_phoff +
                         (uint64_t)i * h.e_phentsize, sizeof(seg));
        if (seg.p_type != PT_LOAD) continue;

        if (seg.p_memsz == 0 || seg.p_memsz < seg.p_filesz ||
            !in(seg.p_offset, seg.p_filesz, size) ||
            (seg.p_flags & ~(PF_R | PF_W | PF_X)) != 0 ||
            (seg.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -5;

        uint64_t end = 0, map_end = 0;
        if (!add_ok(seg.p_vaddr, seg.p_memsz, &end) ||
            seg.p_vaddr < CHIMERA_ELF_USER_MIN ||
            end > CHIMERA_ELF_USER_LIMIT || seg.p_vaddr >= stack ||
            end > stack || !up(end, &map_end) ||
            map_end > CHIMERA_ELF_USER_LIMIT) return -6;

        if (seg.p_align > 1u &&
            ((seg.p_align & (seg.p_align - 1u)) != 0 ||
             (seg.p_vaddr % seg.p_align) != (seg.p_offset % seg.p_align))) return -7;
        if (n >= MAX_SEGMENTS) return -8;

        const uint64_t base = down(seg.p_vaddr);
        const uint64_t span = map_end - base;
        uint64_t prior_end = 0;
        for (uint32_t j = 0; j < n; ++j) {
            if (!add_ok(p.segments[j].virtual_address,
                        p.segments[j].memory_size, &prior_end)) return -9;
            if (base < prior_end && p.segments[j].virtual_address < map_end)
                return -9;
        }
        if (base < stack && stack - PAGE < map_end) return -9;

        auto &dst = p.segments[n++];
        dst.file_offset = seg.p_offset;
        dst.virtual_address = base;
        dst.file_size = seg.p_filesz;
        dst.memory_size = span;
        dst.flags = seg.p_flags;
        dst.align = seg.p_align ? seg.p_align : PAGE;

        if (base < low) low = base;
        if (map_end > high) high = map_end;
        if ((seg.p_flags & PF_X) && h.e_entry >= seg.p_vaddr &&
            h.e_entry < end) entry_x = true;
    }

    if (!n || !entry_x || p.entry < low || p.entry >= high) return -10;
    p.segment_count = n;
    p.image_low = low;
    p.image_high = high;

    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used) {
            p.pid = next_pid++;
            if (!next_pid) next_pid = 1;
            p.state = CHIMERA_PROCESS_ADMITTED;
            slots[i].image = p;
            slots[i].used = true;
            ++count;
            *out = p;
            return (int)p.pid;
        }
    }
    return -11;
}
extern "C" int chimera_process_get(uint32_t pid,chimera_process_image*out){if(!out||!pid)return -1;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){*out=slots[i].image;return 0;}return -2;}
extern "C" int chimera_process_bind_address_space(uint32_t pid,uint64_t root_physical){
 if(!pid||!root_physical||(root_physical&4095u))return -1;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){
  if(slots[i].image.state!=CHIMERA_PROCESS_ADMITTED||slots[i].image.address_space_root)return -3;
  slots[i].image.address_space_root=root_physical;
  return 0;
 }
 return -2;
}
extern "C" int chimera_process_set_state(uint32_t pid,chimera_process_state state){if(!pid||state<CHIMERA_PROCESS_ADMITTED||state>CHIMERA_PROCESS_FAULTED)return -1;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){slots[i].image.state=state;return 0;}return -2;}
extern "C" int chimera_process_reap(uint32_t pid,chimera_process_image*out){if(!pid)return -1;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){const uint32_t state=slots[i].image.state;if(state!=CHIMERA_PROCESS_EXITED&&state!=CHIMERA_PROCESS_FAULTED)return -3;if(out)*out=slots[i].image;(void)koronos_process_fd_close_all(pid);slots[i]={};if(count)--count;return 0;}return -2;}
extern "C" uint32_t chimera_process_count(void){return count;}
