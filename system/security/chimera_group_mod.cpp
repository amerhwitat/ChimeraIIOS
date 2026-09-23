#include "chimera_identity_store.hpp"
#include <iostream>
#include <sstream>
using namespace chimera_identity;
int main(int c,char**v){if(!privileged()||c<4){std::cerr<<"usage: chm-groupmod GROUP --gid GID|--members LIST\n";return 2;}if(!ensure_db())return 1;std::string in;if(!read_all(etc("group"),in))return 1;std::istringstream s(in);std::string l,out;bool f=false;while(std::getline(s,l)){std::stringstream p(l);std::string a[4];int n=0;while(n<4&&std::getline(p,a[n],':'))++n;if(n==4&&a[0]==v[1]){if(std::string(v[2])=="--gid")a[2]=v[3];else if(std::string(v[2])=="--members")a[3]=v[3];else return 2;l=a[0]+":"+a[1]+":"+a[2]+":"+a[3];f=true;}out+=l+"\n";}return f&&atomic_write(etc("group"),out,0644)?0:1;}