#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <cstdlib>
namespace fs=std::filesystem;
static bool enabled(){const char*e=std::getenv("CHIMERA_KNOWLEDGE_ENABLE");return e&&std::string(e)=="1";}
static void tick(const fs::path&root){fs::create_directories(root/"inbox");fs::create_directories(root/"normalized");fs::create_directories(root/"columnar");fs::create_directories(root/"proposals");std::ofstream(root/"daemon.status")<<"state=ready\npolicy=staged\nexecute_downloads=false\n";std::cout<<"knowledge: staged pipeline ready at "<<root<<"\n";}
int main(int argc,char**argv){fs::path root=std::getenv("CHIMERA_KNOWLEDGE_ROOT")?std::getenv("CHIMERA_KNOWLEDGE_ROOT"):"/var/lib/chimera/knowledge";if(argc>1&&std::string(argv[1])=="once"){tick(root);return 0;}if(!enabled()){std::cerr<<"knowledge: disabled; set CHIMERA_KNOWLEDGE_ENABLE=1 under administrator policy\n";return 78;}for(;;){tick(root);std::this_thread::sleep_for(std::chrono::hours(24));}}