#include "chimera/elf_loader.h"

namespace {
constexpr uint64_t PAGE = CHIMERA_ELF_PAGE_SIZE;
struct PageRecord {
    uint64_t va = 0;
    uint64_t physical = 0;
    uint8_t *alias = nullptr;
    uint32_t permissions = 0;
    bool mapped = false;
};
static void zero_bytes(void *dst, uint64_t n) {
    auto *p = static_cast<uint8_t *>(dst);
    for (uint64_t i = 0; i < n; ++i) p[i] = 0;
}
static void copy_bytes(void *dst, const void *src, uint64_t n) {
    auto *d = static_cast<uint8_t *>(dst);
    const auto *s = static_cast<const uint8_t *>(src);
    for (uint64_t i = 0; i < n; ++i) d[i] = s[i];
}
static uint64_t page_down(uint64_t n) { return n & ~(PAGE - 1); }
static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return false;
    *out = a + b; return true;
}
static bool page_up(uint64_t n, uint64_t *out) {
    if (n > UINT64_MAX - (PAGE - 1)) return false;
    *out = (n + PAGE - 1) & ~(PAGE - 1); return true;
}
static uint32_t elf_permissions(uint64_t flags) {
    uint32_t out = CHIMERA_ELF_USER;
    if (flags & 2u) out |= CHIMERA_ELF_WRITE;
    if (flags & 1u) out |= CHIMERA_ELF_EXEC;
    return out;
}
static void rollback(const chimera_elf_loader_ops *ops, PageRecord *pages,
                     uint32_t count) {
    while (count) {
        PageRecord &p = pages[--count];
        if (p.mapped) ops->unmap_user_page(ops->context, p.va);
        if (p.physical) ops->free_page(ops->context, p.physical);
        p = {};
    }
}
static int allocate_zero_page(const chimera_elf_loader_ops *ops,
                              PageRecord *record, uint64_t va,
                              uint32_t permissions) {
    uint64_t physical = 0; void *alias = nullptr;
    if (ops->alloc_page(ops->context, &physical, &alias) != 0 ||
        !physical || !alias) {
        if (physical) ops->free_page(ops->context, physical);
        return -1;
    }
    record->va = va; record->physical = physical;
    record->alias = static_cast<uint8_t *>(alias);
    record->permissions = permissions;
    zero_bytes(alias, PAGE);
    return 0;
}
}

extern "C" int chimera_elf_load_and_enter(const void *image, uint64_t image_size,
                                           uint16_t machine, uint64_t stack_top,
                                           const chimera_elf_loader_ops *ops,
                                           uint32_t *pid_out) {
    if (!image || !ops || !pid_out || !ops->alloc_page ||
        !ops->map_user_page || !ops->unmap_user_page || !ops->free_page ||
        !ops->enter_user || stack_top < PAGE * (CHIMERA_ELF_STACK_PAGES + 1u))
        return -1;

    chimera_process_image plan{};
    const int admitted = chimera_process_admit_elf(image, image_size, machine,
                                                    stack_top, &plan);
    if (admitted < 1) return admitted;
    const uint64_t top = plan.user_stack_top;
    const uint64_t stack_bytes = PAGE * CHIMERA_ELF_STACK_PAGES;
    if (top < stack_bytes + PAGE || top - stack_bytes <= plan.image_high) {
        chimera_process_discard_admitted(plan.pid);
        return -2;
    }

    PageRecord pages[CHIMERA_ELF_MAX_MAPPED_PAGES]{};
    uint32_t used = 0;
    const auto *file = static_cast<const uint8_t *>(image);
    for (uint32_t s = 0; s < plan.segment_count; ++s) {
        const chimera_elf_load_segment &seg = plan.segments[s];
        uint64_t raw_end = 0, rounded_end = 0;
        if (!add_ok(seg.virtual_address, seg.memory_size, &raw_end) ||
            !page_up(raw_end, &rounded_end) || seg.file_size > seg.memory_size ||
            seg.page_offset >= PAGE || used >= CHIMERA_ELF_MAX_MAPPED_PAGES) {
            rollback(ops, pages, used);
            chimera_process_discard_admitted(plan.pid);
            return -3;
        }
        const uint64_t first = seg.virtual_address;
        for (uint64_t va = first; va < rounded_end; va += PAGE) {
            if (used >= CHIMERA_ELF_MAX_MAPPED_PAGES) {
                rollback(ops, pages, used);
                chimera_process_discard_admitted(plan.pid);
                return -4;
            }
            PageRecord &p = pages[used];
            if (allocate_zero_page(ops, &p, va, elf_permissions(seg.flags)) != 0) {
                rollback(ops, pages, used);
                chimera_process_discard_admitted(plan.pid);
                return -5;
            }
            ++used;
            const uint64_t page_segment_start = va >= first ? va - first : 0;
            const uint64_t page_file_start = page_segment_start >= seg.page_offset
                ? page_segment_start - seg.page_offset : 0;
            const uint64_t dest_start = page_segment_start < seg.page_offset
                ? seg.page_offset - page_segment_start : 0;
            if (page_file_start < seg.file_size) {
                uint64_t bytes = seg.file_size - page_file_start;
                if (bytes > PAGE - dest_start) bytes = PAGE - dest_start;
                uint64_t src_off = 0;
                if (!add_ok(seg.file_offset, page_file_start, &src_off) ||
                    src_off > image_size || bytes > image_size - src_off) {
                    rollback(ops, pages, used);
                    chimera_process_discard_admitted(plan.pid);
                    return -6;
                }
                copy_bytes(p.alias + dest_start, file + src_off, bytes);
            }
        }
    }

    /* The guard page at top-stack_bytes-PAGE is deliberately left unmapped. */
    for (uint32_t i = 0; i < CHIMERA_ELF_STACK_PAGES; ++i) {
        if (used >= CHIMERA_ELF_MAX_MAPPED_PAGES) {
            rollback(ops, pages, used);
            chimera_process_discard_admitted(plan.pid);
            return -7;
        }
        const uint64_t va = top - PAGE * (i + 1u);
        PageRecord &p = pages[used];
        if (allocate_zero_page(ops, &p, va, CHIMERA_ELF_USER | CHIMERA_ELF_WRITE) != 0) {
            rollback(ops, pages, used);
            chimera_process_discard_admitted(plan.pid);
            return -8;
        }
        ++used;
    }

    /* Contents are populated through kernel aliases before user PTEs exist.
       The backend must implement NX and reject writable+executable mappings. */
    for (uint32_t i = 0; i < used; ++i) {
        PageRecord &p = pages[i];
        if ((p.permissions & (CHIMERA_ELF_WRITE | CHIMERA_ELF_EXEC)) ==
            (CHIMERA_ELF_WRITE | CHIMERA_ELF_EXEC) ||
            ops->map_user_page(ops->context, p.va, p.physical, p.permissions) != 0) {
            rollback(ops, pages, used);
            chimera_process_discard_admitted(plan.pid);
            return -9;
        }
        p.mapped = true;
    }

    if (chimera_process_set_state(plan.pid, CHIMERA_PROCESS_READY) != 0) {
        rollback(ops, pages, used);
        chimera_process_discard_admitted(plan.pid);
        return -10;
    }
    *pid_out = plan.pid;
    const int handoff = ops->enter_user(ops->context, plan.entry, top, plan.pid);
    /* A real ring-3 transfer cannot return here. A returned callback means
       handoff failed; tear down mappings instead of leaving a half-live task. */
    rollback(ops, pages, used);
    chimera_process_set_state(plan.pid, CHIMERA_PROCESS_ADMITTED);
    chimera_process_discard_admitted(plan.pid);
    return handoff == 0 ? -11 : -12;
}
