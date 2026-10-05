#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <unistd.h>

namespace {
struct App { const char* id; const char* entry; };
static const App apps[]={
 {"terminal","userland/shell/chimera-shell"},{"files","desktop/aurora/files"},
 {"settings","desktop/aurora/settings"},{"browser","desktop/aurora/browser"},
 {"process-monitor","desktop/aurora/process-monitor"},{"network-manager","desktop/aurora/network-manager"},
 {"package-center","desktop/aurora/package-center"},{"help-man","tools/help/chimera-help"},
 {"chimera-neural-chat","desktop/aurora/apps/chimera_neural_chat"},
 {"aurora-peripherals","desktop/aurora/apps/aurora_peripherals"},
 {"aurora-settings","desktop/aurora/apps/aurora_settings"},
 {"aurora-media-player","desktop/aurora/apps/aurora_media"},
 {"aurora-video-player","desktop/aurora/apps/aurora_video"},
 {"system-control","userland/commands/chmctl"},{"diagnostics","userland/commands/chm-diagnostics"}
};
static const char* resolve(const char* entry,char* buf,size_t n){
  const char* root=std::getenv("CHIMERA_AURORA_EXEC_ROOT");
  if(root && *root){ std::snprintf(buf,n,"%s/%s",root,entry); if(access(buf,X_OK)==0)return buf; }
  if(access(entry,X_OK)==0)return entry;
  return nullptr;
}
}
extern "C" int aurora_launch(const char* id,const char* profile){
 if(!id) return 2;
 for(const auto&a:apps) if(std::strcmp(id,a.id)==0){
   char path[1024]{};
   const char* exe=resolve(a.entry,path,sizeof(path));
   if(!exe){ std::fprintf(stderr,"Aurora: executable unavailable: %s (%s)\n",a.id,a.entry); return 127; }
   char* const argv[]={const_cast<char*>(exe),nullptr};
   std::printf("Aurora: exec %s (%s) profile=%s\n",a.id,exe,profile?profile:"chimera-modern");
   std::fflush(stdout);
   ::execv(exe,argv);
   std::perror("Aurora: execv");
   return 126;
 }
 std::fprintf(stderr,"Aurora: application not registered: %s\n",id);
 return 127;
}
int main(int argc,char**argv){
 const char* id=argc>1?argv[1]:"terminal";
 const char* profile=argc>2?argv[2]:"chimera-modern";
 return aurora_launch(id,profile);
}
