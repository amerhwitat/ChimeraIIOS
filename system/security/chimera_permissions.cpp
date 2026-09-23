#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
namespace fs=std::filesystem;
static fs::path root(){const char*p=std::getenv("CHIMERA_SYSROOT");return(p&&*p)?fs::path(p):fs::path("");}
static fs::path path(std::string x){if(!x.empty()&&x[0]=='/')return root()/x.substr(1);return root()/x;}
int main(int argc,char**argv){
 if(argc<3){std::cout<<"usage: chm-perms stat PATH | chmod MODE PATH | chown UID:GID PATH\n";return 2;}
 std::string op=argv[1],x=argv[2];fs::path p=path(x);
 if(op=="stat"){struct stat s{};if(::stat(p.c_str(),&s))return 1;std::cout<<"uid="<<s.st_uid<<" gid="<<s.st_gid<<" mode="<<std::oct<<(s.st_mode&07777)<<std::dec<<"\n";return 0;}
 if(geteuid()!=0){std::cerr<<"chm-perms: root privileges required\n";return 77;}
 if(op=="chmod"&&argc>=4){mode_t m=std::strtol(argv[2],nullptr,8);p=path(argv[3]);return ::chmod(p.c_str(),m)?1:0;}
 if(op=="chown"&&argc>=4){auto q=std::string(argv[2]);auto c=q.find(':');if(c==std::string::npos)return 2;uid_t u=std::stoul(q.substr(0,c));gid_t g=std::stoul(q.substr(c+1));p=path(argv[3]);return ::chown(p.c_str(),u,g)?1:0;}
 return 2;
}
