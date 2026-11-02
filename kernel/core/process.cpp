#include "../include/chimera/process.h"
#include "chimera/x86_64_trap_frame.h"
#if defined(KORONOS_FREESTANDING)
#include "chimera/frame_allocator.h"
#include "chimera/physmap.h"
#include "chimera/address_space.h"
#endif

namespace {
constexpr uint32_t MAX_SEGMENTS = 16;
constexpr uint64_t PAGE = 4096;
constexpr uint32_t PT_LOAD = 1, PF_W = 2, PF_X = 1;
#if defined(KORONOS_FREESTANDING)
constexpr uint32_t PROCESS_KERNEL_STACK_PAGES = 4;
#endif

static void copy_bytes(void *destination, const void *source, uint64_t length) {
    auto *dst = static_cast<uint8_t *>(destination);
    const auto *src = static_cast<const uint8_t *>(source);
    for (uint64_t i = 0; i < length; ++i) dst[i] = src[i];
}
static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return false;
    *out = a + b;
    return true;
}
static uint64_t down(uint64_t x) { return x & ~(PAGE - 1); }
static bool up(uint64_t x, uint64_t *out) {
    if (x > UINT64_MAX - (PAGE - 1)) return false;
    *out = (x + PAGE - 1) & ~(PAGE - 1);
    return true;
}
static bool in(uint64_t offset, uint64_t length, uint64_t size) {
    uint64_t end = 0;
    return add_ok(offset, length, &end) && end <= size;
}

struct Slot {
    chimera_process_image image{};
    chimera_loaded_elf loaded{};
    chimera_elf_load_ops load_ops{};
    void *load_context = nullptr;
    uint64_t kernel_stack_physical = 0;
    uint32_t kernel_stack_pages = 0;
    uint64_t kernel_stack_top = 0;
    uint64_t user_stack_size = 0;
    uint64_t initial_trap_frame_rsp = 0;
    uint64_t saved_kernel_rsp = 0;
    bool used = false;
    bool loaded_ok = false;
    bool execution_context_ready = false;
};
Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1, count = 0;

static bool pid_in_use(uint32_t pid) {
    if (!pid) return true;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) return true;
    return false;
}
/* Never wrap PID allocation onto an existing live process record. */
static uint32_t allocate_pid() {
    for (uint32_t attempt = 0; attempt < CHIMERA_PROCESS_MAX + 1u; ++attempt) {
        if (!next_pid || next_pid > 0x7fffffffu) next_pid = 1;
        const uint32_t candidate = next_pid++;
        if (candidate && !pid_in_use(candidate)) return candidate;
    }
    return 0;
}
static Slot *find_slot(uint32_t pid) {
    if (!pid) return nullptr;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) return &slots[i];
    return nullptr;
}
#if defined(KORONOS_FREESTANDING)
static bool allocate_kernel_stack(Slot *slot) {
    if (!slot || !koronos_physmap_ready()) return false;
    const uint64_t physical = koronos_frame_alloc_contiguous(PROCESS_KERNEL_STACK_PAGES);
    if (!physical) return false;
    const uint64_t bytes = (uint64_t)PROCESS_KERNEL_STACK_PAGES * KORONOS_FRAME_SIZE;
    auto *base = static_cast<uint8_t *>(koronos_phys_to_virt(physical, bytes));
    if (!base) {
        (void)koronos_frame_free_contiguous(physical, PROCESS_KERNEL_STACK_PAGES);
        return false;
    }
    for (uint64_t i = 0; i < bytes; ++i) base[i] = 0;
    slot->kernel_stack_physical = physical;
    slot->kernel_stack_pages = PROCESS_KERNEL_STACK_PAGES;
    slot->kernel_stack_top =
        (reinterpret_cast<uint64_t>(base) + bytes) & ~static_cast<uint64_t>(0xFu);
    return slot->kernel_stack_top != 0;
}
static void release_kernel_stack(Slot *slot) {
    if (!slot) return;
    if (slot->kernel_stack_physical && slot->kernel_stack_pages)
        (void)koronos_frame_free_contiguous(slot->kernel_stack_physical,
                                            slot->kernel_stack_pages);
    slot->kernel_stack_physical = 0;
    slot->kernel_stack_pages = 0;
    slot->kernel_stack_top = 0;
}
#else
static bool allocate_kernel_stack(Slot *) { return true; }
static void release_kernel_stack(Slot *) {}
#endif
static void destroy_loaded(Slot *slot) {
    if (!slot || !slot->loaded_ok) return;
    if (slot->load_ops.destroy_address_space)
        slot->load_ops.destroy_address_space(slot->load_context,
                                             slot->loaded.address_space);
    slot->loaded = {};
    slot->load_ops = {};
    slot->load_context = nullptr;
    slot->loaded_ok = false;
    slot->saved_kernel_rsp = 0;
    slot->initial_trap_frame_rsp = 0;
    slot->user_stack_size = 0;
}
}

extern "C" int chimera_process_init(void) {
    /* Initialization is a one-shot boot operation before any process is loaded. */
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) slots[i] = {};
    next_pid = 1;
    count = 0;
    return 0;
}

extern "C" int chimera_process_admit_elf(const void *image, uint64_t size,
                                          uint16_t machine, uint64_t stack,
                                          chimera_process_image *out) {
    if (!image || !out || stack < PAGE) return -1;
    if (!koronos_elf64_validate(image, size, machine)) return -2;

    koronos_elf64_ehdr h{};
    copy_bytes(&h, image, sizeof(h));
    if (h.e_type != KORONOS_ET_EXEC || h.e_phnum == 0 ||
        h.e_phnum > 4096u) return -2;

    const auto *bytes = static_cast<const uint8_t *>(image);
    chimera_process_image p{};
    p.entry = h.e_entry;
    p.user_stack_top = down(stack);
    uint32_t n = 0;
    uint64_t low = UINT64_MAX, high = 0;
    bool entry_executable = false;

    for (uint16_t i = 0; i < h.e_phnum; ++i) {
        koronos_elf64_phdr s{};
        const uint64_t offset = h.e_phoff +
            static_cast<uint64_t>(i) * sizeof(koronos_elf64_phdr);
        copy_bytes(&s, bytes + offset, sizeof(s));
        if (s.p_type != PT_LOAD) continue;
        if (s.p_memsz < s.p_filesz || !in(s.p_offset, s.p_filesz, size))
            return -3;

        uint64_t end = 0;
        if (!add_ok(s.p_vaddr, s.p_memsz, &end) || s.p_memsz == 0 ||
            s.p_vaddr < 0x0000000100000000ull ||
            s.p_vaddr >= 0x0000800000000000ull ||
            end > stack || end > 0x0000800000000000ull) return -4;
        if (s.p_align > 1 &&
            ((s.p_align & (s.p_align - 1)) != 0 ||
             (s.p_vaddr % s.p_align) != (s.p_offset % s.p_align))) return -5;
        if (n >= MAX_SEGMENTS) return -6;
        if ((s.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -7;

        auto &d = p.segments[n++];
        d.file_offset = s.p_offset;
        d.virtual_address = down(s.p_vaddr);
        d.file_size = s.p_filesz;
        d.memory_size = end - d.virtual_address;
        d.flags = s.p_flags;
        d.align = s.p_align ? s.p_align : PAGE;

        if (d.virtual_address < low) low = d.virtual_address;
        uint64_t aligned_end = 0;
        if (!up(end, &aligned_end)) return -8;
        for (uint32_t j = 0; j + 1u < n; ++j) {
            uint64_t prior_end = 0;
            if (!add_ok(p.segments[j].virtual_address,
                        p.segments[j].memory_size, &prior_end) ||
                !up(prior_end, &prior_end)) return -8;
            if (d.virtual_address < prior_end &&
                p.segments[j].virtual_address < aligned_end) return -11;
        }
        if (aligned_end > high) high = aligned_end;
        if ((s.p_flags & PF_X) && h.e_entry >= s.p_vaddr &&
            h.e_entry < end) entry_executable = true;
    }

    if (!n || p.entry < low || p.entry >= high || p.entry >= stack ||
        !entry_executable) return -9;
    p.segment_count = n;
    p.image_low = low;
    p.image_high = high;

    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used) {
            p.pid = allocate_pid();
            if (!p.pid) return -10;
            p.state = CHIMERA_PROCESS_ADMITTED;
            slots[i] = {};
            slots[i].image = p;
            slots[i].used = true;
            ++count;
            *out = p;
            return static_cast<int>(p.pid);
        }
    }
    return -10;
}

extern "C" int chimera_process_load_elf(uint32_t pid, const void *image,
                                         uint64_t image_size, uint16_t machine,
                                         uint64_t stack_top, uint64_t stack_size,
                                         const chimera_elf_load_ops *ops,
                                         void *context) {
    Slot *slot = find_slot(pid);
    if (!slot || !image || !ops || slot->loaded_ok ||
        slot->image.state != CHIMERA_PROCESS_ADMITTED) return -1;
    chimera_loaded_elf loaded{};
    const int rc = chimera_elf_load_user_image(image, image_size, machine,
                                               stack_top, stack_size, ops,
                                               context, &loaded);
    if (rc != 0) return rc;
    slot->loaded = loaded;
    slot->user_stack_size = stack_size;
    slot->load_ops = *ops;
    slot->load_context = context;
    slot->loaded_ok = true;
    if (!allocate_kernel_stack(slot)) {
        destroy_loaded(slot);
        return -20;
    }
#if defined(KORONOS_FREESTANDING)
    slot->loaded.address_space = loaded.address_space;
    const uint64_t kernel_stack_bytes =
        (uint64_t)slot->kernel_stack_pages * KORONOS_FRAME_SIZE;
    const uint64_t root = koronos_address_space_root(loaded.address_space);
    if (!root || koronos_address_space_validate_kernel_range(
            root, slot->kernel_stack_physical, kernel_stack_bytes, 1u) != 0) {
        release_kernel_stack(slot);
        destroy_loaded(slot);
        return -21;
    }
#endif
    /* Deliberately remain ADMITTED: no validated CPL3 frame/iretq entry has
       been connected, so a mapped ELF is not yet a runnable process. */
    return 0;
}

extern "C" int chimera_process_prepare_initial_context(uint32_t pid) {
    Slot *slot = find_slot(pid);
    if (!slot || !slot->loaded_ok ||
        slot->image.state != CHIMERA_PROCESS_ADMITTED) return -1;
    if (slot->initial_trap_frame_rsp) return -2;
#if !defined(KORONOS_FREESTANDING)
    return -3;
#else
    if (!slot->kernel_stack_top || !slot->kernel_stack_pages ||
        !slot->user_stack_size || !slot->loaded.address_space) return -4;
    if (slot->loaded.user_stack_top < slot->user_stack_size) return -5;
    const uint64_t root = koronos_address_space_root(slot->loaded.address_space);
    const uint64_t stack_base = slot->loaded.user_stack_top - slot->user_stack_size;
    if (!root ||
        koronos_address_space_validate_user_executable_range(root, slot->loaded.entry, 1u) != 0 ||
        koronos_address_space_validate_user_range(root, stack_base, slot->user_stack_size, 1u) != 0)
        return -6;
    const uint64_t kernel_bytes = (uint64_t)slot->kernel_stack_pages * KORONOS_FRAME_SIZE;
    if (koronos_address_space_validate_kernel_range(root, slot->kernel_stack_physical, kernel_bytes, 1u) != 0)
        return -7;
    auto *kernel_base = static_cast<uint8_t *>(koronos_phys_to_virt(slot->kernel_stack_physical, kernel_bytes));
    if (!kernel_base) return -8;
    const uint64_t stack_top = slot->kernel_stack_top;
    const uint64_t base_address = reinterpret_cast<uint64_t>(kernel_base);
    if ((stack_top & 0xFu) != 0 || stack_top < base_address ||
        stack_top - base_address < sizeof(chimera_x86_64_trap_frame)) return -9;
    const uint64_t frame_address = (stack_top - sizeof(chimera_x86_64_trap_frame)) & ~0xFull;
    auto *frame = reinterpret_cast<chimera_x86_64_trap_frame *>(frame_address);
    *frame = {};
    frame->rip = slot->loaded.entry;
    frame->cs = CHIMERA_X86_64_USER_CODE_SELECTOR;
    frame->rflags = CHIMERA_X86_64_RFLAGS_FIXED | CHIMERA_X86_64_RFLAGS_IF;
    frame->user_rsp = slot->loaded.user_stack_top;
    frame->user_ss = CHIMERA_X86_64_USER_DATA_SELECTOR;
    if (!chimera_x86_64_trap_frame_is_user(frame) ||
        frame_address < base_address || frame_address > stack_top ||
        sizeof(*frame) > stack_top - frame_address ||
        frame_address - base_address > kernel_bytes ||
        sizeof(*frame) > kernel_bytes - (frame_address - base_address)) return -10;
    slot->initial_trap_frame_rsp = frame_address;
    /* Not the scheduler's saved context: that ABI remains intentionally unset. */
    return 0;
#endif
}

extern "C" int chimera_process_get_runtime(uint32_t pid,
                                            chimera_process_runtime *out) {
    if (!out) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -2;
    chimera_process_runtime result{};
    result.abi = CHIMERA_PROCESS_RUNTIME_ABI;
    result.loaded = slot->loaded_ok ? 1u : 0u;
    result.execution_context_ready = slot->execution_context_ready ? 1u : 0u;
    if (slot->loaded_ok) {
        result.address_space = slot->loaded.address_space;
        result.entry = slot->loaded.entry;
        result.user_stack_top = slot->loaded.user_stack_top;
#if defined(KORONOS_FREESTANDING)
        result.address_space_root =
            koronos_address_space_root(slot->loaded.address_space);
        result.kernel_stack_top = slot->kernel_stack_top;
#endif
        result.saved_kernel_rsp = slot->saved_kernel_rsp;
    }
    *out = result;
    return 0;
}

extern "C" int chimera_process_release(uint32_t pid) {
    Slot *slot = find_slot(pid);
    if (!slot) return -1;
    if (slot->image.state != CHIMERA_PROCESS_ADMITTED &&
        slot->image.state != CHIMERA_PROCESS_EXITED &&
        slot->image.state != CHIMERA_PROCESS_FAULTED) return -2;
    destroy_loaded(slot);
    release_kernel_stack(slot);
    *slot = {};
    if (count) --count;
    return 0;
}

extern "C" int chimera_process_get(uint32_t pid, chimera_process_image *out) {
    if (!out || !pid) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -2;
    *out = slot->image;
    return 0;
}

extern "C" int chimera_process_set_state(uint32_t pid,
                                          chimera_process_state state) {
    if (!pid || state < CHIMERA_PROCESS_ADMITTED ||
        state > CHIMERA_PROCESS_FAULTED) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -2;
    /* Never expose a mapped-but-unentered image as runnable. The future
       trap-frame/iret integration must set this internal bit only after it
       has built and validated the complete execution context. */
    if ((state == CHIMERA_PROCESS_READY || state == CHIMERA_PROCESS_RUNNING ||
         state == CHIMERA_PROCESS_BLOCKED) &&
        (!slot->loaded_ok || !slot->execution_context_ready)) return -3;
    if ((state == CHIMERA_PROCESS_EXITED || state == CHIMERA_PROCESS_FAULTED) &&
        slot->image.state != CHIMERA_PROCESS_ADMITTED)
        return -4; // READY/BLOCKED/RUNNING require a scheduler-owned detach/reap path
    slot->image.state = state;
    return 0;
}

extern "C" uint32_t chimera_process_count(void) { return count; }
