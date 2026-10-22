#include <stdint.h>
#include <stddef.h>
#include "chimera/address_space.h"
#include "chimera/frame_allocator.h"
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
constexpr uint32_t MAX_ADDRESS_SPACES = 8u;
constexpr uint32_t MAX_TABLE_FRAMES = 4096u;
constexpr uint32_t MAX_MAPPED_BLOCKS = CHIMERA_ELF_LOADER_MAX_SEGMENTS + 1u;
constexpr uint64_t MAX_USER_PAGES = 131072ull; // 512 MiB per address space.
constexpr uint64_t SPACE_MAGIC = 0x43484D4153504143ull; // "CHMASPAC"



struct FrameBlock { uint64_t physical; uint32_t pages; };
struct AddressSpace {
    uint64_t magic;
    uint64_t root_physical;
    uint64_t table_frames[MAX_TABLE_FRAMES];
    FrameBlock mapped[MAX_MAPPED_BLOCKS];
    uint32_t table_count;
    uint32_t mapped_count;
    uint64_t user_pages;
    uint8_t active;
};
static AddressSpace spaces[MAX_ADDRESS_SPACES]{};
static volatile uint32_t backend_ready = 0;
static volatile uint32_t backend_lock = 0;
static uint64_t created_spaces = 0;

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
    uint64_t physical = koronos_frame_alloc();
    if (!physical) return 0;
    if (!track_table(space, physical)) {
        (void)koronos_frame_free(physical);
        return 0;
    }
    zero_bytes(reinterpret_cast<void *>(static_cast<uintptr_t>(physical)), PAGE_SIZE);
    return physical;
}
static bool space_valid(const AddressSpace *space) {
    return space && space->magic == SPACE_MAGIC && space->active && space->root_physical;
}
static void destroy_locked(AddressSpace *space) {
    if (!space || space->magic != SPACE_MAGIC) return;
    for (uint32_t i = 0; i < space->mapped_count; ++i) {
        if (space->mapped[i].physical && space->mapped[i].pages)
            (void)koronos_frame_free_contiguous(space->mapped[i].physical, space->mapped[i].pages);
    }
    for (uint32_t i = space->table_count; i > 0; --i)
        (void)koronos_frame_free(space->table_frames[i - 1]);
    space->magic = 0;
    space->active = 0;
    space->root_physical = 0;
    space->table_count = 0;
    space->mapped_count = 0;
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

static void *create_address_space(void *) {
    if (!backend_ready) return nullptr;
    lock_backend();
    AddressSpace *space = nullptr;
    for (uint32_t i = 0; i < MAX_ADDRESS_SPACES; ++i) {
        if (!spaces[i].active && spaces[i].magic == 0) { space = &spaces[i]; break; }
    }
    if (!space) { unlock_backend(); return nullptr; }
    zero_bytes(space, sizeof(AddressSpace));
    space->magic = SPACE_MAGIC;
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
    AddressSpace *space = static_cast<AddressSpace *>(opaque);
    if (!space_valid(space) || space->mapped_count >= MAX_MAPPED_BLOCKS ||
        (elf_flags & ~7u) != 0u || (elf_flags & 2u && elf_flags & 1u)) return -2;
    const uint64_t pages64 = size / PAGE_SIZE;
    if (!pages64 || pages64 > UINT32_MAX || pages64 > MAX_USER_PAGES - space->user_pages) return -3;
    lock_backend();
    const uint64_t physical = koronos_frame_alloc_contiguous(static_cast<uint32_t>(pages64));
    if (!physical) { unlock_backend(); return -4; }
    FrameBlock &block = space->mapped[space->mapped_count++];
    block.physical = physical;
    block.pages = static_cast<uint32_t>(pages64);
    space->user_pages += pages64;
    const uint64_t leaf_flags = ENTRY_PRESENT | ENTRY_USER |
        ((elf_flags & 2u) ? ENTRY_WRITE : 0u) |
        ((elf_flags & 1u) ? 0u : ENTRY_NX);
    for (uint64_t i = 0; i < pages64; ++i) {
        uint64_t *pte = ensure_pte(space, virtual_base + i * PAGE_SIZE);
        if (!pte || (*pte & ENTRY_PRESENT)) { unlock_backend(); return -5; }
        *pte = (physical + i * PAGE_SIZE) | leaf_flags;
    }
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
        uint64_t *code_pte = ensure_pte(space, KORONOS_USER_VIRTUAL_MIN);
        uint64_t *stack_pte = ensure_pte(space, 0x00007FFFFFFFE000ull);
        uint64_t *root = table_ptr(space->root_physical);
        uint64_t *pdpt = root ? table_ptr(root[0] & ENTRY_ADDRESS_MASK) : nullptr;
        uint64_t *pd = pdpt ? table_ptr(pdpt[0] & ENTRY_ADDRESS_MASK) : nullptr;
        // Existing 2-MiB identity leaves must remain supervisor-only even though
        // their parent entries are user-capable for high user mappings.
        ok = code_pte && stack_pte && root && pdpt && pd &&
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
static const chimera_elf_load_ops loader_ops = {
    create_address_space, map_pages, destroy_address_space
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
extern "C" uint64_t koronos_address_space_count(void) { return created_spaces; }
