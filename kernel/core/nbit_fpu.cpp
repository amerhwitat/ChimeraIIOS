#include "chimera/nbit_fpu.h"
#include <string.h>

uint32_t ChimeraNBitFPU::lane_bits(ChimeraNBitFloatOpcode op) {
    switch(op) {
    case CHIMERA_NBIT_F32_ADD: case CHIMERA_NBIT_F32_SUB:
    case CHIMERA_NBIT_F32_MUL: case CHIMERA_NBIT_F32_DIV: return 32;
    case CHIMERA_NBIT_F64_ADD: case CHIMERA_NBIT_F64_SUB:
    case CHIMERA_NBIT_F64_MUL: case CHIMERA_NBIT_F64_DIV: return 64;
    default:return 0;
    }
}
int ChimeraNBitFPU::execute_lanes(ChimeraNBitFloatView d,const ChimeraNBitFloatView a,
                                  const ChimeraNBitFloatView b,ChimeraNBitFloatOpcode op) {
    const uint32_t lane=lane_bits(op);
    if(!lane||!d.bytes||!a.bytes||!b.bytes||!d.width_bits||d.width_bits!=a.width_bits||
       a.width_bits!=b.width_bits||d.width_bits%lane) return -1;
    const uint64_t need=((uint64_t)d.width_bits+7u)/8u;
    if(d.capacity_bytes<need||a.capacity_bytes<need||b.capacity_bytes<need)return -2;
    const uint32_t count=d.width_bits/lane;
    if(lane==32) {
        for(uint32_t i=0;i<count;++i) {
            float x,y,z; memcpy(&x,a.bytes+i*4u,4); memcpy(&y,b.bytes+i*4u,4);
            switch(op) { case CHIMERA_NBIT_F32_ADD:z=x+y;break; case CHIMERA_NBIT_F32_SUB:z=x-y;break;
                case CHIMERA_NBIT_F32_MUL:z=x*y;break; default:z=x/y;break; }
            memcpy(d.bytes+i*4u,&z,4);
        }
    } else {
        for(uint32_t i=0;i<count;++i) {
            double x,y,z; memcpy(&x,a.bytes+i*8u,8); memcpy(&y,b.bytes+i*8u,8);
            switch(op) { case CHIMERA_NBIT_F64_ADD:z=x+y;break; case CHIMERA_NBIT_F64_SUB:z=x-y;break;
                case CHIMERA_NBIT_F64_MUL:z=x*y;break; default:z=x/y;break; }
            memcpy(d.bytes+i*8u,&z,8);
        }
    }
    return 0;
}
extern "C" int chimera_nbit_fpu_execute(uint8_t*d,uint32_t dc,const uint8_t*a,uint32_t ac,
 const uint8_t*b,uint32_t bc,uint32_t bits,uint32_t opcode) {
    return ChimeraNBitFPU::execute_lanes({d,bits,dc},{const_cast<uint8_t*>(a),bits,ac},
       {const_cast<uint8_t*>(b),bits,bc},static_cast<ChimeraNBitFloatOpcode>(opcode));
}
