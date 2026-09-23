#include <crypt.h>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>
#include <sys/stat.h>
namespace fs=std::filesystem;
static fs::path f(){const char*r=std::getenv("CHIMERA_SYSROOT");return (r&&*r?fs::path(r):fs::path(""))/"etc/shadow";}
static std::string pw(){std::string a,b;std::cerr<<"New password: ";std::getline(std::cin,a);std::cerr<<"Retype new password: ";std::getline(std::cin,b);if(a.empty()||a!=b)return {};char salt[64];std::snprintf(salt,sizeof(salt),"$6$chimera-%ld$",static_cast<long>(getpid()));char*h=crypt(a.c_str(),salt);return h?h:"";}
int main(int argc,char**argv){if(geteuid()!=0){std::cerr<<"passwd: root privileges required\n";return 77;}if(argc<2){std::cerr<<"usage: passwd USER\n";return 2;}std::string u=argv[1],h=pw();if(h.empty()){std::cerr<<"password rejected\n";return 2;}std::ifstream in(f());std::string line,out;bool found=false;while(std::getline(in,line)){auto p=line.find(':');if(p!=std::string::npos&&line.substr(0,p)==u){auto q=line.find(':',p+1);line=u+":"+h+(q==std::string::npos?":19701:0:99999:7::":line.substr(q));found=true;}out+=line+"\n";}if(!found)return 1;std::ofstream o(f());o<<out;o.close();chmod(f().c_str(),0600);std::cout<<"password updated for "<<u<<"\n";return 0;}
