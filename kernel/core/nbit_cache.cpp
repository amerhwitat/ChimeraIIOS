#include "chimera/nbit_cache.h"
#include <stddef.h>

int ChimeraNBitCache::initialize(ChimeraNBitInstructionCache &c,
                                 ChimeraNBitInstructionCacheLine *lines, uint32_t count) {
    if (!lines || !count) return -1;
    c={}; c.lines=lines; c.line_count=count;
    for(uint32_t i=0;i<count;++i) lines[i]={};
    return 0;
}
bool ChimeraNBitCache::fetch(ChimeraNBitInstructionCache &c,
                             const ChimeraNBitInstruction *program, uint32_t pc,
                             uint64_t generation, ChimeraNBitInstruction &out) {
    if(!c.lines || !c.line_count || !program) return false;
    const uintptr_t identity=reinterpret_cast<uintptr_t>(program);
    const uint32_t index=(uint32_t)(((uint64_t)pc ^ (uint64_t)(identity>>4) ^ generation) % c.line_count);
    ChimeraNBitInstructionCacheLine &line=c.lines[index];
    if(line.valid && line.program_identity==identity && line.pc==pc &&
       line.code_generation==generation) {
        out=line.instruction; ++c.hits; return true;
    }
    line.program_identity=identity; line.pc=pc; line.code_generation=generation;
    line.instruction=program[pc]; line.valid=1; ++c.misses; out=line.instruction;
    return true;
}
void ChimeraNBitCache::invalidate(ChimeraNBitInstructionCache &c) {
    if(!c.lines)return;
    for(uint32_t i=0;i<c.line_count;++i)c.lines[i].valid=0;
}
extern "C" int chimera_nbit_cache_initialize(ChimeraNBitInstructionCache *c,
                                              ChimeraNBitInstructionCacheLine *lines,uint32_t count) {
    return c?ChimeraNBitCache::initialize(*c,lines,count):-1;
}
extern "C" void chimera_nbit_cache_invalidate(ChimeraNBitInstructionCache *c) {
    if(c)ChimeraNBitCache::invalidate(*c);
}
