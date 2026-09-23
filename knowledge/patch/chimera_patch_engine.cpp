#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include "reboot_manager.hpp"
namespace fs=std::filesystem;
static bool approved(){const char*e=std::getenv("CHIMERA_PATCH_APPROVED");return e&&std::string(e)=="1";}
int main(int argc,char**argv){
 fs::path root=std::getenv("CHIMERA_KNOWLEDGE_ROOT")?std::getenv("CHIMERA_KNOWLEDGE_ROOT"):"/var/lib/chimera/knowledge";
 if(argc<2){std::cout<<"usage: chm-patch propose|verify|stage|status\n";return 2;}
 std::string op=argv[1];
 if(op=="status"){std::cout<<"patch-engine: staged; privileged auto-deploy disabled\n";auto r=chm::reboot::load();if(r.required)std::cout<<"reboot: user decision pending\n";return 0;}
 if(op=="propose"){fs::create_directories(root/"proposals");std::ofstream(root/"proposals/README")<<"Proposals require isolated build, tests, artifact hash and signature before staging. A reboot-required patch creates a pending user decision; it never silently reboots.\n";return 0;}
 if(op=="verify"){std::cout<<"verification requires project-specific CI artifacts and signature\n";return 0;}
 if(op=="stage"){
   if(!approved()){std::cerr<<"refusing stage: administrator approval is required\n";return 78;}
   const char* rr=std::getenv("CHIMERA_PATCH_REBOOT_REQUIRED");
   if(rr&&std::string(rr)=="1"){
     chm::reboot::Request r{true,"A staged patch requires reboot to activate","pending-artifact"};
     if(!chm::reboot::save(r)){std::cerr<<"could not record reboot request\n";return 2;}
     std::cout<<"patch staged. Reboot is required; user decision is pending. No automatic reboot will occur.\n";
   } else std::cout<<"stage requested; deployment remains policy-controlled\n";
   return 0;
 }
 return 2;
}
