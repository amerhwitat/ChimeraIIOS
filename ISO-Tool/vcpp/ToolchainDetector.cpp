#include "ToolchainDetector.hpp"
#include <filesystem>
#include <sstream>
#include <windows.h>
namespace fs=std::filesystem;
namespace iso_tool {
static std::string where(const std::string& exe){char b[32768]{};DWORD n=SearchPathA(nullptr,exe.c_str(),nullptr,sizeof(b),b,nullptr);return n&&n<sizeof(b)?std::string(b,n):std::string{};}
std::vector<ToolchainResult> DetectToolchains(){const struct{const char*n;const char*e;const char*v;} t[]={{"GCC/MinGW","gcc.exe","MINGW_HOME"},{"G++","g++.exe","MINGW_HOME"},{"MSVC","cl.exe","MSVC_HOME"},{"NASM","nasm.exe","NASM_HOME"},{"MASM","ml.exe","MASM_HOME"},{"Go","go.exe","GOROOT"},{"Rust","rustc.exe","RUST_HOME"},{"Java","javac.exe","JAVA_HOME"},{"Python","python.exe","PYTHON_HOME"},{"Clang","clang.exe","LLVM_HOME"},{"CMake","cmake.exe","CMAKE_HOME"},{"Ninja","ninja.exe","NINJA_HOME"},{"MSBuild","MSBuild.exe","MSBUILD_HOME"},{"Git","git.exe","GIT_HOME"},{"xorriso","xorriso.exe","XORRISO_HOME"},{"Oscdimg","oscdimg.exe","OSCDIMG_HOME"}};std::vector<ToolchainResult> o;for(auto&x:t){auto p=where(x.e);o.push_back({x.n,x.e,x.v,p,p.empty()?"not-found":"found"});}return o;}
std::string ToolchainsJson(){std::ostringstream o;o<<"{\"platform\":\"windows\",\"tools\":[";bool f=true;for(auto&t:DetectToolchains()){if(!f)o<<',';f=false;o<<"{\"name\":\""<<t.name<<"\",\"executable\":\""<<t.executable<<"\",\"environmentVariable\":\""<<t.environment<<"\",\"status\":\""<<t.status<<"\",\"executablePath\":\""<<t.path<<"\"}";}return o.str()+"]}";}
}
