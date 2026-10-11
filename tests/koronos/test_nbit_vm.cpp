#include "chimera/nbit_vm.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main() {
    uint8_t registers[10]={};
    ChimeraNBitVMState vm{};
    assert(ChimeraNBitVM::initialize(vm,registers,5,2,sizeof(registers),13,32)==0);
    const ChimeraNBitInstruction program[]={
        {CHIMERA_NBIT_OP_LOAD_IMM32,0,0,0,7},
        {CHIMERA_NBIT_OP_LOAD_IMM32,1,0,0,5},
        {CHIMERA_NBIT_OP_ADD,2,0,1,0},
        {CHIMERA_NBIT_OP_LOAD_IMM32,3,0,0,12},
        {CHIMERA_NBIT_OP_CMP,0,2,3,0},
        {CHIMERA_NBIT_OP_JZ,0,0,0,7},
        {CHIMERA_NBIT_OP_LOAD_IMM32,4,0,0,99},
        {CHIMERA_NBIT_OP_HALT,0,0,0,0}
    };
    assert(ChimeraNBitVM::run(vm,program,sizeof(program)/sizeof(program[0]))==CHIMERA_NBIT_VM_HALTED);
    assert(vm.halted && vm.steps==7);
    assert(registers[4*2]==0 && registers[4*2+1]==0);
    assert(registers[2*2]==12 && registers[2*2+1]==0);

    uint8_t loop_registers[2]={};
    ChimeraNBitVMState loop{};
    assert(ChimeraNBitVM::initialize(loop,loop_registers,1,2,sizeof(loop_registers),13,2)==0);
    const ChimeraNBitInstruction infinite_loop[]={{CHIMERA_NBIT_OP_JMP,0,0,0,0}};
    assert(ChimeraNBitVM::run(loop,infinite_loop,1)==CHIMERA_NBIT_VM_STEP_LIMIT);
    assert(loop.steps==2);
    const ChimeraNBitInstruction bad[]={{255,0,0,0,0}};
    ChimeraNBitVMState invalid{};
    assert(ChimeraNBitVM::initialize(invalid,loop_registers,1,2,sizeof(loop_registers),13,4)==0);
    assert(ChimeraNBitVM::run(invalid,bad,1)==CHIMERA_NBIT_VM_BAD_PROGRAM);
    puts("Chimera N-bit virtual bytecode runtime passed.");
    return 0;
}
