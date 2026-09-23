#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
namespace fs=std::filesystem;
static bool approved(){const char*e=std::getenv("CHIMERA_PATCH_APPROVED");return e&&std::string(e)=="1";}
int main(int argc,char**argv){fs::path root=std::getenv("CHIMERA_KNOWLEDGE_ROOT")?std::getenv("CHIMERA_KNOWLEDGE_ROOT"):"/var/lib/chimera/knowledge";if(argc<2){std::cout<<"usage: chm-patch propose|verify|stage|status\n";return 2;}std::string op=argv[1];if(op=="status"){std::cout<<"patch-engine: staged; privileged auto-deploy disabled\n";return 0;}if(op=="propose"){fs::create_directories(root/"proposals");std::ofstream(root/"proposals/README")<<"Proposals require isolated build, tests, artifact hash and signature before staging.\n";std::cout<<"patch proposal workspace created\n";return 0;}if(op=="verify"){std::cout<<"verification requires project-specific CI artifacts and signature\n";return 0;}if(op=="stage"){if(!approved()){std::cerr<<"refusing stage: administrator approval is required\n";return 78;}std::cout<<"stage requested; deployment remains policy-controlled\n";return 0;}return 2;}