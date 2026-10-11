#include "chimera/nbit_fpu.h"
#include <cassert>
#include <cmath>
#include <cstring>
int main(){
    uint8_t a[8]{},b[8]{},d[8]{};
    float a0=1.5f,a1=-2.0f,b0=2.25f,b1=4.0f;
    std::memcpy(a,&a0,4);std::memcpy(a+4,&a1,4);
    std::memcpy(b,&b0,4);std::memcpy(b+4,&b1,4);
    assert(ChimeraNBitFPU::execute_lanes({d,64,8},{a,64,8},{b,64,8},CHIMERA_NBIT_F32_ADD)==0);
    float r0=0,r1=0;std::memcpy(&r0,d,4);std::memcpy(&r1,d+4,4);
    assert(std::fabs(r0-3.75f)<0.0001f && std::fabs(r1-2.0f)<0.0001f);
    uint8_t shortbuf[7]{};
    assert(ChimeraNBitFPU::execute_lanes({shortbuf,64,7},{a,64,8},{b,64,8},CHIMERA_NBIT_F32_ADD)==-2);
    assert(ChimeraNBitFPU::execute_lanes({d,64,8},{a,64,8},{b,64,8},CHIMERA_NBIT_F64_ADD)==0);
    double da=1.25,db=2.5,dr=0;std::memcpy(a,&da,8);std::memcpy(b,&db,8);
    assert(ChimeraNBitFPU::execute_lanes({d,64,8},{a,64,8},{b,64,8},CHIMERA_NBIT_F64_ADD)==0);
    std::memcpy(&dr,d,8);assert(std::fabs(dr-3.75)<0.0001);
    return 0;
}
