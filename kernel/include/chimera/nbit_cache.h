#pragma once
#include <stdint.h>
#include "chimera/nbit_vm.h"

/* Fixed-capacity, caller-owned direct-mapped decode cache. No allocation or locks:
   each VM instance owns its cache; code_generation must change when code is modified. */
struct ChimeraNBitInstructionCacheLine {
    uintptr_t program_identity;
    uint64_t code_generation;
    uint32_t pc;
    uint8_t valid;
    uint8_t reserved[3];
    ChimeraNBitInstruction instruction;
};
struct ChimeraNBitInstructionCache {
    ChimeraNBitInstructionCacheLine *lines;
    uint32_t line_count;
    uint64_t hits;
    uint64_t misses;
};
class ChimeraNBitCache final {
public:
    static int initialize(ChimeraNBitInstructionCache &cache,
                          ChimeraNBitInstructionCacheLine *lines, uint32_t line_count);
    static bool fetch(ChimeraNBitInstructionCache &cache, const ChimeraNBitInstruction *program,
                      uint32_t pc, uint64_t code_generation, ChimeraNBitInstruction &out);
    static void invalidate(ChimeraNBitInstructionCache &cache);
};
extern "C" {
int chimera_nbit_cache_initialize(ChimeraNBitInstructionCache *cache,
                                  ChimeraNBitInstructionCacheLine *lines, uint32_t line_count);
void chimera_nbit_cache_invalidate(ChimeraNBitInstructionCache *cache);
}
