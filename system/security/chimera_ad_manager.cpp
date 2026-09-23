#include <cstdlib>
#include <iostream>
#include <string>
#include <filesystem>
namespace fs=std::filesystem;
static fs::path root(){const char*p=std::getenv("CHIMERA_SYSROOT");return(p&&*p)?fs::path(p):fs::path("");}
int main(int argc,char**argv){
 if(argc<2){std::cout<<"usage: chm-ad status|config|join|leave|users|groups\n";return 2;}
 std::string op=argv[1];
 if(op=="status"){std::cout<<"AD client: SSSD/winbind provider architecture; domain join is administrator-controlled.\n";return 0;}
 if(op=="config"){std::cout<<"providers: sssd, winbind\nprotocols: LDAP, Kerberos, SMB\nconfig root: "<<root()/"etc/chimera/ad.conf"<<"\n";return 0;}
 if(op=="join"){std::cerr<<"AD join requires administrator-supplied domain, controller discovery, join credentials and explicit confirmation. Credentials are not accepted as command-line arguments.\n";return 78;}
 if(op=="leave"){std::cerr<<"AD leave requires administrator confirmation and provider-specific cleanup.\n";return 78;}
 if(op=="users"||op=="groups"){std::cout<<"Directory enumeration is delegated to the configured SSSD/winbind provider.\n";return 0;}
 return 2;
}
