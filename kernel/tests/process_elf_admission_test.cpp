#include "chimera/process.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

namespace {
constexpr uint16_t MACHINE_X86_64 = KORONOS_EM_X86_64;
constexpr uint64_t STACK_TOP = 0x800000;
constexpr uint64_t IMAGE_SIZE = 0x1100;
constexpr uint64_t PAYLOAD_OFFSET = 0x1000;
constexpr uint64_t TEXT_ADDRESS = 0x400000;
constexpr uint32_t PT_LOAD = 1;
constexpr uint32_t PF_X = 1;
constexpr uint32_t PF_W = 2;
constexpr uint32_t PF_R = 4;

int check(bool ok, const char *name) {
    if (!ok) fprintf(stderr, "FAIL: %s\n", name);
    return ok ? 0 : 1;
}

void make_image(uint8_t *bytes, uint32_t flags = PF_R | PF_X) {
    memset(bytes, 0, IMAGE_SIZE);
    auto *h = reinterpret_cast<koronos_elf64_ehdr *>(bytes);
    h->e_ident[0] = KORONOS_ELF_MAG0;
    h->e_ident[1] = KORONOS_ELF_MAG1;
    h->e_ident[2] = KORONOS_ELF_MAG2;
    h->e_ident[3] = KORONOS_ELF_MAG3;
    h->e_ident[4] = KORONOS_ELFCLASS64;
    h->e_ident[5] = KORONOS_ELFDATA2LSB;
    h->e_ident[6] = 1;
    h->e_type = KORONOS_ET_EXEC;
    h->e_machine = MACHINE_X86_64;
    h->e_version = 1;
    h->e_entry = TEXT_ADDRESS;
    h->e_phoff = sizeof(koronos_elf64_ehdr);
    h->e_ehsize = sizeof(koronos_elf64_ehdr);
    h->e_phentsize = sizeof(koronos_elf64_phdr);
    h->e_phnum = 1;

    auto *ph = reinterpret_cast<koronos_elf64_phdr *>(
        bytes + h->e_phoff);
    ph->p_type = PT_LOAD;
    ph->p_flags = flags;
    ph->p_offset = PAYLOAD_OFFSET;
    ph->p_vaddr = TEXT_ADDRESS;
    ph->p_filesz = 16;
    ph->p_memsz = 0x200;
    ph->p_align = 0x1000;
    memset(bytes + PAYLOAD_OFFSET, 0x90, 16);
}
}

int main() {
    alignas(8) static uint8_t bytes[IMAGE_SIZE];
    chimera_process_image out{};
    int failures = 0;

    chimera_process_init();
    make_image(bytes);
    const int pid = chimera_process_admit_elf(
        bytes, sizeof(bytes), MACHINE_X86_64, STACK_TOP, &out);
    failures += check(pid > 0, "valid ELF is admitted");
    failures += check(out.pid == static_cast<uint32_t>(pid) &&
                      out.state == CHIMERA_PROCESS_ADMITTED,
                      "admission returns the registered PID and state");
    failures += check(out.segment_count == 1 &&
                      out.segments[0].virtual_address == TEXT_ADDRESS &&
                      out.segments[0].file_size == 16 &&
                      out.segments[0].memory_size == 0x200,
                      "PT_LOAD file and BSS sizes are preserved");
    failures += check(out.entry == TEXT_ADDRESS &&
                      out.image_low == TEXT_ADDRESS &&
                      out.image_high == TEXT_ADDRESS + 0x1000,
                      "entry and page-aligned image bounds are correct");
    failures += check(chimera_process_count() == 1,
                      "successful admission increments process registry count");

    chimera_process_image fetched{};
    failures += check(chimera_process_get(static_cast<uint32_t>(pid), &fetched) == 0 &&
                      fetched.entry == out.entry,
                      "registered load plan can be retrieved");
    failures += check(chimera_process_get(0, &fetched) != 0,
                      "zero PID lookup is rejected");

    chimera_process_init();
    make_image(bytes, PF_R | PF_W | PF_X);
    failures += check(chimera_process_admit_elf(
                          bytes, sizeof(bytes), MACHINE_X86_64, STACK_TOP, &out) == -7,
                      "writable executable segment is rejected");
    failures += check(chimera_process_count() == 0,
                      "rejected W+X image does not consume a registry slot");

    chimera_process_init();
    make_image(bytes);
    reinterpret_cast<koronos_elf64_ehdr *>(bytes)->e_entry = TEXT_ADDRESS + 0x400;
    failures += check(chimera_process_admit_elf(
                          bytes, sizeof(bytes), MACHINE_X86_64, STACK_TOP, &out) == -9,
                      "entry outside executable segment is rejected");

    chimera_process_init();
    make_image(bytes);
    auto *ph = reinterpret_cast<koronos_elf64_phdr *>(
        bytes + sizeof(koronos_elf64_ehdr));
    ph->p_filesz = ph->p_memsz + 1;
    failures += check(chimera_process_admit_elf(
                          bytes, sizeof(bytes), MACHINE_X86_64, STACK_TOP, &out) == -3,
                      "file size larger than memory size is rejected");

    chimera_process_init();
    make_image(bytes);
    ph = reinterpret_cast<koronos_elf64_phdr *>(
        bytes + sizeof(koronos_elf64_ehdr));
    ph->p_vaddr = UINT64_MAX - 0x10;
    ph->p_memsz = 0x200;
    failures += check(chimera_process_admit_elf(
                          bytes, sizeof(bytes), MACHINE_X86_64, STACK_TOP, &out) == -4,
                      "overflowing virtual segment range is rejected");

    chimera_process_init();
    make_image(bytes);
    auto *overlap_header = reinterpret_cast<koronos_elf64_ehdr *>(bytes);
    overlap_header->e_phnum = 2;
    auto *segments = reinterpret_cast<koronos_elf64_phdr *>(
        bytes + sizeof(koronos_elf64_ehdr));
    segments[1] = segments[0];
    segments[1].p_offset = PAYLOAD_OFFSET + 16;
    segments[1].p_vaddr = TEXT_ADDRESS + 0x100;
    segments[1].p_filesz = 8;
    segments[1].p_memsz = 0x100;
    segments[1].p_align = 1;
    failures += check(chimera_process_admit_elf(
                          bytes, sizeof(bytes), MACHINE_X86_64, STACK_TOP, &out) == -11,
                      "page-overlapping PT_LOAD segments are rejected");

    chimera_process_init();
    make_image(bytes);
    reinterpret_cast<koronos_elf64_ehdr *>(bytes)->e_phoff = UINT64_MAX - 8;
    failures += check(chimera_process_admit_elf(
                          bytes, sizeof(bytes), MACHINE_X86_64, STACK_TOP, &out) == -2,
                      "out-of-bounds program-header table is rejected");

    failures += check(chimera_process_admit_elf(
                          nullptr, sizeof(bytes), MACHINE_X86_64, STACK_TOP, &out) == -1,
                      "null image is rejected");
    failures += check(chimera_process_admit_elf(
                          bytes, sizeof(bytes), MACHINE_X86_64, STACK_TOP, nullptr) == -1,
                      "null output pointer is rejected");

    if (failures) return 1;
    puts("process ELF admission tests passed");
    return 0;
}
