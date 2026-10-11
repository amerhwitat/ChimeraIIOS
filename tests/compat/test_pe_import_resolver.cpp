#include "pe_loader.h"
#include <cassert>
#include <cstdint>
#include <cstring>
using namespace chimera::win::pe;
static bool resolve(const char* dll,const char* symbol,std::uint16_t ordinal,bool by_ordinal,std::uint64_t* address,void*) {
    if(!dll||std::strcmp(dll,"KERNEL32.dll")!=0||by_ordinal||!symbol||std::strcmp(symbol,"CreateFileW")!=0)return false;
    (void)ordinal; *address=0x123456789abcdef0ull; return true;
}
int main(){
    LoadedImage image{}; image.image.pe32_plus=true; image.memory.resize(64);
    image.image.imports.push_back({"KERNEL32.dll","CreateFileW",0,false,16});
    std::string error;
    assert(resolve_imports(image,resolve,nullptr,error)==Status::Ok);
    std::uint64_t value=0;std::memcpy(&value,image.memory.data()+16,8);
    assert(value==0x123456789abcdef0ull);
    LoadedImage unresolved{};unresolved.image.pe32_plus=true;unresolved.memory.resize(64);
    unresolved.image.imports.push_back({"KERNEL32.dll","Missing",0,false,16});
    assert(resolve_imports(unresolved,resolve,nullptr,error)==Status::ImportUnresolved);
    LoadedImage invalid{};invalid.image.pe32_plus=true;invalid.memory.resize(16);
    invalid.image.imports.push_back({"KERNEL32.dll","CreateFileW",0,false,15});
    assert(resolve_imports(invalid,resolve,nullptr,error)==Status::InvalidDirectory);
    return 0;
}
