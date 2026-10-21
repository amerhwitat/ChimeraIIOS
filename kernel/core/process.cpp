#include "../include/chimera/process.h"

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
            s.p_vaddr >= stack || end > stack) return -4;
        if (s.p_align > 1 &&
            ((s.p_align & (s.p_align - 1)) != 0 ||
             (s.p_vaddr % s.p_align) != (s.p_offset % s.p_align))) return -5;
        if (n >= MAX_SEGMENTS) return -6;
        if ((s.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -7;

        const uint64_t segment_low = down(s.p_vaddr);
        uint64_t aligned_end = 0;
        if (!up(end, &aligned_end)) return -8;
        // Reject page-level PT_LOAD overlap. Mapping overlapping segments with
        // different permissions can silently weaken W^X or make load order
        // determine which bytes/permissions survive.
        for (uint32_t j = 0; j < n; ++j) {
            const auto &prior = p.segments[j];
            uint64_t prior_end = 0;
            if (!add_ok(prior.virtual_address, prior.memory_size, &prior_end))
                return -8;
            uint64_t prior_page_end = 0;
            if (!up(prior_end, &prior_page_end)) return -8;
            if (segment_low < prior_page_end &&
                prior.virtual_address < aligned_end) return -11;
        }

        auto &d = p.segments[n++];
        d.file_offset = s.p_offset;
        d.virtual_address = segment_low;
        d.file_size = s.p_filesz;
        // Include the leading page offset without recomputing an unchecked sum.
        d.memory_size = end - d.virtual_address;
        d.flags = s.p_flags;
        d.align = s.p_align ? s.p_align : PAGE;

        if (d.virtual_address < low) low = d.virtual_address;
        if (aligned_end > high) high = aligned_end;
        if ((s.p_flags & PF_X) && h.e_entry >= s.p_vaddr &&
            h.e_entry < end) entry_executable = true;
    }

    if (!n || !entry_executable) return -9;
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
            return static_cast<int>(p.pid);
        }
    }
    return -10;
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
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (slots[i].used && slots[i].image.pid == pid) {
            slots[i].image.state = state;
            return 0;
        }
    }
    return -2;
}

extern "C" uint32_t chimera_process_count(void) { return count; }
