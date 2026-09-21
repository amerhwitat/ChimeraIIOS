#include <stdio.h>
#include "chimera/sdk.h"
int main(void){chimera_runtime_init();printf("Chimera SDK %s (%s)\n",chimera_sdk_version(),chimera_target_triple());chimera_runtime_shutdown();return 0;}
