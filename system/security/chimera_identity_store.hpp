#pragma once
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <sys/file.h>
#include <sys/random.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <crypt.h>
namespace chimera_identity { namespace fs=std::filesystem;
inline fs::path root(){ const char* v=getenv("CHIMERA_SYSROOT"); return (v&&*v)?fs::path(v):fs::path(""); }
inline fs::path etc(const char* n){return root()/"etc"/n;}
inline bool privileged(){return geteuid()==0;}
inline bool valid_name(const std::string& n){if(n.empty()||n.size()>32||n[0]=='-'||n[0]=='.')return false;for(char c:n)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-'||c=='.'))return false;return true;}
struct Lock{int fd=-1;explicit Lock(const fs::path& p){fs::create_directories(p.parent_path());fd=open((p.string()+".lock").c_str(),O_CREAT|O_RDWR|O_CLOEXEC,0600);if(fd>=0&&flock(fd,LOCK_EX)!=0){close(fd);fd=-1;}}~Lock(){if(fd>=0){flock(fd,LOCK_UN);close(fd);}}explicit operator bool()const{return fd>=0;}};
inline bool atomic_write(const fs::path& d,const std::string& s,mode_t mode){fs::create_directories(d.parent_path());fs::path t=d;t+=".new."+std::to_string(getpid());int fd=open(t.c_str(),O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC,mode);if(fd<0)return false;const char*p=s.data();size_t n=s.size();while(n){ssize_t w=write(fd,p,n);if(w<0){if(errno==EINTR)continue;close(fd);unlink(t.c_str());return false;}p+=w;n-=static_cast<size_t>(w);}fsync(fd);fchmod(fd,mode);close(fd);if(rename(t.c_str(),d.c_str())){unlink(t.c_str());return false;}return true;}
inline bool ensure_db(){fs::create_directories(root()/"etc");fs::create_directories(root()/"root");if(!fs::exists(etc("passwd"))&&!atomic_write(etc("passwd"),"root:x:0:0:root:/root:/bin/chimera-shell\n",0644))return false;if(!fs::exists(etc("group"))&&!atomic_write(etc("group"),"root:x:0:\n",0644))return false;if(!fs::exists(etc("shadow"))&&!atomic_write(etc("shadow"),"root:!:19701:0:99999:7:::\n",0600))return false;if(!fs::exists(etc("gshadow"))&&!atomic_write(etc("gshadow"),"root:!::\n",0600))return false;chmod(etc("shadow").c_str(),0600);chmod(etc("gshadow").c_str(),0600);return true;}
inline std::string salt(){unsigned char b[18];if(getrandom(b,sizeof(b),0)!=(ssize_t)sizeof(b)){for(size_t i=0;i<sizeof(b);++i)b[i]=static_cast<unsigned char>(getpid()+i*31);}static const char h[]="0123456789abcdef";std::string s="$6$chimera-";for(auto x:b){s+=h[x>>4];s+=h[x&15];}return s+"$";}
inline std::string hash_password(const std::string& p){std::string s=salt();char* h=crypt(p.c_str(),s.c_str());return h?h:"";}
inline bool read_all(const fs::path& p,std::string& o){std::ifstream f(p);if(!f)return false;std::ostringstream s;s<<f.rdbuf();o=s.str();return true;}
inline bool contains_name(const fs::path& p,const std::string& n){std::ifstream f(p);std::string l;while(std::getline(f,l)){auto q=l.find(':');if(q!=std::string::npos&&l.substr(0,q)==n)return true;}return false;}
inline int next_id(const fs::path& p,int base){std::ifstream f(p);std::string l;int m=base-1;while(std::getline(f,l)){auto a=l.find(':'),b=l.find(':',a+1);if(a==std::string::npos||b==std::string::npos)continue;try{m=std::max(m,std::stoi(l.substr(a+1,b-a-1)));}catch(...){}}return m+1;}
inline bool append_locked(const fs::path& p,const std::string& add,mode_t mode){Lock l(p);if(!l)return false;std::string old;if(fs::exists(p)&&!read_all(p,old))return false;return atomic_write(p,old+add,mode);}
}