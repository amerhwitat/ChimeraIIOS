#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <cstdlib>
namespace fs=std::filesystem;
int main(int argc,char**argv){
 std::string mode=argc>1?argv[1]:"summary";
 if(mode=="summary"){std::cout<<"Chimera diagnostics\nCPU: "<<(std::getenv("PROCESSOR_IDENTIFIER")?std::getenv("PROCESSOR_IDENTIFIER"):"runtime-detected")<<"\n";
  std::cout<<"Kernel: Koronos\nDesktop: Aurora\n"; return 0;}
 if(mode=="mounts"){std::ifstream f("/proc/mounts");std::string s;while(std::getline(f,s))std::cout<<s<<"\n";return 0;}
 if(mode=="devices"){for(const auto& e:fs::directory_iterator("/dev"))std::cout<<e.path().string()<<"\n";return 0;}
 if(mode=="env"){for(const auto& e:fs::directory_iterator("/proc/self/fd"))std::cout<<e.path().string()<<"\n";return 0;}
 std::cout<<"Usage: chm-diagnostics [summary|mounts|devices|env]\n";return 2;
}
