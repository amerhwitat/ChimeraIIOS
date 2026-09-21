#include "chimera/sdk.h"
const char* chimera_sdk_version(void){ return "1.0.0"; }
const char* chimera_target_triple(void){
#if defined(__x86_64__) || defined(_M_X64)
 return "chimera-x86_64";
#elif defined(__aarch64__) || defined(_M_ARM64)
 return "chimera-aarch64";
#elif defined(__riscv) && __riscv_xlen == 64
 return "chimera-riscv64";
#else
 return "chimera-host";
#endif
}
int chimera_runtime_init(void){ return 0; }
void chimera_runtime_shutdown(void){}
