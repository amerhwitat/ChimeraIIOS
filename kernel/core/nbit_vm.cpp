#include "chimera/nbit_vm.h"

namespace {
static uint32_t nbytes(uint32_t bits) { return (uint32_t)(((uint64_t)bits+7u)/8u); }
static uint8_t top_mask(uint32_t bits) {
    uint32_t rem=bits&7u; return rem?(uint8_t)((1u<<rem)-1u):0xffu;
}
static ChimeraNBitConstView as_const(ChimeraNBitView v) {
    return {v.bytes,v.bit_width,v.capacity_bytes};
}
}
int ChimeraNBitVM::initialize(ChimeraNBitVMState &s,uint8_t *storage,
                              uint32_t count,uint32_t stride,uint32_t storage_bytes,
                              uint32_t bits,uint64_t limit) {
    if(!storage||!count||!bits||!limit)return CHIMERA_NBIT_VM_INVALID;
    const uint32_t bytes=nbytes(bits);
    if(stride<bytes||(uint64_t)count*stride>storage_bytes)return CHIMERA_NBIT_VM_INVALID;
    s={};s.register_bytes=storage;s.register_count=count;s.register_stride=stride;
    s.register_storage_bytes=storage_bytes;s.bit_width=bits;s.step_limit=limit;
    for(uint32_t i=0;i<storage_bytes;++i)storage[i]=0;
    return 0;
}
int ChimeraNBitVM::register_view(ChimeraNBitVMState &s,uint32_t index,ChimeraNBitView &out) {
    if(!s.register_bytes||index>=s.register_count||!s.bit_width)return CHIMERA_NBIT_VM_INVALID;
    const uint64_t offset=(uint64_t)index*s.register_stride;
    const uint32_t bytes=nbytes(s.bit_width);
    if(offset+bytes>s.register_storage_bytes)return CHIMERA_NBIT_VM_INVALID;
    out={s.register_bytes+(uint32_t)offset,s.bit_width,s.register_stride};
    return 0;
}
int ChimeraNBitVM::run(ChimeraNBitVMState &s,const ChimeraNBitInstruction *program,
                       uint32_t instruction_count) {
    if(!program||!instruction_count||!s.register_bytes||!s.register_count||
       !s.bit_width||!s.step_limit)return CHIMERA_NBIT_VM_INVALID;
    if(s.halted)return CHIMERA_NBIT_VM_HALTED;
    while(s.pc<instruction_count) {
        if(s.steps>=s.step_limit)return CHIMERA_NBIT_VM_STEP_LIMIT;
        const ChimeraNBitInstruction ins=program[s.pc++];
        ++s.steps;
        ChimeraNBitView d{},a{},b{};
        switch(ins.opcode) {
        case CHIMERA_NBIT_OP_HALT:
            s.halted=1;return CHIMERA_NBIT_VM_HALTED;
        case CHIMERA_NBIT_OP_LOAD_IMM32:
            if(register_view(s,ins.dst,d)!=0)return CHIMERA_NBIT_VM_BAD_PROGRAM;
            for(uint32_t i=0;i<d.capacity_bytes;++i)d.bytes[i]=0;
            for(uint32_t i=0;i<4u&&i<nbytes(s.bit_width);++i)
                d.bytes[i]=(uint8_t)(ins.immediate>>(i*8u));
            d.bytes[nbytes(s.bit_width)-1u]&=top_mask(s.bit_width);
            break;
        case CHIMERA_NBIT_OP_MOV:
            if(register_view(s,ins.dst,d)!=0||register_view(s,ins.lhs,a)!=0)return CHIMERA_NBIT_VM_BAD_PROGRAM;
            for(uint32_t i=0;i<nbytes(s.bit_width);++i)d.bytes[i]=a.bytes[i];
            break;
        case CHIMERA_NBIT_OP_ADD: case CHIMERA_NBIT_OP_SUB:
        case CHIMERA_NBIT_OP_AND: case CHIMERA_NBIT_OP_OR: case CHIMERA_NBIT_OP_XOR:
            if(register_view(s,ins.dst,d)!=0||register_view(s,ins.lhs,a)!=0||
               register_view(s,ins.rhs,b)!=0)return CHIMERA_NBIT_VM_BAD_PROGRAM;
            if(ins.opcode==CHIMERA_NBIT_OP_ADD) {
                if(ChimeraNBitArithmetic::add(d,as_const(a),as_const(b))!=0)return CHIMERA_NBIT_VM_INVALID;
            } else if(ins.opcode==CHIMERA_NBIT_OP_SUB) {
                if(ChimeraNBitArithmetic::subtract(d,as_const(a),as_const(b))!=0)return CHIMERA_NBIT_VM_INVALID;
            } else if(ins.opcode==CHIMERA_NBIT_OP_AND) {
                if(ChimeraNBitArithmetic::bit_and(d,as_const(a),as_const(b))!=0)return CHIMERA_NBIT_VM_INVALID;
            } else if(ins.opcode==CHIMERA_NBIT_OP_OR) {
                if(ChimeraNBitArithmetic::bit_or(d,as_const(a),as_const(b))!=0)return CHIMERA_NBIT_VM_INVALID;
            } else {
                if(ChimeraNBitArithmetic::bit_xor(d,as_const(a),as_const(b))!=0)return CHIMERA_NBIT_VM_INVALID;
            }
            break;
        case CHIMERA_NBIT_OP_NOT:
            if(register_view(s,ins.dst,d)!=0||register_view(s,ins.lhs,a)!=0)return CHIMERA_NBIT_VM_BAD_PROGRAM;
            if(ChimeraNBitArithmetic::bit_not(d,as_const(a))!=0)return CHIMERA_NBIT_VM_INVALID;
            break;
        case CHIMERA_NBIT_OP_SHL: case CHIMERA_NBIT_OP_SHR:
            if(register_view(s,ins.dst,d)!=0||register_view(s,ins.lhs,a)!=0)return CHIMERA_NBIT_VM_BAD_PROGRAM;
            if(ins.opcode==CHIMERA_NBIT_OP_SHL) {
                if(ChimeraNBitArithmetic::shift_left(d,as_const(a),ins.immediate)!=0)return CHIMERA_NBIT_VM_INVALID;
            } else if(ChimeraNBitArithmetic::shift_right(d,as_const(a),ins.immediate)!=0)return CHIMERA_NBIT_VM_INVALID;
            break;
        case CHIMERA_NBIT_OP_CMP:
            if(register_view(s,ins.lhs,a)!=0||register_view(s,ins.rhs,b)!=0)return CHIMERA_NBIT_VM_BAD_PROGRAM;
            s.zero_flag=(ChimeraNBitArithmetic::compare_unsigned(as_const(a),as_const(b))==0)?1u:0u;
            break;
        case CHIMERA_NBIT_OP_JMP:
            if(ins.immediate>=instruction_count)return CHIMERA_NBIT_VM_BAD_PROGRAM;
            s.pc=ins.immediate;break;
        case CHIMERA_NBIT_OP_JZ:
            if(ins.immediate>=instruction_count)return CHIMERA_NBIT_VM_BAD_PROGRAM;
            if(s.zero_flag)s.pc=ins.immediate;
            break;
        default:return CHIMERA_NBIT_VM_BAD_PROGRAM;
        }
    }
    return CHIMERA_NBIT_VM_BAD_PROGRAM;
}

extern "C" int chimera_nbit_vm_initialize(ChimeraNBitVMState *state,uint8_t *register_bytes,
                                            uint32_t register_count,uint32_t register_stride,
                                            uint32_t register_storage_bytes,uint32_t bit_width,
                                            uint64_t step_limit) {
    if(!state)return CHIMERA_NBIT_VM_INVALID;
    return ChimeraNBitVM::initialize(*state,register_bytes,register_count,register_stride,
                                     register_storage_bytes,bit_width,step_limit);
}
extern "C" int chimera_nbit_vm_run(ChimeraNBitVMState *state,
                                     const ChimeraNBitInstruction *program,
                                     uint32_t instruction_count) {
    if(!state)return CHIMERA_NBIT_VM_INVALID;
    return ChimeraNBitVM::run(*state,program,instruction_count);
}
