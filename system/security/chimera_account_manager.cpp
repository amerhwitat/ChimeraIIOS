#include "chimera_identity_store.hpp"
#include <iostream>
#include <sstream>
#include <string>
using namespace chimera_identity;
static std::string prompt(const char* s){std::cerr<<s;std::string v;std::getline(std::cin,v);return v;}
static bool gethash(std::string& h){std::string a=prompt("New password: "),b=prompt("Retype new password: ");if(a.empty()||a!=b)return false;h=hash_password(a);return !h.empty();}
static int create_user(const std::string& n,bool root_account){
 if(!privileged()||!ensure_db()||!valid_name(n))return 2;std::string h;if(!gethash(h))return 2;
 if(root_account){std::string pass,sh;if(!read_all(etc("passwd"),pass)||!read_all(etc("shadow"),sh))return 1;std::istringstream ps(pass),ss(sh);std::string l,np,ns;bool pf=false,sf=false;
  while(std::getline(ps,l)){if(l.rfind("root:",0)==0){l="root:x:0:0:root:/root:/bin/chimera-shell";pf=true;}np+=l+"\n";}
  while(std::getline(ss,l)){if(l.rfind("root:",0)==0){l="root:"+h+":19701:0:99999:7:::";sf=true;}ns+=l+"\n";}
  if(!pf)np+="root:x:0:0:root:/root:/bin/chimera-shell\n";if(!sf)ns+="root:"+h+":19701:0:99999:7:::\n";
  Lock a(etc("passwd"));if(!a||!atomic_write(etc("passwd"),np,0644)||!atomic_write(etc("shadow"),ns,0600))return 1;std::cout<<"root password initialized without removing other accounts\n";return 0;}
 if(contains_name(etc("passwd"),n))return 9;int uid=next_id(etc("passwd"),1000),gid=next_id(etc("group"),1000);
 if(!append_locked(etc("group"),n+":x:"+std::to_string(gid)+":\n",0644)||!append_locked(etc("passwd"),n+":x:"+std::to_string(uid)+":"+std::to_string(gid)+":"+n+":/home/"+n+":/bin/chimera-shell\n",0644)||!append_locked(etc("shadow"),n+":"+h+":19701:0:99999:7:::\n",0600)||!append_locked(etc("gshadow"),n+":!::\n",0600))return 1;
 std::filesystem::create_directories(root()/"home"/n);chmod((root()/"home"/n).c_str(),0700);std::cout<<"account created: "<<n<<" uid="<<uid<<" gid="<<gid<<"\n";return 0;}
int main(int argc,char**argv){if(argc<2){std::cout<<"usage: chm-user-setup init|create-root|create-user NAME|create-admin NAME|files\n";return 2;}std::string op=argv[1];if(op=="init"){if(!privileged())return 77;return ensure_db()?0:1;}if(op=="create-root")return create_user("root",true);if((op=="create-user"||op=="create-admin")&&argc>=3){int rc=create_user(argv[2],false);if(rc)return rc;if(op=="create-admin"){if(!contains_name(etc("group"),"chimera-admin")){int gid=next_id(etc("group"),998);if(gid<998)gid=998;append_locked(etc("group"),"chimera-admin:x:"+std::to_string(gid)+":"+std::string(argv[2])+"\n",0644);}else{std::string g;read_all(etc("group"),g);std::istringstream in(g);std::string l,out;while(std::getline(in,l)){if(l.rfind("chimera-admin:",0)==0&&l.find(argv[2])==std::string::npos)l+=","+std::string(argv[2]);out+=l+"\n";}atomic_write(etc("group"),out,0644);}std::cout<<"administrator role granted through chimera-admin\n";}return 0;}if(op=="files"){std::cout<<etc("passwd")<<"\n"<<etc("shadow")<<"\n"<<etc("group")<<"\n"<<etc("gshadow")<<"\n";return 0;}return 2;}