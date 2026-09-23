#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>
#include <sys/stat.h>
namespace fs=std::filesystem;
static fs::path r(){const char*p=std::getenv("CHIMERA_SYSROOT");return(p&&*p)?fs::path(p):fs::path("");}
static fs::path g(){return r()/"etc/group";} static fs::path gs(){return r()/"etc/gshadow";}
static int next(){std::ifstream in(g());std::string x;int m=999;while(std::getline(in,x)){auto p=x.find(':');auto q=x.find(':',p+1);try{m=std::max(m,std::stoi(x.substr(p+1,q-p-1)));}catch(...){}}return m+1;}
int main(int argc,char**argv){if(geteuid()!=0){std::cerr<<"groupadd: root privileges required\n";return 77;}if(argc<2){std::cerr<<"usage: groupadd GROUP\n";return 2;}std::string n=argv[1];std::ifstream in(g());std::string x;while(std::getline(in,x))if(x.rfind(n+":",0)==0)return 9;int id=next();std::ofstream o(g(),std::ios::app);o<<n<<":x:"<<id<<":\n";std::ofstream s(gs(),std::ios::app);s<<n<<":!::\n";chmod(gs().c_str(),0600);std::cout<<"group created: "<<n<<" gid="<<id<<"\n";return 0;}
