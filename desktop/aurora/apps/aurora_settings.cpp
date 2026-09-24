#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <filesystem>
namespace fs=std::filesystem;

struct Setting { std::string key, label, value, description; };

static fs::path config_path() {
    if (const char* p=std::getenv("CHIMERA_SETTINGS_FILE"); p && *p) return p;
    if (const char* h=std::getenv("HOME"); h && *h) return fs::path(h)/".config/chimera/settings.conf";
    return "/etc/chimera/settings.conf";
}
static std::vector<Setting> defaults() {
    return {
      {"system.theme","Theme","glass","Aurora visual theme"},
      {"system.accent","Accent","auto","Accent policy"},
      {"display.scale","Display scale","100","Logical display scale percent"},
      {"display.refresh","Refresh","auto","Display refresh policy"},
      {"input.primary_button","Primary mouse button","left","left/right"},
      {"input.natural_scroll","Natural scrolling","true","Pointer/touchpad scrolling"},
      {"input.keyboard_layout","Keyboard layout","US","Active keyboard layout"},
      {"language.locale","Locale","en-US","BCP-47 user locale"},
      {"language.direction","Direction","auto","auto/ltr/rtl"},
      {"privacy.camera","Camera access","ask","ask/allow/deny"},
      {"privacy.microphone","Microphone access","ask","ask/allow/deny"},
      {"network.mode","Network mode","managed","managed/manual"},
      {"services.policy","Service policy","managed","managed/manual"},
      {"updates.policy","Updates","notify","notify/automatic/manual"},
      {"developer.mode","Developer mode","false","Developer facilities"},
      {"performance.background","Background resource mode","opportunistic","Use idle CPU/RAM/I/O without starving interactive work"},
      {"performance.knowledge_cache","Knowledge cache","disk-first","Keep content on disk; bound metadata cache in RAM"},
      {"updates.reboot_policy","Reboot policy","ask","ask/later/now; patches never reboot silently"},
      {"isa.nbit.width","N-bit ISA width","8192","Live Chimera ISA register width; changes do not reboot services"},
      {"isa.nbit.style","N-bit ISA style","RISC","RISC/CISC/HYBRID live execution profile"},
      {"isa.execution.mode","ISA execution mode","NativeWide","Scalar/Vector/NativeWide/JIT/QuantumHybrid"},
      {"neural.dimensions","Neural representation dimensions","1024","Live deep-learning dimensionality; 128D baseline, higher dimensions enabled"},
      {"neural.representation","Neural representation","HyperDimensional","HyperDimensional/Tensor/Hybrid"},
      {"neural.learning","Neural learning mode","AdaptiveTensor","Adaptive multidimensional tensor representation"}
    };
}
static std::vector<Setting> load() {
    auto v=defaults(); std::ifstream f(config_path()); std::string line;
    while(std::getline(f,line)) {
        auto eq=line.find('='); if(eq==std::string::npos) continue;
        auto key=line.substr(0,eq), value=line.substr(eq+1);
        for(auto& s:v) if(s.key==key) s.value=value;
    }
    return v;
}
static bool save(const std::vector<Setting>& v) {
    std::error_code ec; fs::create_directories(config_path().parent_path(),ec);
    std::ofstream f(config_path()); if(!f) return false;
    f<<"# Chimera II OS Aurora settings\n";
    for(const auto& s:v) f<<s.key<<"="<<s.value<<"\n";
    return true;
}
static void usage() {
    std::cout<<"Aurora Settings — Chimera II OS\n"
             <<"Usage: aurora-settings [list|show KEY|set KEY VALUE|reset|category CATEGORY]\n";
}
int main(int argc,char** argv) {
    auto v=load();
    if(argc<2 || std::string(argv[1])=="list") {
        for(const auto&s:v) std::cout<<s.key<<"\t"<<s.value<<"\t"<<s.description<<"\n";
        return 0;
    }
    std::string cmd=argv[1];
    if(cmd=="show" && argc>=3) {
        for(const auto&s:v) if(s.key==argv[2]) { std::cout<<s.key<<"="<<s.value<<"\n"; return 0; }
        return 1;
    }
    if(cmd=="set" && argc>=4) {
        for(auto&s:v) if(s.key==argv[2]) { s.value=argv[3]; if(save(v)){std::cout<<"Applied: "<<s.key<<"="<<s.value<<"\n";return 0;} return 2; }
        std::cerr<<"Unknown setting: "<<argv[2]<<"\n"; return 1;
    }
    if(cmd=="reset") {
        v=defaults(); if(save(v)){std::cout<<"Aurora settings reset to defaults.\n";return 0;} return 2;
    }
    if(cmd=="category" && argc>=3) {
        const std::string c=argv[2];
        for(const auto&s:v) if(s.key.rfind(c+".",0)==0) std::cout<<s.key<<"="<<s.value<<"\n";
        return 0;
    }
    usage(); return 2;
}
