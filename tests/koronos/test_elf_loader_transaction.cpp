#include "chimera/elf_loader.h"
#include <cassert>
#include <cstdint>
#include <cstring>
#include <map>
#include <vector>

namespace {
struct Page { uint8_t bytes[4096]{}; };
std::map<uint64_t, Page*> allocated;
std::map<uint64_t, std::pair<uint64_t, uint32_t>> mappings;
uint64_t next_phys = 0x1000;
uint64_t expected_entry = 0x400000, expected_stack = 0x70000000;
int fail_map_after = -1;
int map_calls = 0;
int alloc_page(void*, uint64_t* phys, void** alias) {
    Page* p = new Page{};
    *phys = next_phys; next_phys += 4096;
    allocated[*phys] = p; *alias = p->bytes; return 0;
}
int map_page(void*, uint64_t va, uint64_t phys, uint32_t flags) {
    if (fail_map_after >= 0 && map_calls++ == fail_map_after) return -1;
    if (!allocated.count(phys) || mappings.count(va)) return -1;
    mappings[va] = {phys, flags}; return 0;
}
void unmap_page(void*, uint64_t va) { mappings.erase(va); }
void free_page(void*, uint64_t phys) {
    auto it = allocated.find(phys);
    if (it != allocated.end()) { delete it->second; allocated.erase(it); }
}
int enter_user(void*, uint64_t entry, uint64_t stack, uint32_t pid) {
    assert(pid != 0 && entry == expected_entry && stack == expected_stack - 48);
    assert((stack & 15u) == 0);
    assert(mappings.size() == 17); // one PT_LOAD page plus sixteen stack pages
    const auto code = mappings.at(0x400000);
    assert(code.second == (CHIMERA_ELF_USER | CHIMERA_ELF_EXEC));
    Page* cp = allocated.at(code.first);
    assert(std::memcmp(cp->bytes, "TEST", 4) == 0);
    for (unsigned i = 4; i < 16; ++i) assert(cp->bytes[i] == 0); // BSS
    for (unsigned i = 0; i < CHIMERA_ELF_STACK_PAGES; ++i) {
        const uint64_t va = stack - uint64_t(i + 1) * 4096;
        const auto item = mappings.at(va);
        assert(item.second == (CHIMERA_ELF_USER | CHIMERA_ELF_WRITE)); // NX stack
        Page* sp = allocated.at(item.first);
        for (unsigned j = 0; j < 4096; ++j) assert(sp->bytes[j] == 0);
    }
    assert(!mappings.count(expected_stack - uint64_t(CHIMERA_ELF_STACK_PAGES + 1) * 4096));
    return 0; // returning is deliberately a failed ring-3 handoff
}
std::vector<uint8_t> fixture() {
    std::vector<uint8_t> bytes(256, 0);
    auto* h = reinterpret_cast<koronos_elf64_ehdr*>(bytes.data());
    h->e_ident[0] = 0x7f; h->e_ident[1] = 'E'; h->e_ident[2] = 'L'; h->e_ident[3] = 'F';
    h->e_ident[4] = 2; h->e_ident[5] = 1; h->e_ident[6] = 1;
    h->e_type = KORONOS_ET_EXEC; h->e_machine = KORONOS_EM_X86_64;
    h->e_version = 1; h->e_entry = 0x400000; h->e_phoff = 64;
    h->e_ehsize = sizeof(*h); h->e_phentsize = sizeof(koronos_elf64_phdr); h->e_phnum = 1;
    auto* ph = reinterpret_cast<koronos_elf64_phdr*>(bytes.data() + 64);
    ph->p_type = 1; ph->p_flags = 5; ph->p_offset = 120; ph->p_vaddr = 0x400000;
    ph->p_filesz = 4; ph->p_memsz = 16; ph->p_align = 1;
    std::memcpy(bytes.data() + 120, "TEST", 4);
    return bytes;
}
}
int main() {
    const chimera_elf_loader_ops ops{nullptr, alloc_page, map_page, unmap_page, free_page, enter_user};
    auto bytes = fixture();
    chimera_process_init();
    uint32_t pid = 0;
    int result = chimera_elf_load_and_enter(bytes.data(), bytes.size(), KORONOS_EM_X86_64,
                                             expected_stack, &ops, &pid);
    assert(result == -11 && pid != 0);
    assert(mappings.empty() && allocated.empty() && chimera_process_count() == 0);

    // Mapping failure halfway through must roll back all earlier PTEs and frames.
    map_calls = 0; fail_map_after = 4; pid = 0;
    result = chimera_elf_load_and_enter(bytes.data(), bytes.size(), KORONOS_EM_X86_64,
                                        expected_stack, &ops, &pid);
    assert(result == -9);
    assert(mappings.empty() && allocated.empty() && chimera_process_count() == 0);
    return 0;
}
