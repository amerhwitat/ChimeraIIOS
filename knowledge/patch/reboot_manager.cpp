#include "reboot_manager.hpp"
#include <cstdlib>
#include <fstream>
namespace chm::reboot {
std::filesystem::path state_path(){const char*r=std::getenv("CHIMERA_RUNTIME_ROOT");return(r&&*r?std::filesystem::path(r):std::filesystem::path("/run/chimera"))/"reboot.pending";}
bool save(const Request&r){std::filesystem::create_directories(state_path().parent_path());std::ofstream f(state_path());if(!f)return false;f<<"required="<<(r.required?"true":"false")<<"\nreason="<<r.reason<<"\nartifact="<<r.artifact<<"\n";return true;}
Request load(){Request r;std::ifstream f(state_path());std::string l;while(std::getline(f,l)){auto p=l.find('=');if(p==std::string::npos)continue;auto k=l.substr(0,p),v=l.substr(p+1);if(k=="required")r.required=(v=="true");else if(k=="reason")r.reason=v;else if(k=="artifact")r.artifact=v;}return r;}
bool mark_later(){auto r=load();if(!r.required)return false;r.reason+="; user selected reboot later";return save(r);}
bool clear(){std::error_code ec;return std::filesystem::remove(state_path(),ec)||!std::filesystem::exists(state_path());}
}
