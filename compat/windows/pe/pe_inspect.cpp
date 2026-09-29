#include "pe_loader.h"
#include <cstdio>
using namespace chimera::win::pe;
static const char* machine(Machine m){ switch(m){case Machine::I386:return "x86";case Machine::AMD64:return "x64";case Machine::ARM64:return "ARM64";} return "unknown"; }
int main(int argc,char** argv){
 if(argc!=2){std::fprintf(stderr,"usage: chimera-pe-inspect <file.exe|file.dll>\n");return 2;}
 Image x; std::string e; auto s=inspect(argv[1],x,e); if(s!=Status::Ok){std::fprintf(stderr,"PE error: %s\n",e.c_str());return 1;}
 std::printf("PE: %s\narch: %s\nformat: %s\ntype: %s\nbase: 0x%llx\nentry RVA: 0x%llx\nimage size: 0x%llx\nsections: %zu\nimports: %zu\nexports: %zu\nrelocations: %zu\n",
 argv[1],machine(x.machine),x.pe32_plus?"PE32+":"PE32",x.kind==ImageKind::DLL?"DLL":"EXE",(unsigned long long)x.preferred_base,(unsigned long long)x.entry_rva,(unsigned long long)x.image_size,x.sections.size(),x.imports.size(),x.exports.size(),x.relocation_rvas.size());
 return 0;
}
