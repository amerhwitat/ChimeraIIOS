#include <iostream>
#include "chimera/sdk.h"
int main(){chimera_runtime_init();std::cout<<"Chimera SDK "<<chimera_sdk_version()<<" ("<<chimera_target_triple()<<")\n";chimera_runtime_shutdown();}
