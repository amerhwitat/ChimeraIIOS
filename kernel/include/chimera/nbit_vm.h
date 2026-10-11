#pragma once
#include <stdint.h>
#include "chimera/nbit_runtime.h"

enum ChimeraNBitOpcode : uint8_t {
    CHIMERA_NBIT_OP_HALT=0,
    CHIMERA_NBIT_OP_LOAD_IMM32=1,
    CHIMERA_NBIT_OP_MOV=2,
    CHIMERA_NBIT_OP_ADD=3,
    CHIMERA_NBIT_OP_SUB=4,
    CHIMERA_NBIT_OP_AND=5,
    CHIMERA_NBIT_OP_OR=6,
    CHIMERA_NBIT_OP_XOR=7,
    CHIMERA_NBIT_OP_NOT=8,
    CHIMERA_NBIT_OP_SHL=9,
    CHIMERA_NBIT_OP_SHR=10,
    CHIMERA_NBIT_OP_CMP=11,
    CHIMERA_NBIT_OP_JMP=12,
    CHIMERA_NBIT_OP_JZ=13
};

/* Versioned fixed-width bytecode instruction. immediate is interpreted as LE32
   by the loader; this in-memory representation is 8 bytes on supported targets. */
struct ChimeraNBitInstruction {
    uint8_t opcode;
    uint8_t dst;
    uint8_t lhs;
    uint8_t rhs;
    uint32_t immediate;
};
struct ChimeraNBitVMState {
    uint8_t *register_bytes;
    uint32_t register_count;
    uint32_t register_stride;
    uint32_t register_storage_bytes;
    uint32_t bit_width;
    uint32_t pc;
    uint64_t steps;
    uint64_t step_limit;
    uint8_t zero_flag;
    uint8_t halted;
    uint8_t reserved[6];
};
enum { CHIMERA_NBIT_VM_HALTED=0, CHIMERA_NBIT_VM_STEP_LIMIT=1,
       CHIMERA_NBIT_VM_INVALID=-1, CHIMERA_NBIT_VM_BAD_PROGRAM=-2 };

class ChimeraNBitVM final {
public:
    static int initialize(ChimeraNBitVMState &state, uint8_t *register_bytes,
                          uint32_t register_count, uint32_t register_stride,
                          uint32_t register_storage_bytes, uint32_t bit_width, uint64_t step_limit);
    static int run(ChimeraNBitVMState &state, const ChimeraNBitInstruction *program,
                   uint32_t instruction_count);
    static int register_view(ChimeraNBitVMState &state, uint32_t index,
                             ChimeraNBitView &out);
};
static_assert(sizeof(ChimeraNBitInstruction)==8, "Chimera N-bit bytecode ABI must be 8 bytes");

extern "C" {
int chimera_nbit_vm_initialize(ChimeraNBitVMState *state, uint8_t *register_bytes,
                              uint32_t register_count, uint32_t register_stride,
                              uint32_t register_storage_bytes, uint32_t bit_width,
                              uint64_t step_limit);
int chimera_nbit_vm_run(ChimeraNBitVMState *state,
                        const ChimeraNBitInstruction *program, uint32_t instruction_count);
}
