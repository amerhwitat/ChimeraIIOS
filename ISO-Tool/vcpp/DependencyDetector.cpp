#include "DependencyDetector.hpp"
#include <sstream>
#include <array>
#ifdef _WIN32
#include <windows.h>
#endif
namespace iso_tool { static std::string findCommand(const std::string& c){
#ifdef _WIN32
 char b[MAX_PATH]{}; DWORD n=SearchPathA(nullptr,c.c_str(),nullptr,MAX_PATH,b,nullptr); return n?std::string(b,n):std::string{};
#else
 std::string q="command -v "+c+" 2>/dev/null"; std::array<char,512>b{}; FILE*f=popen(q.c_str(),"r"); if(!f)return{}; std::string s;if(fgets(b.data(),b.size(),f))s=b.data();pclose(f);while(!s.empty()&&(s.back()=='\n'||s.back()=='\r'))s.pop_back();return s;
#endif
}
std::vector<Dependency> DetectDependencies(){const std::vector<Dependency> specs={{"git",{"git"},true,"source"},{"python",{"python","python3"},true,"runtime"},{"cmake",{"cmake"},true,"build"},{"gcc",{"gcc"},false,"compiler"},{"g++",{"g++"},false,"compiler"},{"msvc",{"cl"},false,"compiler"},{"clang",{"clang"},false,"compiler"},{"lld",{"lld"},false,"linker"},{"nasm",{"nasm"},false,"assembler"},{"masm",{"ml","ml64"},false,"assembler"},{"ninja",{"ninja"},false,"build"},{"msbuild",{"msbuild"},false,"build"},{"xorriso",{"xorriso","xorrisofs"},false,"image"},{"oscdimg",{"oscdimg"},false,"image"},{"qemu",{"qemu-system-x86_64"},false,"verification"},{"java",{"java"},false,"runtime"},{"javac",{"javac"},false,"compiler"},{"dotnet",{"dotnet"},false,"runtime"},{"node",{"node"},false,"runtime"},{"go",{"go"},false,"compiler"},{"rustc",{"rustc"},false,"compiler"},{"7zip",{"7z","7zz"},false,"archive"}};auto out=specs;for(auto&d:out){for(auto&c:d.commands){d.path=findCommand(c);if(!d.path.empty()){d.status="found";break;}}if(d.status.empty())d.status="missing";}return out;}
std::string DependenciesJson(const std::vector<Dependency>&ds){std::ostringstream o;o<<"{\"dependencies\":[";for(size_t i=0;i<ds.size();++i){if(i)o<<',';o<<"{\"name\":\""<<ds[i].name<<"\",\"required\":"<<(ds[i].required?"true":"false")<<",\"status\":\""<<ds[i].status<<"\",\"path\":\""<<ds[i].path<<"\"}";}o<<"]}";return o.str();}}
