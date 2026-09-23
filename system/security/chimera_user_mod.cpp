#include "chimera_identity_store.hpp"
#include <iostream>
#include <sstream>
using namespace chimera_identity;
static bool rewrite(const std::string& u,const std::string& v,int idx){std::string in;if(!read_all(etc("passwd"),in))return false;std::istringstream s(in);std::string l,out;bool f=false;while(std::getline(s,l)){std::stringstream p(l);std::string a[7];int n=0;while(n<7&&std::getline(p,a[n],':'))++n;if(n==7&&a[0]==u){a[idx]=v;l="";for(int i=0;i<7;i++){if(i)l+=':';l+=a[i];}f=true;}out+=l+"\n";}return f&&atomic_write(etc("passwd"),out,0644);}
int main(int c,char**v){if(!privileged()||c<4){std::cerr<<"usage: chm-usermod USER --shell PATH|--home PATH|--gid GID\n";return 2;}if(!ensure_db()||!valid_name(v[1]))return 2;std::string o=v[2];if(o=="--shell")return rewrite(v[1],v[3],6)?0:1;if(o=="--home")return rewrite(v[1],v[3],5)?0:1;if(o=="--gid"){try{if(std::stoi(v[3])<0)return 2;}catch(...){return 2;}return rewrite(v[1],v[3],3)?0:1;}return 2;}