#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
namespace fs=std::filesystem;
static bool enabled(){const char*e=std::getenv("CHIMERA_KNOWLEDGE_ENABLE");return e&&std::string(e)=="1";}
static double psi(const char* resource){
 std::ifstream f(std::string("/proc/pressure/")+resource); std::string line;
 if(!f||!std::getline(f,line)) return -1; auto p=line.find("avg10="); if(p==std::string::npos)return -1;p+=6;auto e=line.find(' ',p);
 try{return std::stod(line.substr(p,e-p));}catch(...){return -1;}
}
static void tick(const fs::path&root){
 fs::create_directories(root/"inbox");fs::create_directories(root/"normalized");fs::create_directories(root/"columnar");fs::create_directories(root/"proposals");fs::create_directories(root/"cache");
 bool pressure=psi("memory")>=10.0||psi("io")>=10.0||psi("cpu")>=15.0;
 std::ofstream(root/"daemon.status")<<"state="<<(pressure?"paused-under-pressure":"ready")<<"\npolicy=staged\nexecute_downloads=false\nmemory_cache=disk-first-bounded\ncontent_in_memory=false\n";
 std::cout<<"knowledge: "<<(pressure?"paused under resource pressure":"background window available")<<" at "<<root<<"\n";
}
int main(int argc,char**argv){
 fs::path root=std::getenv("CHIMERA_KNOWLEDGE_ROOT")?std::getenv("CHIMERA_KNOWLEDGE_ROOT"):"/var/lib/chimera/knowledge";
 if(argc>1&&std::string(argv[1])=="once"){tick(root);return 0;}
 if(!enabled()){std::cerr<<"knowledge: disabled; set CHIMERA_KNOWLEDGE_ENABLE=1 under administrator policy\n";return 78;}
 for(;;){tick(root);std::this_thread::sleep_for(std::chrono::hours(24));}
}
