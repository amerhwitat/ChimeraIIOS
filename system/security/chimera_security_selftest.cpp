#include "chimera_identity_store.hpp"
#include <iostream>
#include <sys/stat.h>
using namespace chimera_identity;
int main(){if(!ensure_db()){std::cerr<<"identity database initialization failed\n";return 1;}struct stat s{};if(stat(etc("shadow").c_str(),&s)||((s.st_mode&0777)!=0600)){std::cerr<<"shadow must be 0600\n";return 2;}if(!contains_name(etc("passwd"),"root")||!contains_name(etc("group"),"root")){std::cerr<<"root account/group missing\n";return 3;}std::cout<<"Chimera identity security self-test: PASS\n";return 0;}