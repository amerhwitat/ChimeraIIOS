#include <iostream>
#include "chimera/RegisterN.hpp"
namespace koronos { void boot(const char*); }
namespace spotnik { void demo(); }
int main(){Reg8192 a(42),b(7);auto c=a+b;std::cout<<"Chimera II host research scaffold\n";std::cout<<"8192-bit register word0="<<c[0]<<"\n";koronos::boot("host-emulated");spotnik::demo();return 0;}
