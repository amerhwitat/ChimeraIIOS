#include "../include/chimera/process.h"
#if defined(KORONOS_FREESTANDING)
#include "chimera/address_space.h"
#include "chimera/process_stack.h"
#endif

namespace {
constexpr uint32_t MAX_SEGMENTS = 16;

static void copy_bytes(void *destination, const void *source, uint64_t length) {
    auto *dst = static_cast<uint8_t *>(destination);
    const auto *src = static_cast<const uint8_t *>(source);
    for (uint64_t i = 0; i < length; ++i) dst[i] = src[i];
}
constexpr uint64_t PAGE = 4096;
constexpr uint32_t PT_LOAD = 1, PF_W = 2, PF_X = 1;

struct Slot {
    chimera_process_image image{};
    chimera_loaded_elf loaded{};
    chimera_elf_load_ops load_ops{};
    void *load_context = nullptr;
    koronos_kernel_stack kernel_stack{};
    uint64_t saved_kernel_rsp = 0;
    bool has_kernel_stack = false;
    bool loaded_ok = false;
    bool execution_context_ready = false;
    bool used = false;
};

Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1, count = 0;

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
    slot->execution_context_ready = false;
}
}

extern "C" int chimera_process_init(void) {
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
        // Include the leading page offset without recomputing an unchecked sum.
        d.memory_size = end - d.virtual_address;
        d.flags = s.p_flags;
        d.align = s.p_align ? s.p_align : PAGE;

        if (d.virtual_address < low) low = d.virtual_address;
        uint64_t aligned_end = 0;
        if (!up(end, &aligned_end)) return -8;
        /* The current mapper has no safe permission-merging policy for
         * page-overlapping PT_LOAD segments; reject them before loading. */
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
    slot->load_ops = *ops;
    slot->load_context = context;
    slot->loaded_ok = true;
#if defined(KORONOS_FREESTANDING)
    if (chimera_process_create_kernel_stack(pid) != 0) {
        destroy_loaded(slot);
        return -20;
    }
#endif
    /* A mapped ELF remains ADMITTED until a validated user trap frame and
       IRETQ entry/return path are connected. */
    return 0;
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
        if (slot->has_kernel_stack) {
            result.kernel_stack_base = slot->kernel_stack.base;
            result.kernel_stack_top = slot->kernel_stack.top;
        }
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
#if defined(KORONOS_FREESTANDING)
    if (slot->has_kernel_stack && chimera_process_release_kernel_stack(pid) != 0)
        return -3; // Keep the process record and address space if stack release fails.
#endif
    destroy_loaded(slot);
    *slot = {};
    if (count) --count;
    return 0;
}

extern "C" int chimera_process_get(uint32_t pid, chimera_process_image *out) {
    if (!out || !pid) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (slots[i].used && slots[i].image.pid == pid) {
            *out = slots[i].image;
            return 0;
        }
    }
    return -2;
}

extern "C" int chimera_process_set_state(uint32_t pid,
                                          chimera_process_state state) {
    if (!pid || state < CHIMERA_PROCESS_ADMITTED ||
        state > CHIMERA_PROCESS_FAULTED) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -2;
    /* A loaded image is not runnable until a complete saved user context is
       validated. Terminal transitions from active states require a scheduler
       detach/reap path, which is not yet implemented. */
    if ((state == CHIMERA_PROCESS_READY || state == CHIMERA_PROCESS_RUNNING ||
         state == CHIMERA_PROCESS_BLOCKED) &&
        (!slot->loaded_ok || !slot->execution_context_ready)) return -3;
    if ((state == CHIMERA_PROCESS_EXITED || state == CHIMERA_PROCESS_FAULTED) &&
        slot->image.state != CHIMERA_PROCESS_ADMITTED) return -4;
    slot->image.state = state;
    return 0;
}

extern "C" int chimera_process_attach_kernel_stack(
    uint32_t pid, const koronos_kernel_stack *stack) {
    if (!pid || !stack || stack->slot >= KORONOS_KERNEL_STACK_SLOT_COUNT ||
        !stack->generation || !stack->base || stack->top <= stack->base ||
        (stack->base & 0xFu) || (stack->top & 0xFu)) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used || slots[i].image.pid != pid) continue;
        if (slots[i].has_kernel_stack) return -2;
        slots[i].kernel_stack = *stack;
        slots[i].has_kernel_stack = true;
        return 0;
    }
    return -3;
}

extern "C" int chimera_process_get_kernel_stack(
    uint32_t pid, koronos_kernel_stack *out_stack) {
    if (!pid || !out_stack) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used || slots[i].image.pid != pid) continue;
        if (!slots[i].has_kernel_stack) return -2;
        *out_stack = slots[i].kernel_stack;
        return 0;
    }
    return -3;
}

extern "C" int chimera_process_detach_kernel_stack(
    uint32_t pid, koronos_kernel_stack *out_stack) {
    if (!pid || !out_stack) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used || slots[i].image.pid != pid) continue;
        if (!slots[i].has_kernel_stack) return -2;
        *out_stack = slots[i].kernel_stack;
        slots[i].kernel_stack = {};
        slots[i].has_kernel_stack = false;
        return 0;
    }
    return -3;
}

extern "C" uint32_t chimera_process_count(void) { return count; }
