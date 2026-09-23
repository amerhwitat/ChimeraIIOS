#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>

namespace fs = std::filesystem;

static double psi_some(const char* resource) {
    std::ifstream f(std::string("/proc/pressure/") + resource);
    std::string line;
    if (!f || !std::getline(f, line)) return -1.0;
    auto p=line.find("avg10=");
    if (p==std::string::npos) return -1.0;
    p+=6; auto e=line.find(' ',p);
    try { return std::stod(line.substr(p,e-p)); } catch (...) { return -1.0; }
}
static unsigned cpus() {
    const char* p=std::getenv("CHIMERA_CPU_COUNT");
    if(p&&*p) return std::max(1u,(unsigned)std::strtoul(p,nullptr,10));
    return std::max(1u,std::thread::hardware_concurrency());
}
static void write_state(const fs::path& root, int budget) {
    fs::create_directories(root);
    std::ofstream(root/"resource.state")
      <<"cpu_count="<<cpus()<<"\n"
      <<"background_budget_percent="<<budget<<"\n"
      <<"cpu_psi_some="<<psi_some("cpu")<<"\n"
      <<"memory_psi_some="<<psi_some("memory")<<"\n"
      <<"io_psi_some="<<psi_some("io")<<"\n";
}
int main(int argc,char**argv){
    fs::path root=std::getenv("CHIMERA_RESOURCE_ROOT")?std::getenv("CHIMERA_RESOURCE_ROOT"):"/run/chimera";
    int budget=80;
    if(argc>1 && std::string(argv[1])=="once") { write_state(root,budget); return 0; }
    std::cout<<"resource-manager: opportunistic mode; interactive workloads retain priority\n";
    for(;;){
        double c=psi_some("cpu"),m=psi_some("memory"),i=psi_some("io");
        bool pressured=(c>=15.0)||(m>=10.0)||(i>=10.0);
        int effective=pressured?10:budget;
        write_state(root,effective);
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
}
