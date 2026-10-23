#include <stdint.h>
#include <stddef.h>
#include "chimera/address_space.h"
#include "chimera/frame_allocator.h"
#include "chimera/swap.h"
#include "chimera/koronos_abi.h"
extern "C" uint8_t koronos_bootstrap_pml4[];
namespace {
constexpr uint64_t PAGE_SIZE = 4096ull;
constexpr uint64_t PAGE_MASK = PAGE_SIZE - 1ull;
constexpr uint64_t ENTRY_ADDRESS_MASK = 0x000FFFFFFFFFF000ull;
constexpr uint64_t ENTRY_PRESENT = 1ull;
constexpr uint64_t ENTRY_WRITE = 2ull;
constexpr uint64_t ENTRY_USER = 4ull;
constexpr uint64_t ENTRY_LARGE = 0x80ull;
constexpr uint64_t ENTRY_NX = 1ull << 63;
constexpr uint64_t ENTRY_ACCESSED = 1ull << 5;
constexpr uint64_t ENTRY_DIRTY = 1ull << 6;
constexpr uint64_t ENTRY_SWAPPED = 1ull << 9;
constexpr uint64_t VM_EVICTION_SCAN_LIMIT = 128ull;
constexpr uint32_t VM_EVICTION_RETRY_LIMIT = 128u;
constexpr uint32_t MAX_ADDRESS_SPACES = 8u;
constexpr uint32_t MAX_TABLE_FRAMES = 4096u;
constexpr uint32_t MAX_MAPPED_BLOCKS = CHIMERA_ELF_LOADER_MAX_SEGMENTS + 1u;
constexpr uint64_t MAX_USER_PAGES = 131072ull; // 512 MiB per address space.
constexpr uint64_t SPACE_MAGIC = 0x43484D4153504143ull; // "CHMASPAC"



enum PageState : uint8_t { PAGE_NONRESIDENT = 0, PAGE_RESIDENT = 1, PAGE_SWAPPED = 2, PAGE_EVICTING = 3, PAGE_LOADING = 4 };
constexpr uint8_t PAGE_META_DIRTY = 0x40u;
constexpr uint8_t PAGE_META_REFERENCED = 0x80u;
struct PageMeta {
    uint64_t physical;
    uint64_t owner_generation;
    uint16_t pins;
    uint8_t state;
    uint8_t flags;
    uint32_t swap_slot;
};
static_assert(sizeof(PageMeta) == 24, "per-page metadata must retain frame ownership, generation, and state");
struct FrameBlock {
    uint64_t physical;
    uint64_t metadata_physical;
    uint64_t virtual_base;
    uint32_t pages;
    uint32_t metadata_pages;
    uint32_t elf_flags;
};
struct AddressSpace {
    uint64_t magic;
    uint64_t generation;
    uint64_t root_physical;
    uint64_t table_frames[MAX_TABLE_FRAMES];
    FrameBlock mapped[MAX_MAPPED_BLOCKS];
    koronos_vma_descriptor vmas[KORONOS_VMA_MAX];
    uint32_t vma_count;
    uint32_t table_count;
    uint32_t mapped_count;
    uint64_t user_pages;
    uint64_t eviction_cursor;
    uint8_t active;
};
static AddressSpace spaces[MAX_ADDRESS_SPACES]{};
static volatile uint32_t backend_ready = 0;
static volatile uint32_t backend_lock = 0;
static uint64_t created_spaces = 0;
static uint64_t next_space_generation = 1;
static koronos_tlb_shootdown_fn tlb_shootdown = nullptr;
static void *tlb_context = nullptr;

static void lock_backend() {
    while (__sync_lock_test_and_set(&backend_lock, 1u)) {}
}
static void unlock_backend() { __sync_lock_release(&backend_lock); }

static void zero_bytes(void *ptr, size_t n) {
    uint8_t *p = static_cast<uint8_t *>(ptr);
    for (size_t i = 0; i < n; ++i) p[i] = 0;
}
static void copy_bytes(void *dst, const void *src, size_t n) {
    uint8_t *d = static_cast<uint8_t *>(dst);
    const uint8_t *s = static_cast<const uint8_t *>(src);
    for (size_t i = 0; i < n; ++i) d[i] = s[i];
}
static uint64_t *table_ptr(uint64_t physical) {
    if (!physical || physical >= KORONOS_FRAME_PHYS_LIMIT || (physical & PAGE_MASK)) return nullptr;
    return reinterpret_cast<uint64_t *>(static_cast<uintptr_t>(physical));
}
static bool track_table(AddressSpace *space, uint64_t physical) {
    if (!space || !physical || space->table_count >= MAX_TABLE_FRAMES) return false;
    space->table_frames[space->table_count++] = physical;
    return true;
}
static uint64_t new_table(AddressSpace *space) {
    uint64_t physical = koronos_vm_frame_alloc();
    if (!physical) return 0;
    if (!track_table(space, physical)) {
        (void)koronos_vm_frame_release(physical);
        return 0;
    }
    zero_bytes(reinterpret_cast<void *>(static_cast<uintptr_t>(physical)), PAGE_SIZE);
    return physical;
}
static bool space_valid(const AddressSpace *space) {
    return space && space->magic == SPACE_MAGIC && space->active && space->root_physical;
}
static uint64_t current_cr3_root() {
#if defined(__x86_64__)
    uint64_t root = 0;
    __asm__ volatile("mov %%cr3, %0" : "=r"(root));
    return root & ENTRY_ADDRESS_MASK;
#else
    return 0;
#endif
}
static void destroy_locked(AddressSpace *space) {
    if (!space || space->magic != SPACE_MAGIC) return;
    // Never reclaim page tables while this CPU is still executing on the root.
    // AP scheduling is not enabled in the current kernel; future SMP activation
    // must additionally track per-CPU root ownership before using this path.
    if (current_cr3_root() == space->root_physical) return;
    for (uint32_t i = 0; i < space->mapped_count; ++i) {
        const FrameBlock &b = space->mapped[i];
        if (!b.metadata_physical) continue;
        const auto *meta = reinterpret_cast<const PageMeta *>(
            static_cast<uintptr_t>(b.metadata_physical));
        for (uint32_t p = 0; p < b.pages; ++p) {
            if (meta[p].owner_generation != space->generation ||
                meta[p].pins != 0u || meta[p].state == PAGE_EVICTING ||
                meta[p].state == PAGE_LOADING) return;
            if (meta[p].physical && koronos_vm_frame_refcount(meta[p].physical) == 0u) return;
        }
    }
    for (uint32_t i = 0; i < space->mapped_count; ++i) {
        FrameBlock &b = space->mapped[i];
        auto *meta = b.metadata_physical
            ? reinterpret_cast<PageMeta *>(static_cast<uintptr_t>(b.metadata_physical)) : nullptr;
        if (meta) {
            for (uint32_t p = 0; p < b.pages; ++p) {
                if (meta[p].physical) {
                    if (koronos_vm_frame_release(meta[p].physical) != 0) {
                        space->active = 0; space->magic = 0; space->root_physical = 0;
                        return; // poisoned space: leak remaining ownership, never reuse it
                    }
                    meta[p].physical = 0;
                }
                if (meta[p].state == PAGE_SWAPPED && meta[p].swap_slot != KORONOS_SWAP_SLOT_INVALID) {
                    if (koronos_swap_release(meta[p].swap_slot) != 0) {
                        space->active = 0; space->magic = 0; space->root_physical = 0;
                        return;
                    }
                    meta[p].swap_slot = KORONOS_SWAP_SLOT_INVALID;
                }
            }
        }
        if (b.metadata_physical && b.metadata_pages &&
            koronos_vm_frame_release_contiguous(b.metadata_physical, b.metadata_pages) != 0) {
            space->active = 0; space->magic = 0; space->root_physical = 0;
            return;
        }
    }
    for (uint32_t i = space->table_count; i > 0; --i) {
        if (koronos_vm_frame_release(space->table_frames[i - 1]) != 0) {
            space->active = 0; space->magic = 0; space->root_physical = 0;
            return;
        }
    }
    space->magic = 0;
    space->active = 0;
    space->root_physical = 0;
    space->table_count = 0;
    space->mapped_count = 0;
    space->vma_count = 0;
    space->user_pages = 0;
}
static bool clone_bootstrap_map(AddressSpace *space) {
    const uint64_t bootstrap = reinterpret_cast<uint64_t>(koronos_bootstrap_pml4);
    if (!bootstrap || (bootstrap & PAGE_MASK) || bootstrap >= KORONOS_FRAME_PHYS_LIMIT) return false;
    const uint64_t *src_root = table_ptr(bootstrap);
    if (!src_root || !(src_root[0] & ENTRY_PRESENT)) return false;
    // This bootstrap currently has a low identity map only. Refuse to share an
    // unknown higher-half kernel subtree: a future layout must clone it explicitly.
    for (uint32_t i = 1; i < 512u; ++i) if (src_root[i] & ENTRY_PRESENT) return false;

    const uint64_t root = new_table(space);
    if (!root) return false;
    copy_bytes(table_ptr(root), src_root, PAGE_SIZE);
    space->root_physical = root;

    const uint64_t old_pdpt_phys = src_root[0] & ENTRY_ADDRESS_MASK;
    const uint64_t *old_pdpt = table_ptr(old_pdpt_phys);
    if (!old_pdpt) return false;
    const uint64_t pdpt = new_table(space);
    if (!pdpt) return false;
    copy_bytes(table_ptr(pdpt), old_pdpt, PAGE_SIZE);
    uint64_t *new_root = table_ptr(root);
    uint64_t *new_pdpt = table_ptr(pdpt);
    new_root[0] = pdpt | (src_root[0] & 0xFFFu) | ENTRY_USER;

    // Clone all four 1-GiB bootstrap PDs. The 2-MiB identity leaves remain
    // supervisor-only; user mappings are placed above the 4-GiB identity span.
    for (uint32_t i = 0; i < 4u; ++i) {
        if (!(old_pdpt[i] & ENTRY_PRESENT) || (old_pdpt[i] & ENTRY_LARGE)) return false;
        const uint64_t old_pd_phys = old_pdpt[i] & ENTRY_ADDRESS_MASK;
        const uint64_t *old_pd = table_ptr(old_pd_phys);
        if (!old_pd) return false;
        const uint64_t pd = new_table(space);
        if (!pd) return false;
        copy_bytes(table_ptr(pd), old_pd, PAGE_SIZE);
        new_pdpt[i] = pd | (old_pdpt[i] & 0xFFFu) | ENTRY_USER;
    }
    for (uint32_t i = 4u; i < 512u; ++i) {
        if (old_pdpt[i] & ENTRY_PRESENT) return false;
    }
    return true;
}
static uint64_t *ensure_pte(AddressSpace *space, uint64_t virtual_address) {
    if (!space_valid(space) || virtual_address < KORONOS_USER_VIRTUAL_MIN ||
        virtual_address >= CHIMERA_ELF_USER_LIMIT || (virtual_address & PAGE_MASK)) return nullptr;
    const uint32_t pml4_i = static_cast<uint32_t>((virtual_address >> 39) & 0x1FFu);
    const uint32_t pdpt_i = static_cast<uint32_t>((virtual_address >> 30) & 0x1FFu);
    const uint32_t pd_i = static_cast<uint32_t>((virtual_address >> 21) & 0x1FFu);
    const uint32_t pt_i = static_cast<uint32_t>((virtual_address >> 12) & 0x1FFu);
    uint64_t *root = table_ptr(space->root_physical);
    if (!root) return nullptr;

    uint64_t entry = root[pml4_i];
    if (!(entry & ENTRY_PRESENT)) {
        const uint64_t child = new_table(space);
        if (!child) return nullptr;
        root[pml4_i] = child | ENTRY_PRESENT | ENTRY_WRITE | ENTRY_USER;
        entry = root[pml4_i];
    } else {
        if (entry & ENTRY_LARGE) return nullptr;
        root[pml4_i] |= ENTRY_USER | ENTRY_WRITE;
    }
    uint64_t *pdpt = table_ptr(entry & ENTRY_ADDRESS_MASK);
    if (!pdpt) return nullptr;

    entry = pdpt[pdpt_i];
    if (!(entry & ENTRY_PRESENT)) {
        const uint64_t child = new_table(space);
        if (!child) return nullptr;
        pdpt[pdpt_i] = child | ENTRY_PRESENT | ENTRY_WRITE | ENTRY_USER;
        entry = pdpt[pdpt_i];
    } else {
        if (entry & ENTRY_LARGE) return nullptr;
        pdpt[pdpt_i] |= ENTRY_USER | ENTRY_WRITE;
    }
    uint64_t *pd = table_ptr(entry & ENTRY_ADDRESS_MASK);
    if (!pd) return nullptr;

    entry = pd[pd_i];
    if (!(entry & ENTRY_PRESENT)) {
        const uint64_t child = new_table(space);
        if (!child) return nullptr;
        pd[pd_i] = child | ENTRY_PRESENT | ENTRY_WRITE | ENTRY_USER;
        entry = pd[pd_i];
    } else {
        // User virtual addresses below 4 GiB are rejected, so a present large
        // identity leaf here would be an unexpected overlap and must fail closed.
        if (entry & ENTRY_LARGE) return nullptr;
        pd[pd_i] |= ENTRY_USER | ENTRY_WRITE;
    }
    uint64_t *pt = table_ptr(entry & ENTRY_ADDRESS_MASK);
    return pt ? &pt[pt_i] : nullptr;
}

static uint64_t *find_pte(AddressSpace *space, uint64_t virtual_address) {
    if (!space_valid(space) || virtual_address < KORONOS_USER_VIRTUAL_MIN ||
        virtual_address >= CHIMERA_ELF_USER_LIMIT) return nullptr;
    const uint32_t pml4_i = static_cast<uint32_t>((virtual_address >> 39) & 0x1FFu);
    const uint32_t pdpt_i = static_cast<uint32_t>((virtual_address >> 30) & 0x1FFu);
    const uint32_t pd_i = static_cast<uint32_t>((virtual_address >> 21) & 0x1FFu);
    const uint32_t pt_i = static_cast<uint32_t>((virtual_address >> 12) & 0x1FFu);
    uint64_t *root = table_ptr(space->root_physical);
    if (!root) return nullptr;
    uint64_t entry = root[pml4_i];
    if (!(entry & ENTRY_PRESENT) || (entry & ENTRY_LARGE)) return nullptr;
    uint64_t *pdpt = table_ptr(entry & ENTRY_ADDRESS_MASK);
    if (!pdpt) return nullptr;
    entry = pdpt[pdpt_i];
    if (!(entry & ENTRY_PRESENT) || (entry & ENTRY_LARGE)) return nullptr;
    uint64_t *pd = table_ptr(entry & ENTRY_ADDRESS_MASK);
    if (!pd) return nullptr;
    entry = pd[pd_i];
    if (!(entry & ENTRY_PRESENT) || (entry & ENTRY_LARGE)) return nullptr;
    uint64_t *pt = table_ptr(entry & ENTRY_ADDRESS_MASK);
    return pt ? &pt[pt_i] : nullptr;
}

static bool table_empty(uint64_t physical) {
    uint64_t *table = table_ptr(physical);
    if (!table) return false;
    for (uint32_t i = 0; i < 512u; ++i) if (table[i] != 0u) return false;
    return true;
}

static bool release_tracked_table(AddressSpace *space, uint64_t physical) {
    if (!space || !physical || physical == space->root_physical ||
        koronos_vm_frame_refcount(physical) != 1u) return false;
    uint32_t index = space->table_count;
    for (uint32_t i = 0; i < space->table_count; ++i) {
        if (space->table_frames[i] == physical) { index = i; break; }
    }
    if (index == space->table_count || koronos_vm_frame_release(physical) != 0) return false;
    for (uint32_t i = index + 1u; i < space->table_count; ++i)
        space->table_frames[i - 1u] = space->table_frames[i];
    --space->table_count;
    return true;
}

/* Caller holds backend_lock and has already cleared the leaf PTE and completed
   a synchronous shootdown. Empty user-owned tables are detached, invalidated,
   then reclaimed. Bootstrap identity-map tables remain populated and owned. */
static void prune_empty_user_tables(AddressSpace *space, uint64_t va) {
    if (!space_valid(space) || !tlb_shootdown) return;
    const uint32_t pml4_i = static_cast<uint32_t>((va >> 39) & 0x1FFu);
    const uint32_t pdpt_i = static_cast<uint32_t>((va >> 30) & 0x1FFu);
    const uint32_t pd_i = static_cast<uint32_t>((va >> 21) & 0x1FFu);
    uint64_t *root = table_ptr(space->root_physical);
    if (!root || !(root[pml4_i] & ENTRY_PRESENT) || (root[pml4_i] & ENTRY_LARGE)) return;
    uint64_t *pdpt = table_ptr(root[pml4_i] & ENTRY_ADDRESS_MASK);
    if (!pdpt || !(pdpt[pdpt_i] & ENTRY_PRESENT) || (pdpt[pdpt_i] & ENTRY_LARGE)) return;
    const uint64_t pd_phys = pdpt[pdpt_i] & ENTRY_ADDRESS_MASK;
    uint64_t *pd = table_ptr(pd_phys);
    if (!pd || !(pd[pd_i] & ENTRY_PRESENT) || (pd[pd_i] & ENTRY_LARGE)) return;
    const uint64_t pt_phys = pd[pd_i] & ENTRY_ADDRESS_MASK;
    if (table_empty(pt_phys)) {
        const uint64_t saved = pd[pd_i];
        pd[pd_i] = 0;
        tlb_shootdown(space->root_physical, va, PAGE_SIZE, tlb_context);
        if (!release_tracked_table(space, pt_phys)) {
            pd[pd_i] = saved;
            tlb_shootdown(space->root_physical, va, PAGE_SIZE, tlb_context);
            return;
        }
    }
    if (table_empty(pd_phys)) {
        const uint64_t saved = pdpt[pdpt_i];
        pdpt[pdpt_i] = 0;
        tlb_shootdown(space->root_physical, va, PAGE_SIZE, tlb_context);
        if (!release_tracked_table(space, pd_phys)) {
            pdpt[pdpt_i] = saved;
            tlb_shootdown(space->root_physical, va, PAGE_SIZE, tlb_context);
            return;
        }
    }
    const uint64_t pdpt_phys = root[pml4_i] & ENTRY_ADDRESS_MASK;
    if (table_empty(pdpt_phys)) {
        const uint64_t saved = root[pml4_i];
        root[pml4_i] = 0;
        tlb_shootdown(space->root_physical, va, PAGE_SIZE, tlb_context);
        if (!release_tracked_table(space, pdpt_phys)) {
            root[pml4_i] = saved;
            tlb_shootdown(space->root_physical, va, PAGE_SIZE, tlb_context);
        }
    }
}

static PageMeta *find_page_meta(AddressSpace *space, uint64_t page_va, uint64_t *physical_out);

static FrameBlock *find_block(AddressSpace *space, uint64_t base, uint64_t length) {
    if (!space || !length || (base & PAGE_MASK) || (length & PAGE_MASK)) return nullptr;
    const uint64_t pages = length / PAGE_SIZE;
    if (pages > UINT32_MAX) return nullptr;
    for (uint32_t i = 0; i < space->mapped_count; ++i) {
        FrameBlock *b = &space->mapped[i];
        if (b->virtual_base == base && b->pages == static_cast<uint32_t>(pages)) return b;
    }
    return nullptr;
}

static void *create_address_space(void *) {
    if (!backend_ready) return nullptr;
    lock_backend();
    AddressSpace *space = nullptr;
    for (uint32_t i = 0; i < MAX_ADDRESS_SPACES; ++i) {
        if (!spaces[i].active && spaces[i].magic == 0) { space = &spaces[i]; break; }
    }
    if (!space) { unlock_backend(); return nullptr; }
    zero_bytes(space, sizeof(AddressSpace));
    if (next_space_generation == 0u || next_space_generation == UINT64_MAX) {
        unlock_backend();
        return nullptr; // never reuse a generation after counter exhaustion
    }
    space->magic = SPACE_MAGIC;
    space->generation = next_space_generation++;
    space->active = 1;
    if (!clone_bootstrap_map(space)) {
        destroy_locked(space);
        unlock_backend();
        return nullptr;
    }
    ++created_spaces;
    unlock_backend();
    return space;
}
static int map_pages(void *, void *opaque, uint64_t virtual_base, uint64_t size,
                     uint32_t elf_flags, void **kernel_alias) {
    if (!kernel_alias || !size || (virtual_base & PAGE_MASK) || (size & PAGE_MASK) ||
        virtual_base < KORONOS_USER_VIRTUAL_MIN || virtual_base >= CHIMERA_ELF_USER_LIMIT ||
        size > CHIMERA_ELF_USER_LIMIT - virtual_base) return -1;
    *kernel_alias = nullptr;
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || (elf_flags & ~7u) != 0u ||
        (elf_flags & 2u && elf_flags & 1u)) return -2;
    const uint64_t pages64 = size / PAGE_SIZE;
    if (!pages64 || pages64 > UINT32_MAX || pages64 > MAX_USER_PAGES) return -3;
    lock_backend();
    if (!space_valid(space) || space->mapped_count >= MAX_MAPPED_BLOCKS || space->vma_count >= KORONOS_VMA_MAX ||
        pages64 > MAX_USER_PAGES - space->user_pages) {
        unlock_backend(); return -3;
    }
    const bool root_is_active = current_cr3_root() == space->root_physical;
    if (root_is_active && !tlb_shootdown) {
        unlock_backend(); return -10; // no stale non-present translation may survive publication
    }

    // Prepare every page-table path and reject overlap before acquiring data
    // frames. Intermediate empty tables are owned by this address space and
    // may safely remain until teardown if preparation runs out of frames.
    for (uint64_t i = 0; i < pages64; ++i) {
        uint64_t *pte = ensure_pte(space, virtual_base + i * PAGE_SIZE);
        if (!pte) { unlock_backend(); return -5; }
        if (*pte & ENTRY_PRESENT) { unlock_backend(); return -6; }
    }

    const uint64_t physical = koronos_vm_frame_alloc_contiguous(static_cast<uint32_t>(pages64));
    if (!physical) { unlock_backend(); return -4; }
    const uint64_t metadata_bytes = pages64 * sizeof(PageMeta);
    const uint64_t metadata_pages64 = (metadata_bytes + PAGE_MASK) / PAGE_SIZE;
    if (!metadata_pages64 || metadata_pages64 > UINT32_MAX) {
        (void)koronos_vm_frame_release_contiguous(physical, static_cast<uint32_t>(pages64));
        unlock_backend(); return -8;
    }
    const uint64_t metadata_physical = koronos_vm_frame_alloc_contiguous(
        static_cast<uint32_t>(metadata_pages64));
    if (!metadata_physical) {
        (void)koronos_vm_frame_release_contiguous(physical, static_cast<uint32_t>(pages64));
        unlock_backend(); return -9;
    }
    auto *page_meta = reinterpret_cast<PageMeta *>(static_cast<uintptr_t>(metadata_physical));
    for (uint64_t i = 0; i < pages64; ++i) {
        page_meta[i].physical = physical + i * PAGE_SIZE;
        page_meta[i].owner_generation = space->generation;
        page_meta[i].pins = 0;
        page_meta[i].state = PAGE_RESIDENT;
        page_meta[i].flags = static_cast<uint8_t>(elf_flags | PAGE_META_REFERENCED);
        page_meta[i].swap_slot = KORONOS_SWAP_SLOT_INVALID;
    }
    const uint64_t leaf_flags = ENTRY_PRESENT | ENTRY_USER |
        ((elf_flags & 2u) ? ENTRY_WRITE : 0u) |
        ((elf_flags & 1u) ? 0u : ENTRY_NX);

    // Since the backend lock remains held and every PTE path was prepared
    // above, installation is deterministic. Keep defensive rollback anyway:
    // never publish a partial mapping or leak/reuse a frame still referenced
    // by a PTE if a future page-table backend changes these assumptions.
    uint64_t installed = 0;
    for (; installed < pages64; ++installed) {
        uint64_t *pte = ensure_pte(space, virtual_base + installed * PAGE_SIZE);
        if (!pte || (*pte & ENTRY_PRESENT)) break;
        *pte = (physical + installed * PAGE_SIZE) | leaf_flags;
    }
    if (installed != pages64) {
        for (uint64_t i = 0; i < installed; ++i) {
            uint64_t *pte = ensure_pte(space, virtual_base + i * PAGE_SIZE);
            if (pte) *pte = 0;
        }
        (void)koronos_vm_frame_release_contiguous(physical, static_cast<uint32_t>(pages64));
        (void)koronos_vm_frame_release_contiguous(metadata_physical, static_cast<uint32_t>(metadata_pages64));
        unlock_backend();
        return -7;
    }
    FrameBlock &block = space->mapped[space->mapped_count++];
    block.physical = physical;
    block.metadata_physical = metadata_physical;
    block.virtual_base = virtual_base;
    block.pages = static_cast<uint32_t>(pages64);
    block.metadata_pages = static_cast<uint32_t>(metadata_pages64);
    block.elf_flags = elf_flags;
    if (root_is_active)
        tlb_shootdown(space->root_physical, virtual_base, size, tlb_context);
    koronos_vma_descriptor &vma = space->vmas[space->vma_count++];
    vma.abi = KORONOS_VMA_ABI;
    vma.backing_kind = KORONOS_VMA_ANONYMOUS;
    vma.elf_flags = elf_flags;
    vma.residency = KORONOS_VMA_RESIDENT;
    vma.virtual_base = virtual_base;
    vma.length = size;
    vma.backing_object = 0;
    vma.backing_offset = 0;
    vma.page_count = pages64;
    vma.resident_pages = pages64;
    space->user_pages += pages64;
    *kernel_alias = reinterpret_cast<void *>(static_cast<uintptr_t>(physical));
    unlock_backend();
    return 0;
}
static void destroy_address_space(void *, void *opaque) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    lock_backend();
    if (space_valid(space)) destroy_locked(space);
    unlock_backend();
}
static bool user_page_access(uint64_t root_physical, uint64_t va, bool write_access) {
    uint64_t *root = table_ptr(root_physical & ENTRY_ADDRESS_MASK);
    if (!root) return false;
    uint64_t entry = root[(va >> 39) & 0x1FFu];
    if (!(entry & ENTRY_PRESENT) || !(entry & ENTRY_USER) ||
        (write_access && !(entry & ENTRY_WRITE)) || (entry & ENTRY_LARGE)) return false;
    uint64_t *pdpt = table_ptr(entry & ENTRY_ADDRESS_MASK);
    if (!pdpt) return false;
    entry = pdpt[(va >> 30) & 0x1FFu];
    if (!(entry & ENTRY_PRESENT) || !(entry & ENTRY_USER) ||
        (write_access && !(entry & ENTRY_WRITE))) return false;
    if (entry & ENTRY_LARGE) return true;
    uint64_t *pd = table_ptr(entry & ENTRY_ADDRESS_MASK);
    if (!pd) return false;
    entry = pd[(va >> 21) & 0x1FFu];
    if (!(entry & ENTRY_PRESENT) || !(entry & ENTRY_USER) ||
        (write_access && !(entry & ENTRY_WRITE))) return false;
    if (entry & ENTRY_LARGE) return true;
    uint64_t *pt = table_ptr(entry & ENTRY_ADDRESS_MASK);
    if (!pt) return false;
    entry = pt[(va >> 12) & 0x1FFu];
    return (entry & (ENTRY_PRESENT | ENTRY_USER)) == (ENTRY_PRESENT | ENTRY_USER) &&
           (!write_access || (entry & ENTRY_WRITE));
}

static bool address_space_self_test() {
    const uint64_t before = koronos_frame_free_count();
    const uint64_t reference_probe = koronos_vm_frame_alloc();
    if (!reference_probe) return false;
    bool refs_ok = koronos_vm_frame_refcount(reference_probe) == 1u &&
        koronos_vm_frame_retain(reference_probe) == 0 &&
        koronos_vm_frame_refcount(reference_probe) == 2u &&
        koronos_vm_frame_release(reference_probe) == 0 &&
        koronos_vm_frame_refcount(reference_probe) == 1u &&
        koronos_vm_frame_release(reference_probe) == 0 &&
        koronos_vm_frame_refcount(reference_probe) == 0u;
    if (!refs_ok) { const uint32_t remaining = koronos_vm_frame_refcount(reference_probe); if (remaining) (void)koronos_vm_frame_release_contiguous(reference_probe, 1u); return false; }
    if (koronos_frame_free_count() != before) return false;
    AddressSpace *space = static_cast<AddressSpace *>(create_address_space(nullptr));
    if (!space) return false;
    void *code_alias = nullptr;
    void *stack_alias = nullptr;
    const int code_rc = map_pages(nullptr, space, KORONOS_USER_VIRTUAL_MIN, PAGE_SIZE, 5u, &code_alias);
    const int stack_rc = code_rc == 0
        ? map_pages(nullptr, space, 0x00007FFFFFFFE000ull, PAGE_SIZE, 6u, &stack_alias)
        : -1;
    bool ok = code_rc == 0 && stack_rc == 0 && code_alias && stack_alias;
    if (ok) {
        PageMeta *generation_meta = find_page_meta(space, KORONOS_USER_VIRTUAL_MIN, nullptr);
        const uint64_t saved_generation = generation_meta ? generation_meta->owner_generation : 0u;
        if (generation_meta) generation_meta->owner_generation = saved_generation ^ 1u;
        const bool stale_generation_rejected =
            find_page_meta(space, KORONOS_USER_VIRTUAL_MIN, nullptr) == nullptr;
        if (generation_meta) generation_meta->owner_generation = saved_generation;
        ok = generation_meta != nullptr && saved_generation == space->generation &&
             stale_generation_rejected;
    }
    if (ok) {
        uint64_t queried_physical = 0;
        uint32_t queried_flags = 0;
        const uint64_t free_before_overlap = koronos_frame_free_count();
        const int query_rc = koronos_address_space_query(
            space, KORONOS_USER_VIRTUAL_MIN, &queried_physical, &queried_flags);
        koronos_vma_descriptor queried_vma{};
        const int vma_rc = koronos_address_space_vma_query(
            space, KORONOS_USER_VIRTUAL_MIN, &queried_vma);
        const int vma_backing_rc = koronos_address_space_vma_set_backing(
            space, KORONOS_USER_VIRTUAL_MIN, PAGE_SIZE, KORONOS_VMA_ELF_IMAGE,
            0xC0DEu, 0u);
        koronos_vma_descriptor updated_vma{};
        const int updated_vma_rc = koronos_address_space_vma_query(space, KORONOS_USER_VIRTUAL_MIN, &updated_vma);
        const int overlap_rc = koronos_address_space_map(
            space, KORONOS_USER_VIRTUAL_MIN, PAGE_SIZE, 5u);
        const int pin_rc = koronos_address_space_pin(
            space, KORONOS_USER_VIRTUAL_MIN, 1u, 0u);
        const int unpin_rc = pin_rc == 0 ? koronos_address_space_unpin(
            space, KORONOS_USER_VIRTUAL_MIN, 1u) : -1;
        const int double_unpin_rc = koronos_address_space_unpin(
            space, KORONOS_USER_VIRTUAL_MIN, 1u);
        ok = query_rc == 0 && vma_rc == 0 && vma_backing_rc == 0 && updated_vma_rc == 0 &&
             updated_vma.backing_kind == KORONOS_VMA_ELF_IMAGE && updated_vma.backing_object == 0xC0DEu &&
             queried_vma.abi == KORONOS_VMA_ABI &&
             queried_vma.backing_kind == KORONOS_VMA_ANONYMOUS &&
             queried_vma.virtual_base == KORONOS_USER_VIRTUAL_MIN &&
             queried_vma.page_count == 1u && queried_vma.resident_pages == 1u &&
             queried_physical == reinterpret_cast<uintptr_t>(code_alias) &&
             queried_flags == 5u && overlap_rc != 0 && pin_rc == 0 &&
             unpin_rc == 0 && double_unpin_rc != 0 &&
             koronos_frame_free_count() == free_before_overlap;
        uint64_t *code_pte = ensure_pte(space, KORONOS_USER_VIRTUAL_MIN);
        uint64_t *stack_pte = ensure_pte(space, 0x00007FFFFFFFE000ull);
        uint64_t *root = table_ptr(space->root_physical);
        uint64_t *pdpt = root ? table_ptr(root[0] & ENTRY_ADDRESS_MASK) : nullptr;
        uint64_t *pd = pdpt ? table_ptr(pdpt[0] & ENTRY_ADDRESS_MASK) : nullptr;
        // Existing 2-MiB identity leaves must remain supervisor-only even though
        // their parent entries are user-capable for high user mappings.
        ok = ok && code_pte && stack_pte && root && pdpt && pd &&
             (*code_pte & (ENTRY_PRESENT | ENTRY_USER)) == (ENTRY_PRESENT | ENTRY_USER) &&
             (*code_pte & ENTRY_WRITE) == 0 && (*code_pte & ENTRY_NX) == 0 &&
             (*stack_pte & (ENTRY_PRESENT | ENTRY_USER | ENTRY_WRITE | ENTRY_NX)) ==
                 (ENTRY_PRESENT | ENTRY_USER | ENTRY_WRITE | ENTRY_NX) &&
             (pd[0] & ENTRY_LARGE) != 0 && (pd[0] & ENTRY_USER) == 0 &&
             koronos_address_space_validate_user_range(space->root_physical,
                 KORONOS_USER_VIRTUAL_MIN, 1u, 0u) == 0 &&
             koronos_address_space_validate_user_range(space->root_physical,
                 KORONOS_USER_VIRTUAL_MIN, 1u, 1u) != 0 &&
             koronos_address_space_validate_user_range(space->root_physical,
                 0x00007FFFFFFFE000ull, 1u, 1u) == 0 &&
             koronos_address_space_validate_user_range(space->root_physical,
                 0x00100000ull, 1u, 0u) != 0;
    }
    destroy_address_space(nullptr, space);
    return ok && koronos_frame_free_count() == before;
}
static int set_vma_backing(void *, void *address_space, uint64_t base, uint64_t length,
                             uint32_t kind, uint64_t object, uint64_t offset) {
    return koronos_address_space_vma_set_backing(address_space, base, length, kind, object, offset);
}
static const chimera_elf_load_ops loader_ops = {
    create_address_space, map_pages, destroy_address_space, set_vma_backing
};
}

extern "C" int koronos_address_space_init(void) {
    const koronos_cpu_features *features = koronos_get_cpu_features();
    if (!features || !features->long_mode || !features->nx) {
        backend_ready = 0;
        return -1;
    }
#if defined(__x86_64__)
    uint32_t lo = 0, hi = 0;
    __asm__ volatile("rdmsr" : "=a"(lo), "=d"(hi) : "c"(0xC0000080u));
    lo |= (1u << 11); // EFER.NXE: required before installing NX PTE bits.
    __asm__ volatile("wrmsr" : : "a"(lo), "d"(hi), "c"(0xC0000080u));
    backend_ready = 1;
    return 0;
#else
    backend_ready = 0;
    return -2;
#endif
}
extern "C" int koronos_address_space_ready(void) { return backend_ready ? 1 : 0; }
extern "C" int koronos_address_space_self_test(void) {
    if (!backend_ready) return -1;
    if (!address_space_self_test()) {
        backend_ready = 0;
        return -2;
    }
    return 0;
}
extern "C" const chimera_elf_load_ops *koronos_address_space_loader_ops(void) {
    return backend_ready ? &loader_ops : nullptr;
}
extern "C" uint64_t koronos_address_space_root(const void *opaque) {
    const AddressSpace *space = static_cast<const AddressSpace *>(opaque);
    return space_valid(space) ? space->root_physical : 0;
}
extern "C" int koronos_address_space_validate_user_range(uint64_t root_physical,
                                                        uint64_t address, uint64_t length,
                                                        uint32_t write_access) {
    if (length == 0) return 0;
    if (address < KORONOS_USER_VIRTUAL_MIN || address >= CHIMERA_ELF_USER_LIMIT ||
        length > CHIMERA_ELF_USER_LIMIT - address) return -1;
    const uint64_t end = address + length;
    uint64_t page = address & ~PAGE_MASK;
    while (page < end) {
        if (!user_page_access(root_physical, page, write_access != 0)) return -2;
        if (page > UINT64_MAX - PAGE_SIZE) return -3;
        page += PAGE_SIZE;
    }
    return 0;
}
extern "C" int koronos_address_space_register_tlb_shootdown(
    koronos_tlb_shootdown_fn callback, void *context) {
    if (!callback) return -1;
    lock_backend();
    if (tlb_shootdown && (tlb_shootdown != callback || tlb_context != context)) {
        unlock_backend(); return -2;
    }
    tlb_shootdown = callback;
    tlb_context = context;
    unlock_backend();
    return 0;
}

extern "C" int koronos_address_space_map(void *opaque, uint64_t base, uint64_t length,
                                           uint32_t elf_flags) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space)) return -1;
    void *alias = nullptr;
    return map_pages(nullptr, space, base, length, elf_flags, &alias);
}

extern "C" int koronos_address_space_unmap(void *opaque, uint64_t base, uint64_t length) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || !length || (base & PAGE_MASK) || (length & PAGE_MASK) ||
        base < KORONOS_USER_VIRTUAL_MIN || base >= CHIMERA_ELF_USER_LIMIT ||
        length > CHIMERA_ELF_USER_LIMIT - base) return -1;
    lock_backend();
    if (!tlb_shootdown) { unlock_backend(); return -2; }
    if (!space_valid(space)) { unlock_backend(); return -3; }
    uint32_t index = space->mapped_count;
    FrameBlock *block = find_block(space, base, length);
    if (!block) { unlock_backend(); return -4; }
    index = static_cast<uint32_t>(block - space->mapped);
    for (uint64_t i = 0; i < block->pages; ++i) {
        uint64_t *pte = find_pte(space, base + i * PAGE_SIZE);
        PageMeta *meta = find_page_meta(space, base + i * PAGE_SIZE, nullptr);
        if (!pte || !(*pte & ENTRY_PRESENT) || !meta || meta->state != PAGE_RESIDENT ||
            meta->physical == 0u || meta->pins != 0u ||
            ((*pte & ENTRY_ADDRESS_MASK) != meta->physical)) {
            unlock_backend(); return -5;
        }
    }
    const uint64_t root = space->root_physical;
    const uint32_t pages = block->pages;
    const uint64_t metadata_physical = block->metadata_physical;
    const uint32_t metadata_pages = block->metadata_pages;
    for (uint64_t i = 0; i < pages; ++i) *find_pte(space, base + i * PAGE_SIZE) = 0;
    // The callback is required to be synchronous and cannot report partial
    // completion: frames are not returned to the allocator before shootdown.
    tlb_shootdown(root, base, length, tlb_context);
    for (uint64_t i = 0; i < pages; ++i)
        prune_empty_user_tables(space, base + i * PAGE_SIZE);
    auto *page_meta = reinterpret_cast<PageMeta *>(static_cast<uintptr_t>(metadata_physical));
    for (uint32_t i = 0; i < pages; ++i) {
        if (koronos_vm_frame_release(page_meta[i].physical) != 0) {
            // Never reinstall PTEs to possibly reclaimed frames. The unmapped
            // range remains inaccessible and teardown is blocked for diagnosis.
            tlb_shootdown(root, base, length, tlb_context);
            unlock_backend(); return -6;
        }
        page_meta[i].physical = 0;
        page_meta[i].state = PAGE_NONRESIDENT;
    }
    if (metadata_physical && metadata_pages)
        (void)koronos_vm_frame_release_contiguous(metadata_physical, metadata_pages);
    for (uint32_t v = 0; v < space->vma_count; ++v) {
        if (space->vmas[v].virtual_base == base && space->vmas[v].length == length) {
            for (uint32_t j = v + 1; j < space->vma_count; ++j) space->vmas[j - 1] = space->vmas[j];
            --space->vma_count;
            break;
        }
    }
    space->user_pages -= pages;
    for (uint32_t i = index + 1; i < space->mapped_count; ++i) space->mapped[i - 1] = space->mapped[i];
    --space->mapped_count;
    unlock_backend();
    return 0;
}

extern "C" int koronos_address_space_protect(void *opaque, uint64_t base, uint64_t length,
                                               uint32_t elf_flags) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || (elf_flags & ~7u) != 0u ||
        ((elf_flags & 2u) && (elf_flags & 1u)) || !length || (base & PAGE_MASK) ||
        (length & PAGE_MASK) || base < KORONOS_USER_VIRTUAL_MIN ||
        base >= CHIMERA_ELF_USER_LIMIT || length > CHIMERA_ELF_USER_LIMIT - base) return -1;
    lock_backend();
    if (!tlb_shootdown) { unlock_backend(); return -2; }
    FrameBlock *block = find_block(space, base, length);
    if (!block) { unlock_backend(); return -3; }
    for (uint64_t i = 0; i < block->pages; ++i) {
        uint64_t *pte = find_pte(space, base + i * PAGE_SIZE);
        PageMeta *meta = find_page_meta(space, base + i * PAGE_SIZE, nullptr);
        if (!pte || !(*pte & ENTRY_PRESENT) || !meta || meta->state != PAGE_RESIDENT ||
            meta->physical == 0u || meta->pins != 0u ||
            ((*pte & ENTRY_ADDRESS_MASK) != meta->physical)) {
            unlock_backend(); return -4;
        }
    }
    const uint64_t root = space->root_physical;
    for (uint64_t i = 0; i < block->pages; ++i) {
        uint64_t *pte = find_pte(space, base + i * PAGE_SIZE);
        PageMeta *meta = find_page_meta(space, base + i * PAGE_SIZE, nullptr);
        *pte = (*pte & ~(ENTRY_WRITE | ENTRY_NX)) |
               ((elf_flags & 2u) ? ENTRY_WRITE : 0u) |
               ((elf_flags & 1u) ? 0u : ENTRY_NX);
        if (meta) meta->flags = static_cast<uint8_t>(
            (meta->flags & (PAGE_META_DIRTY | PAGE_META_REFERENCED)) | elf_flags);
    }
    tlb_shootdown(root, base, length, tlb_context);
    block->elf_flags = elf_flags;
    for (uint32_t v = 0; v < space->vma_count; ++v) {
        if (space->vmas[v].virtual_base == base && space->vmas[v].length == length)
            space->vmas[v].elf_flags = elf_flags;
    }
    unlock_backend();
    return 0;
}

extern "C" int koronos_address_space_query(void *opaque, uint64_t va,
                                             uint64_t *physical_out, uint32_t *flags_out) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || va < KORONOS_USER_VIRTUAL_MIN ||
        va >= CHIMERA_ELF_USER_LIMIT || !physical_out || !flags_out) return -1;
    lock_backend();
    uint64_t *pte = find_pte(space, va);
    if (!pte || !(*pte & ENTRY_PRESENT) || !(*pte & ENTRY_USER)) {
        unlock_backend(); return -2;
    }
    *physical_out = (*pte & ENTRY_ADDRESS_MASK) | (va & PAGE_MASK);
    *flags_out = ((*pte & ENTRY_NX) ? 0u : 1u) |
                 ((*pte & ENTRY_WRITE) ? 2u : 0u) | 4u;
    unlock_backend();
    return 0;
}

extern "C" int koronos_address_space_vma_query(void *opaque, uint64_t va,
                                                 koronos_vma_descriptor *out) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || !out || va < KORONOS_USER_VIRTUAL_MIN ||
        va >= CHIMERA_ELF_USER_LIMIT) return -1;
    lock_backend();
    for (uint32_t i = 0; i < space->vma_count; ++i) {
        const koronos_vma_descriptor &vma = space->vmas[i];
        if (va >= vma.virtual_base && va - vma.virtual_base < vma.length) {
            *out = vma;
            unlock_backend();
            return 0;
        }
    }
    unlock_backend();
    return -2;
}

extern "C" int koronos_address_space_vma_set_backing(void *opaque, uint64_t base,
                                                       uint64_t length, uint32_t kind,
                                                       uint64_t object, uint64_t offset) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || kind > KORONOS_VMA_SWAP || !length ||
        (base & PAGE_MASK) || (length & PAGE_MASK) ||
        base < KORONOS_USER_VIRTUAL_MIN || base >= CHIMERA_ELF_USER_LIMIT ||
        length > CHIMERA_ELF_USER_LIMIT - base || offset > UINT64_MAX - length)
        return -1;
    if ((kind == KORONOS_VMA_ELF_IMAGE || kind == KORONOS_VMA_FILE) && object == 0u)
        return -2;
    lock_backend();
    for (uint32_t i = 0; i < space->vma_count; ++i) {
        koronos_vma_descriptor &vma = space->vmas[i];
        if (vma.virtual_base != base || vma.length != length) continue;
        if (kind == KORONOS_VMA_SWAP) {
            FrameBlock *block = find_block(space, base, length);
            if (!block) { unlock_backend(); return -3; }
            auto *meta = reinterpret_cast<PageMeta *>(static_cast<uintptr_t>(block->metadata_physical));
            for (uint32_t p = 0; p < block->pages; ++p) {
                if (meta[p].owner_generation != space->generation ||
                    meta[p].state != PAGE_SWAPPED || meta[p].swap_slot == KORONOS_SWAP_SLOT_INVALID) {
                    unlock_backend(); return -4;
                }
            }
        }
        vma.backing_kind = kind;
        vma.backing_object = object;
        vma.backing_offset = offset;
        unlock_backend();
        return 0;
    }
    unlock_backend();
    return -5;
}

namespace {
static PageMeta *find_page_meta(AddressSpace *space, uint64_t page_va, uint64_t *physical_out) {
    for (uint32_t i = 0; i < space->mapped_count; ++i) {
        FrameBlock &b = space->mapped[i];
        const uint64_t bytes = static_cast<uint64_t>(b.pages) * PAGE_SIZE;
        if (page_va < b.virtual_base || page_va - b.virtual_base >= bytes) continue;
        const uint64_t index = (page_va - b.virtual_base) / PAGE_SIZE;
        if (index >= b.pages || !b.metadata_physical) return nullptr;
        auto *meta = reinterpret_cast<PageMeta *>(static_cast<uintptr_t>(b.metadata_physical));
        if (meta[index].owner_generation != space->generation) return nullptr;
        if (physical_out) *physical_out = meta[index].physical;
        return &meta[index];
    }
    return nullptr;
}
}

extern "C" int koronos_address_space_pin(void *opaque, uint64_t address, uint64_t length,
                                           uint32_t write_access) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || !length || write_access > 1u ||
        address < KORONOS_USER_VIRTUAL_MIN || address >= CHIMERA_ELF_USER_LIMIT ||
        length > CHIMERA_ELF_USER_LIMIT - address) return -1;
    const uint64_t end = address + length;
    const uint64_t first_page = address & ~PAGE_MASK;
    // Syscall entry is interrupt context; never perform swap I/O here.
    // Resident pages are pinned below; swapped pages fail until a pager thread
    // has resolved them before the syscall attempts its user-memory copy.
    lock_backend();
    if (!space_valid(space)) { unlock_backend(); return -2; }
    // Validate the entire range before changing any pin counts.
    for (uint64_t va = first_page; va < end; va += PAGE_SIZE) {
        uint64_t physical = 0;
        PageMeta *meta = find_page_meta(space, va, &physical);
        uint64_t *pte = find_pte(space, va);
        if (!meta || meta->state != PAGE_RESIDENT || meta->pins == UINT16_MAX ||
            !pte || !(*pte & ENTRY_PRESENT) || !(*pte & ENTRY_USER) ||
            ((*pte & ENTRY_ADDRESS_MASK) != physical) ||
            (write_access && !(*pte & ENTRY_WRITE))) {
            unlock_backend(); return -3;
        }
        if (va > UINT64_MAX - PAGE_SIZE) { unlock_backend(); return -4; }
    }
    for (uint64_t va = first_page; va < end; va += PAGE_SIZE) {
        PageMeta *meta = find_page_meta(space, va, nullptr);
        ++meta->pins;
        meta->flags |= PAGE_META_REFERENCED;
        if (write_access) meta->flags |= PAGE_META_DIRTY;
    }
    unlock_backend();
    return 0;
}

extern "C" int koronos_address_space_unpin(void *opaque, uint64_t address, uint64_t length) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || !length || address < KORONOS_USER_VIRTUAL_MIN ||
        address >= CHIMERA_ELF_USER_LIMIT || length > CHIMERA_ELF_USER_LIMIT - address) return -1;
    const uint64_t end = address + length;
    const uint64_t first_page = address & ~PAGE_MASK;
    lock_backend();
    if (!space_valid(space)) { unlock_backend(); return -2; }
    for (uint64_t va = first_page; va < end; va += PAGE_SIZE) {
        PageMeta *meta = find_page_meta(space, va, nullptr);
        if (!meta || meta->state != PAGE_RESIDENT || meta->pins == 0) {
            unlock_backend(); return -3;
        }
        if (va > UINT64_MAX - PAGE_SIZE) { unlock_backend(); return -4; }
    }
    for (uint64_t va = first_page; va < end; va += PAGE_SIZE) {
        PageMeta *meta = find_page_meta(space, va, nullptr);
        --meta->pins;
    }
    unlock_backend();
    return 0;
}

extern "C" int koronos_address_space_evict_one(void *opaque) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space)) return -1;
    koronos_swap_snapshot swap_status{};
    if (koronos_swap_get_snapshot(&swap_status) != 0 || !swap_status.initialized) return -2;
    lock_backend();
    if (!space_valid(space) || !tlb_shootdown) { unlock_backend(); return -3; }
    const uint64_t total = space->user_pages;
    if (!total) { unlock_backend(); return -4; }
    const uint64_t start = space->eviction_cursor % total;
    const uint64_t scan = total < VM_EVICTION_SCAN_LIMIT ? total : VM_EVICTION_SCAN_LIMIT;
    for (uint64_t step = 0; step < scan; ++step) {
        const uint64_t flat = (start + step) % total;
        uint64_t prefix = 0, va = 0; FrameBlock *block = nullptr; uint32_t page_index = 0;
        for (uint32_t b = 0; b < space->mapped_count; ++b) {
            if (flat < prefix + space->mapped[b].pages) { block = &space->mapped[b]; page_index = static_cast<uint32_t>(flat - prefix); break; }
            prefix += space->mapped[b].pages;
        }
        if (!block) continue;
        va = block->virtual_base + static_cast<uint64_t>(page_index) * PAGE_SIZE;
        PageMeta *meta = find_page_meta(space, va, nullptr); uint64_t *pte = find_pte(space, va);
        if (!meta || !pte || meta->state != PAGE_RESIDENT || meta->pins || !meta->physical ||
            !(*pte & ENTRY_PRESENT) || ((*pte & ENTRY_ADDRESS_MASK) != meta->physical) ||
            koronos_vm_frame_refcount(meta->physical) != 1u) continue;
        if (*pte & ENTRY_DIRTY) meta->flags |= PAGE_META_DIRTY;
        if ((*pte & ENTRY_ACCESSED) || (meta->flags & PAGE_META_REFERENCED)) {
            *pte &= ~ENTRY_ACCESSED; meta->flags &= static_cast<uint8_t>(~PAGE_META_REFERENCED);
            space->eviction_cursor = (flat + 1u) % total;
            const uint64_t root = space->root_physical; const auto shoot = tlb_shootdown; void *ctx = tlb_context;
            unlock_backend(); shoot(root, va, PAGE_SIZE, ctx); return 1;
        }
        const uint64_t physical = meta->physical, root = space->root_physical;
        const uint64_t original_pte = *pte; const uint32_t old_slot = meta->swap_slot;
        const auto shoot = tlb_shootdown; void *ctx = tlb_context;
        meta->state = PAGE_EVICTING;
        if (*pte & ENTRY_WRITE) *pte &= ~ENTRY_WRITE;
        space->eviction_cursor = (flat + 1u) % total;
        unlock_backend();
        if (original_pte & ENTRY_WRITE) shoot(root, va, PAGE_SIZE, ctx);
        uint32_t new_slot = KORONOS_SWAP_SLOT_INVALID;
        if (koronos_swap_store(reinterpret_cast<const void *>(static_cast<uintptr_t>(physical)), &new_slot) != 0) {
            lock_backend();
            if (meta->state == PAGE_EVICTING && meta->physical == physical) { *pte = original_pte; meta->state = PAGE_RESIDENT; }
            unlock_backend();
            if (original_pte & ENTRY_WRITE) shoot(root, va, PAGE_SIZE, ctx);
            return -5;
        }
        if (old_slot != KORONOS_SWAP_SLOT_INVALID && koronos_swap_release(old_slot) != 0) {
            (void)koronos_swap_release(new_slot);
            lock_backend();
            if (meta->state == PAGE_EVICTING && meta->physical == physical) { *pte = original_pte; meta->state = PAGE_RESIDENT; }
            unlock_backend();
            if (original_pte & ENTRY_WRITE) shoot(root, va, PAGE_SIZE, ctx);
            return -6;
        }
        lock_backend();
        if (old_slot != KORONOS_SWAP_SLOT_INVALID && meta->swap_slot == old_slot)
            meta->swap_slot = KORONOS_SWAP_SLOT_INVALID;
        if (meta->state != PAGE_EVICTING || meta->physical != physical ||
            !(*pte & ENTRY_PRESENT) || ((*pte & ENTRY_ADDRESS_MASK) != physical)) {
            if (meta->state == PAGE_EVICTING) meta->state = PAGE_NONRESIDENT;
            unlock_backend(); (void)koronos_swap_release(new_slot);
            if (original_pte & ENTRY_WRITE) shoot(root, va, PAGE_SIZE, ctx);
            return -7;
        }
        *pte = ENTRY_SWAPPED; meta->swap_slot = new_slot; meta->physical = 0; meta->state = PAGE_SWAPPED;
        for (uint32_t v = 0; v < space->vma_count; ++v) {
            auto &vma = space->vmas[v];
            if (va >= vma.virtual_base && va - vma.virtual_base < vma.length) {
                if (vma.resident_pages) --vma.resident_pages;
                vma.residency = vma.resident_pages == 0 ? KORONOS_VMA_NONRESIDENT : KORONOS_VMA_PARTIAL;
                break;
            }
        }
        unlock_backend();
        shoot(root, va, PAGE_SIZE, ctx);
        const int release_rc = koronos_vm_frame_release(physical);
        if (release_rc != 0 && release_rc == -3 && koronos_vm_frame_refcount(physical) != 0u) {
            lock_backend();
            if (meta->state == PAGE_SWAPPED && meta->swap_slot == new_slot && meta->physical == 0u) {
                meta->physical = physical; meta->state = PAGE_RESIDENT; meta->swap_slot = KORONOS_SWAP_SLOT_INVALID;
                *pte = physical | (original_pte & ~ENTRY_ADDRESS_MASK);
                for (uint32_t v = 0; v < space->vma_count; ++v) {
                    auto &vma = space->vmas[v];
                    if (va >= vma.virtual_base && va - vma.virtual_base < vma.length) {
                        ++vma.resident_pages; vma.residency = KORONOS_VMA_RESIDENT; break;
                    }
                }
            }
            unlock_backend(); shoot(root, va, PAGE_SIZE, ctx); (void)koronos_swap_release(new_slot); return -8;
        }
        return release_rc == 0 ? 0 : -9;
    }
    space->eviction_cursor = (start + scan) % total;
    unlock_backend(); return -10;
}

extern "C" int koronos_address_space_page_fault_fastpath(void *opaque, uint64_t fault_address, uint64_t error_code) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || fault_address < KORONOS_USER_VIRTUAL_MIN ||
        fault_address >= CHIMERA_ELF_USER_LIMIT || !(error_code & 4u) || (error_code & 8u)) return -1;
    const uint64_t va = fault_address & ~PAGE_MASK;
    lock_backend();
    PageMeta *meta = find_page_meta(space, va, nullptr);
    uint64_t *pte = find_pte(space, va);
    const koronos_vma_descriptor *vma = nullptr;
    for (uint32_t i = 0; i < space->vma_count; ++i)
        if (va >= space->vmas[i].virtual_base && va - space->vmas[i].virtual_base < space->vmas[i].length) {
            vma = &space->vmas[i]; break;
        }
    if (!meta || !pte || !vma) { unlock_backend(); return -2; }
    if (((error_code & 2u) && !(vma->elf_flags & 2u)) ||
        ((error_code & 16u) && !(vma->elf_flags & 1u))) { unlock_backend(); return -3; }
    if (meta->state == PAGE_RESIDENT && (*pte & ENTRY_PRESENT) &&
        user_page_access(space->root_physical, va, (error_code & 2u) != 0u) &&
        (!(error_code & 16u) || !(*pte & ENTRY_NX))) {
        unlock_backend(); return 0;
    }
    // Storage-backed transitions are intentionally delegated to a pager thread.
    // Exception/syscall entry must never block on a device callback.
    unlock_backend();
    return -4;
}

extern "C" int koronos_address_space_handle_page_fault(void *opaque, uint64_t fault_address, uint64_t error_code) {
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || fault_address < KORONOS_USER_VIRTUAL_MIN || fault_address >= CHIMERA_ELF_USER_LIMIT ||
        !(error_code & 4u) || (error_code & 8u)) return -1;
    const uint64_t va = fault_address & ~PAGE_MASK;
    for (uint32_t wait = 0; wait < 1000000u; ++wait) {
        lock_backend();
        if (!space_valid(space)) { unlock_backend(); return -2; }
        PageMeta *meta = find_page_meta(space, va, nullptr); uint64_t *pte = find_pte(space, va);
        koronos_vma_descriptor *vma = nullptr;
        for (uint32_t i = 0; i < space->vma_count; ++i)
            if (va >= space->vmas[i].virtual_base && va - space->vmas[i].virtual_base < space->vmas[i].length) { vma = &space->vmas[i]; break; }
        if (!meta || !pte || !vma) { unlock_backend(); return -3; }
        if (((error_code & 2u) && !(vma->elf_flags & 2u)) || ((error_code & 16u) && !(vma->elf_flags & 1u))) { unlock_backend(); return -4; }
        if (meta->state == PAGE_EVICTING || meta->state == PAGE_LOADING) { unlock_backend(); __asm__ volatile("pause"); continue; }
        if (meta->state == PAGE_RESIDENT && (*pte & ENTRY_PRESENT)) {
            const bool allowed = (!(error_code & 2u) || (*pte & ENTRY_WRITE)) && (!(error_code & 16u) || !(*pte & ENTRY_NX));
            unlock_backend(); return allowed ? 0 : -5;
        }
        if (meta->state != PAGE_SWAPPED || !(*pte & ENTRY_SWAPPED) || (*pte & ENTRY_PRESENT) ||
            meta->swap_slot == KORONOS_SWAP_SLOT_INVALID || !tlb_shootdown) { unlock_backend(); return -6; }
        const uint32_t slot = meta->swap_slot; const uint32_t flags = vma->elf_flags;
        const uint64_t root = space->root_physical; const auto shoot = tlb_shootdown; void *ctx = tlb_context;
        meta->state = PAGE_LOADING;
        unlock_backend();
        uint64_t frame = koronos_vm_frame_alloc();
        for (uint32_t retry = 0; !frame && retry < VM_EVICTION_RETRY_LIMIT; ++retry) {
            (void)koronos_address_space_evict_one(space); frame = koronos_vm_frame_alloc();
        }
        if (!frame) { lock_backend(); if (meta->state == PAGE_LOADING) meta->state = PAGE_SWAPPED; unlock_backend(); return -7; }
        if (koronos_swap_load(slot, reinterpret_cast<void *>(static_cast<uintptr_t>(frame))) != 0) {
            (void)koronos_vm_frame_release(frame);
            lock_backend(); if (meta->state == PAGE_LOADING) meta->state = PAGE_SWAPPED; unlock_backend(); return -8;
        }
        lock_backend();
        if (meta->state != PAGE_LOADING || meta->swap_slot != slot || !(*pte & ENTRY_SWAPPED) || (*pte & ENTRY_PRESENT)) {
            if (meta->state == PAGE_LOADING) meta->state = PAGE_SWAPPED;
            unlock_backend(); (void)koronos_vm_frame_release(frame); return -9;
        }
        meta->physical = frame; meta->state = PAGE_LOADING;
        *pte = frame | ENTRY_PRESENT | ENTRY_USER | ((flags & 2u) ? ENTRY_WRITE : 0u) | ((flags & 1u) ? 0u : ENTRY_NX);
        for (uint32_t v = 0; v < space->vma_count; ++v) {
            auto &entry = space->vmas[v];
            if (va >= entry.virtual_base && va - entry.virtual_base < entry.length) {
                ++entry.resident_pages; entry.residency = entry.resident_pages == entry.page_count ? KORONOS_VMA_RESIDENT : KORONOS_VMA_PARTIAL; break;
            }
        }
        unlock_backend();
        shoot(root, va, PAGE_SIZE, ctx);
        const int slot_release = koronos_swap_release(slot);
        lock_backend();
        if (meta->state == PAGE_LOADING && meta->physical == frame) {
            if (slot_release == 0 && meta->swap_slot == slot) meta->swap_slot = KORONOS_SWAP_SLOT_INVALID;
            meta->state = PAGE_RESIDENT;
        }
        unlock_backend();
        return 0;
    }
    return -10;
}

extern "C" uint64_t koronos_address_space_count(void) { return created_spaces; }
