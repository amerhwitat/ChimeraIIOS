#include <cstdio>
#include <cstring>
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
}
extern "C" int aurora_launch(const char* id,const char* profile){
 for(const auto&a:apps) if(std::strcmp(id,a.id)==0){
  std::printf("Aurora: launch %s (%s) profile=%s\\n",a.id,a.entry,profile?profile:"chimera-modern"); return 0;
 }
 std::fprintf(stderr,"Aurora: application not registered: %s\\n",id?id:"<null>"); return 127;
}
int main(int argc, char** argv) {
 const char* id = (argc > 1) ? argv[1] : "terminal";
 const char* profile = (argc > 2) ? argv[2] : "chimera-modern";
 return aurora_launch(id, profile);
}
