#include <cassert>
#include <cstdint>
#include <string>
#include "chimera/RegisterN.hpp"
#include "chimera/state128.hpp"
#include "chimera/unified_isa.hpp"
#include "chimera/kernel_arch.hpp"
#include "chimera/nbit_runtime.hpp"
#include "chimera/quantum_bridge.hpp"
int main(){
    chimera::RegisterN<8192>a{};chimera::RegisterN<8192>b{};a.set_u64(0,0xffffffffffffffffULL);b.set_u64(0,1ULL);auto c=a+b;assert(c.lane(0)==0);assert(c.lane(1)==1);
    chimera::State128 s{};s[0]=1.0;s[127]=2.0;auto y=chimera::state_transition(s,s);assert(y[0]==2.0);assert(y[127]==4.0);
    auto rv=chimera::isa::decode_riscv64(0x003100b3u);assert(rv.valid);assert(rv.instruction.rd==1&&rv.instruction.rs1==2&&rv.instruction.rs2==3);assert(rv.instruction.mnemonic=="add");
    const uint8_t syscall[]={0x0f,0x05};auto x86=chimera::isa::decode_x86_64(syscall,sizeof(syscall));assert(x86.valid&&x86.instruction.mnemonic=="syscall");
    chimera::kernel::Scheduler sched;chimera::kernel::Task task{42,0,0,1,chimera::kernel::TaskState::Ready};sched.enqueue(&task);assert(sched.pick_next()==&task);
    using chimera::runtime::Width;chimera::runtime::Runtime rt({16384,true,false,true});assert(rt.switch_mode(chimera::runtime::ExecutionMode::NativeWide,Width{8192}));std::uint64_t one[]={~0ULL};std::uint64_t two[]={1ULL};chimera::runtime::WideInt wa{Width{8192},one};chimera::runtime::WideInt wb{Width{8192},two};auto wc=chimera::runtime::WideInt::add(wa,wb);assert(wc.limbs()[0]==0&&wc.limbs()[1]==1);assert(rt.switch_mode(chimera::runtime::ExecutionMode::QuantumHybrid,Width{256}));
    chimera::quantum::Circuit circuit(2);circuit.append({chimera::quantum::Gate::H,0,0});circuit.append({chimera::quantum::Gate::CNOT,0,1});assert(circuit.operations().size()==2);return 0;
}
