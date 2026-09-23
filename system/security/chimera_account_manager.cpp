#include <crypt.h>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <algorithm>
namespace fs=std::filesystem;
static fs::path root(){const char*p=std::getenv("CHIMERA_SYSROOT");return(p&&*p)?fs::path(p):fs::path("");}
static fs::path p(const char*n){return root()/n;}
static bool superuser(){return geteuid()==0;}
static std::string prompt(const char*s){std::cerr<<s;std::string v;std::getline(std::cin,v);return v;}
static bool append_unique(const fs::path&f,const std::string&line,const std::string&key){std::ifstream in(f);std::string x;while(std::getline(in,x))if(x.rfind(key+":",0)==0)return false;std::ofstream out(f,std::ios::app);if(!out)return false;out<<line<<"\n";return true;}
static int next_id(const fs::path&f,int base){std::ifstream in(f);std::string x;int max=base-1;while(std::getline(in,x)){std::stringstream ss(x);std::string a;std::getline(ss,a,':');try{max=std::max(max,std::stoi(a));}catch(...){}}return max+1;}
static bool init_db(){
 fs::create_directories(p("etc"));
 if(!fs::exists(p("etc/passwd")))std::ofstream(p("etc/passwd"))<<"root:x:0:0:root:/root:/bin/chimera-shell\n";
 if(!fs::exists(p("etc/group")))std::ofstream(p("etc/group"))<<"root:x:0:\n";
 if(!fs::exists(p("etc/shadow")))std::ofstream(p("etc/shadow"))<<"root:!:19701:0:99999:7:::\n";
 if(!fs::exists(p("etc/gshadow")))std::ofstream(p("etc/gshadow"))<<"root:!::\n";
 chmod(p("etc/shadow").c_str(),0600);chmod(p("etc/gshadow").c_str(),0600);chmod(p("etc/passwd").c_str(),0644);chmod(p("etc/group").c_str(),0644);return true;
}
static std::string hashpw(const std::string&pw){char salt[64];std::snprintf(salt,sizeof(salt),"$6$chimera-%ld$",static_cast<long>(getpid()));char*h=crypt(pw.c_str(),salt);return h?h:"";}
static int create_user(const std::string&name,bool root_account){
 if(!superuser()){std::cerr<<"chm-user: root privileges required\n";return 77;} init_db();
 if(name.empty()||name.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")!=std::string::npos){std::cerr<<"invalid account name\n";return 2;}
 int uid=root_account?0:next_id(p("etc/passwd"),1000);int gid=root_account?0:next_id(p("etc/group"),1000);
 std::string pw=prompt("New password: ");std::string pw2=prompt("Retype new password: ");if(pw.empty()||pw!=pw2){std::cerr<<"password mismatch or empty password\n";return 2;}
 std::string h=hashpw(pw);if(h.empty()){std::cerr<<"password hashing failed\n";return 2;}
 if(!root_account){
   append_unique(p("etc/group"),name+":x:"+std::to_string(gid)+":",name);
   append_unique(p("etc/passwd"),name+":x:"+std::to_string(uid)+":"+std::to_string(gid)+":"+name+":/home/"+name+":/bin/chimera-shell",name);
   std::ofstream(p("etc/shadow"),std::ios::app)<<name<<":"<<h<<":19701:0:99999:7:::\n";
   std::ofstream(p("etc/gshadow"),std::ios::app)<<name<<":!::\n";fs::create_directories(p("home")/name);
 } else {
   std::ofstream out(p("etc/shadow"),std::ios::trunc);out<<"root:"<<h<<":19701:0:99999:7:::\n";
   std::ofstream(p("etc/passwd"),std::ios::trunc)<<"root:x:0:0:root:/root:/bin/chimera-shell\n";
 }
 chmod(p("etc/shadow").c_str(),0600);chmod(p("etc/gshadow").c_str(),0600);std::cout<<"account created: "<<name<<" uid="<<uid<<" gid="<<gid<<"\n";return 0;
}
int main(int argc,char**argv){
 if(argc<2){std::cout<<"usage: chm-user-setup init|create-root|create-user NAME|files\n";return 2;}
 std::string op=argv[1];if(op=="init"){if(!superuser())return 77;init_db();std::cout<<"account database initialized\n";return 0;}
 if(op=="create-root")return create_user("root",true);
 if(op=="create-user"&&argc>=3)return create_user(argv[2],false);
 if(op=="create-admin"&&argc>=3){int rc=create_user(argv[2],false);if(rc)return rc;std::ofstream g(p("etc/group"),std::ios::app);g<<"chimera-admin:x:998:"<<argv[2]<<"\\n";std::cout<<"administrator role granted through chimera-admin group\\n";return 0;}
 if(op=="files"){std::cout<<p("etc/passwd")<<"\n"<<p("etc/shadow")<<"\n"<<p("etc/group")<<"\n"<<p("etc/gshadow")<<"\n";return 0;}
 return 2;
}
