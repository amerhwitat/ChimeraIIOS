#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "chimera/x86_64_cpu.h"

extern "C" void koronos_x86_64_context_trampoline() {}

static void sample_entry(void *) {}

int main() {
    alignas(16) uint8_t stack[256]{};
    uint64_t argument = 0x12345678u;
    chimera_x86_64_context context{};

    const uint64_t base = reinterpret_cast<uint64_t>(stack);
    const uint64_t top = (base + sizeof(stack)) & ~0xFull;
    assert(koronos_x86_64_context_prepare(&context, base, sizeof(stack),
                                         0x2000u, sample_entry, &argument) == 0);
    assert(context.rsp == top - CHIMERA_X86_64_CONTEXT_FRAME_SIZE);
    assert(context.cr3 == 0x2000u);

    const auto *frame = reinterpret_cast<const uint64_t *>(context.rsp);
    assert(frame[0] == 0); // r15
    assert(frame[1] == 0); // r14
    assert(frame[2] == reinterpret_cast<uint64_t>(sample_entry)); // r13
    assert(frame[3] == reinterpret_cast<uint64_t>(&argument)); // r12
    assert(frame[4] == 0); // rbx
    assert(frame[5] == 0); // rbp
    assert(frame[6] == reinterpret_cast<uint64_t>(&koronos_x86_64_context_trampoline));
    assert(frame[7] == 0); // alignment padding

    assert(koronos_x86_64_context_prepare(nullptr, base, sizeof(stack),
                                          0x2000u, sample_entry, &argument) == -1);
    assert(koronos_x86_64_context_prepare(&context, base, sizeof(stack),
                                          0, sample_entry, &argument) == -1);
    assert(koronos_x86_64_context_prepare(&context, base, sizeof(stack),
                                          0x2001u, sample_entry, &argument) == -1);
    assert(koronos_x86_64_context_prepare(&context, base, sizeof(stack),
                                          0x100000000ull, sample_entry, &argument) == -1);
    assert(koronos_x86_64_context_prepare(&context, base, 32u,
                                          0x2000u, sample_entry, &argument) == -1);
    assert(koronos_x86_64_context_prepare(&context, UINT64_MAX - 16u, 64u,
                                          0x2000u, sample_entry, &argument) == -1);
    assert(koronos_x86_64_context_prepare(&context, base, sizeof(stack),
                                          0x2000u, nullptr, &argument) == -1);

    puts("x86_64 context frame: ABI layout, stack alignment, CR3 validation and invalid inputs passed");
    return 0;
}
