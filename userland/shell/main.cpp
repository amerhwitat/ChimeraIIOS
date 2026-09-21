#include "chimera_shell.hpp"
#include <cstdio>
#include <cstring>
#include <cstdlib>
int main(int argc,char**argv){
 chimera::shell::Dialect d=chimera::shell::Dialect::Chimera;
 if(argc>1&&std::strcmp(argv[1],"--bash")==0)d=chimera::shell::Dialect::Bash;
 chimera::shell::CommandContext c{std::getenv("PWD")?std::getenv("PWD"):"/","user",std::getenv("HOME")?std::getenv("HOME"):"/home/user",std::getenv("PATH")?std::getenv("PATH"):"",0,0,true,false};
 char out[8192],line[4096];
 while(std::fputs("chimera$ ",stdout),std::fflush(stdout),std::fgets(line,sizeof(line),stdin)){
  if(std::strncmp(line,"exit",4)==0)break;
  int rc=chimera::shell::execute_line(c,d,line,out,sizeof(out)); std::fputs(out,stdout);
  if(rc && std::getenv("CHIMERA_SHELL_DEBUG")) std::fprintf(stderr,"[exit=%d]\n",rc);
 }
 return 0;
}
