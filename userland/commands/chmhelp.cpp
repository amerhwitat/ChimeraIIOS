#include <iostream>
#include <string>
int main(int argc,char**argv){
 if(argc<2){std::cout<<"Chimera commands: chmctl chm-diagnostics chimera-utils aurora-settings chm-knowledge-daemon chm-resource-manager chm-reboot chm-patch\n";return 0;}
 std::string n=argv[1];
 if(n=="chmctl") std::cout<<"System control gateway. See man chmctl.\n";
 else if(n=="aurora-settings") std::cout<<"Aurora Settings control surface. See man aurora-settings.\n";
 else if(n=="chm-diagnostics") std::cout<<"System diagnostics utility. See man chm-diagnostics.\n";
 else if(n=="chimera-utils") std::cout<<"Portable filesystem/text utilities. See man chimera-utils.\n";
 else if(n=="chm-resource-manager") std::cout<<"Adaptive CPU/memory/I/O background resource governor. See man chm-resource-manager.\n";
 else if(n=="chm-reboot") std::cout<<"User-controlled reboot request manager. See man chm-reboot.\n";
 else std::cout<<"No Chimera manual entry for "<<n<<"\n";
 return 0;
}
