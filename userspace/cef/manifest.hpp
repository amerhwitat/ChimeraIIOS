#pragma once
#include <cstdint>
#include <string>
#include <unordered_map>
namespace chimera::cef {
struct Manifest { std::string exec; std::unordered_map<std::string,bool> resources; std::unordered_map<std::string,bool> privileges; };
inline bool allowed(const Manifest&m,const std::string&p){auto i=m.privileges.find(p);return i!=m.privileges.end()&&i->second;}
}
