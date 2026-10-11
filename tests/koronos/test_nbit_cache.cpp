#include "chimera/nbit_cache.h"
#include <cassert>
int main() {
    ChimeraNBitInstruction program[2]{};
    program[0].opcode=CHIMERA_NBIT_OP_LOAD_IMM32;
    program[0].immediate=0x12345678u;
    program[1].opcode=CHIMERA_NBIT_OP_HALT;
    ChimeraNBitInstructionCacheLine lines[4]{};
    ChimeraNBitInstructionCache cache{};
    assert(ChimeraNBitCache::initialize(cache,lines,4)==0);
    ChimeraNBitInstruction out{};
    assert(ChimeraNBitCache::fetch(cache,program,0,1,out));
    assert(out.immediate==0x12345678u && cache.misses==1);
    assert(ChimeraNBitCache::fetch(cache,program,0,1,out));
    assert(cache.hits==1);
    assert(ChimeraNBitCache::fetch(cache,program,0,2,out));
    assert(cache.misses==2); // generation change is a miss
    ChimeraNBitCache::invalidate(cache);
    for (const auto &line : lines) assert(line.valid==0);
    return 0;
}
