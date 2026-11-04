#include "chimera/hardware.h"
#include <assert.h>
int main(){
    chimera_hardware_profile p{};
    assert(chimera_hardware_probe(&p)==0);
    assert(p.version==CHIMERA_HW_PROFILE_VERSION);
    assert(p.logical_cpus>=1u);
    assert(p.physical_cores>=1u);
    assert(p.threads_per_core>=1u);
    assert(p.physical_cores<=p.logical_cpus);
    if(p.topology_valid){
        assert(p.topology_leaf==0x0Bu||p.topology_leaf==0x1Fu||p.topology_leaf==0x8000001Eu);
        assert(p.logical_cpus>=p.physical_cores*p.threads_per_core);
    }
    return 0;
}
