#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <filesystem>
#include <cstring>
#if defined(__unix__) || defined(__APPLE__)
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#endif
namespace fs=std::filesystem;

struct Setting { std::string key, label, value, description; };

static fs::path config_path() {
    if (const char* p=std::getenv("CHIMERA_SETTINGS_FILE"); p && *p) return p;
    if (const char* h=std::getenv("HOME"); h && *h) return fs::path(h)/".config/chimera/settings.conf";
    return "/etc/chimera/settings.conf";
}
static fs::path nbit_profile_path() {
    if (const char* p=std::getenv("CHIMERA_NBIT_PROFILE_FILE"); p && *p) return p;
    if (const char* h=std::getenv("HOME"); h && *h) return fs::path(h)/".config/chimera/nbit-mode.json";
    return "/etc/chimera/nbit-mode.json";
}
static bool notify_nbitd(uint32_t width,const std::string& backend,
                           const std::string& guest,const std::string& personality) {
#if defined(__unix__) || defined(__APPLE__)
    const char* configured=std::getenv("CHIMERA_NBIT_SOCKET");
    const char* path=(configured&&*configured)?configured:"/run/chimera/nbitd.sock";
    const int fd=::socket(AF_UNIX,SOCK_STREAM,0); if(fd<0)return false;
    sockaddr_un addr{}; addr.sun_family=AF_UNIX;
    if(std::strlen(path)>=sizeof(addr.sun_path)){::close(fd);return false;}
    std::strncpy(addr.sun_path,path,sizeof(addr.sun_path)-1);
    if(::connect(fd,reinterpret_cast<sockaddr*>(&addr),sizeof(addr))!=0){::close(fd);return false;}
    std::ostringstream request;
    request<<"{\"op\":\"set\",\"bits\":"<<width
           <<",\"backend\":\""<<backend<<"\",\"isa\":\""<<guest<<"\"";
    if(backend=="compatibility")request<<",\"compatibility\":\""<<personality<<"\"";
    request<<"}\n";const std::string bytes=request.str();
    std::size_t sent=0;
    while(sent<bytes.size()){const auto n=::write(fd,bytes.data()+sent,bytes.size()-sent);if(n<=0){::close(fd);return false;}sent+=static_cast<std::size_t>(n);}
    char response[1024]{};const auto got=::read(fd,response,sizeof(response)-1);::close(fd);
    return got>0&&std::strstr(response,"\"ok\":true")!=nullptr;
#else
    (void)width;(void)backend;(void)guest;(void)personality;return false;
#endif
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
      {"services.enterprise.install_policy","Enterprise services","manual","manual/selected; optional services require explicit installer review"},
      {"services.enterprise.enabled_targets","Enterprise targets","","Comma-separated reviewed boot targets; empty by default"},
      {"gpu.compute.enabled","GPU programming","false","Enable only after GPU device and runtime feature probing"},
      {"gpu.compute.backend","GPU backend","auto","auto/vulkan/opencl/cuda/rocm-hip/directcompute/metal"},
      {"gpu.compute.isa_policy","GPU ISA policy","probe","Compile for probed device target; never execute device ISA on CPU"},
      {"isa.nbit.cache","N-bit instruction cache","true","Bounded per-VM cache; invalidate on code-generation change"},
      {"isa.vector.state","Extended vector state","auto","auto/scalar/sse/avx/avx2/avx512/neon/sve; hardware and OS state gated"},
      {"aurora.input.click_policy","Click policy","platform-default","single-select/double-open/triple-select-line/titlebar-double-toggle"},
      {"aurora.compatibility.event_loop","Compatibility event loop","true","Route compatibility pointer, keyboard, and context-menu events through Aurora dispatcher"},
      {"updates.policy","Updates","notify","notify/automatic/manual"},
      {"developer.mode","Developer mode","false","Developer facilities"},
      {"performance.background","Background resource mode","opportunistic","Use idle CPU/RAM/I/O without starving interactive work"},
      {"performance.knowledge_cache","Knowledge cache","disk-first","Keep content on disk; bound metadata cache in RAM"},
      {"updates.reboot_policy","Reboot policy","ask","ask/later/now; patches never reboot silently"},
      {"isa.nbit.width","N-bit width","auto","auto or any positive width from 1 to 4294967295; no power-of-two whitelist"},
      {"isa.nbit.backend","N-bit backend","auto","auto/chimera-virtual/physical-native/compatibility"},
      {"isa.nbit.guest","Guest ISA","auto","auto/chimera-nbit/x86-16/x86-32/x86-64/aarch64/arm32/riscv32/riscv64/mips32/mips64/powerpc/loongarch64/s390x/sparc-v9/wasm32/wasm64"},
      {"isa.nbit.compatibility","Compatibility personality","auto","auto/native/windows/linux/bsd/darwin/android/ios; set before choosing compatibility backend"},
      {"isa.nbit.style","N-bit ISA style","HYBRID","RISC/CISC/HYBRID semantic mapping preference; not a conformance claim"},
      {"isa.execution.mode","ISA execution mode","AutoHardware","Scalar/Vector/NativeWide/JIT/QuantumHybrid"},
      {"neural.dimensions","Neural representation dimensions","1024","Live deep-learning dimensionality; 128D baseline, higher dimensions enabled"},
      {"neural.representation","Neural representation","HyperDimensional","HyperDimensional/Tensor/Hybrid"},
      {"neural.learning","Neural learning mode","AdaptiveTensor","Adaptive multidimensional tensor representation"},
      {"security.biometric.enabled","Biometric login","true","Offer enrolled biometric methods alongside username/password"},
      {"security.biometric.password_fallback","Password fallback","true","Keep username/password available for recovery"},
      {"security.biometric.remote","Remote biometric login","false","Disabled by default; biometrics remain local"},
      {"security.biometric.liveness","Require liveness","true","Require provider liveness for face/iris/palm/voice/vein"}
    };
}
static std::string value_of(const std::vector<Setting>& v,const std::string& key) {
    for(const auto& s:v)if(s.key==key)return s.value;
    return {};
}
static bool valid_width(const std::string& value) {
    if(value=="auto")return true;
    if(value.empty())return false;
    uint64_t n=0;
    for(char ch:value) {
        if(ch<'0'||ch>'9')return false;
        const uint64_t digit=(uint64_t)(ch-'0');
        if(n>((uint64_t)UINT32_MAX-digit)/10u)return false;
        n=n*10u+digit;
    }
    return n>0;
}
static bool valid_setting(const std::string& key,const std::string& value) {
    if(key=="isa.nbit.width")return valid_width(value);
    if(key=="isa.nbit.backend")
        return value=="auto"||value=="chimera-virtual"||value=="physical-native"||value=="compatibility";
    if(key=="isa.nbit.guest") {
        static const char* choices[]={"auto","chimera-nbit","x86-16","x86-32","x86-64","aarch64","arm32","arm32-thumb","riscv32","riscv64","riscv128","mips32","mips64","powerpc","ppc64","loongarch32","loongarch64","s390x","sparc-v9","wasm32","wasm64"};
        for(const char* choice:choices)if(value==choice)return true;
        return false;
    }
    if(key=="isa.nbit.compatibility")
        return value=="auto"||value=="native"||value=="windows"||value=="linux"||value=="bsd"||value=="darwin"||value=="android"||value=="ios";
    if(key=="isa.nbit.style")return value=="RISC"||value=="CISC"||value=="HYBRID";
    return true;
}
static uint32_t compatibility_mask(const std::string& target) {
    if(target=="native")return 1u<<0;
    if(target=="windows")return 1u<<1;
    if(target=="linux")return 1u<<2;
    if(target=="bsd")return 1u<<3;
    if(target=="darwin")return 1u<<4;
    if(target=="android")return 1u<<5;
    if(target=="ios")return 1u<<6;
    return 0;
}
static uint32_t backend_id(const std::string& backend) {
    if(backend=="chimera-virtual")return 1u;
    if(backend=="physical-native")return 2u;
    if(backend=="compatibility")return 3u;
    return 0u;
}
static uint32_t guest_isa_id(const std::string& guest) {
    static const char* names[]={"auto","chimera-nbit","x86-16","x86-32","x86-64","aarch64",
      "arm32","arm32-thumb","riscv32","riscv64","riscv128","mips32","mips64","powerpc",
      "ppc64","loongarch32","loongarch64","s390x","sparc-v9","wasm32","wasm64"};
    for(uint32_t i=0;i<sizeof(names)/sizeof(names[0]);++i)if(guest==names[i])return i;
    return 0u;
}
static bool valid_nbit_profile(const std::vector<Setting>& v) {
    const std::string width_text=value_of(v,"isa.nbit.width");
    const std::string backend=value_of(v,"isa.nbit.backend");
    const std::string guest=value_of(v,"isa.nbit.guest");
    const std::string personality=value_of(v,"isa.nbit.compatibility");
    if(!valid_width(width_text)||!valid_setting("isa.nbit.backend",backend)||
       !valid_setting("isa.nbit.guest",guest)||!valid_setting("isa.nbit.compatibility",personality))return false;
    return backend!="compatibility"||compatibility_mask(personality)!=0;
}
static bool save_nbit_profile(const std::vector<Setting>& v) {
    if(!valid_nbit_profile(v))return false;
    const std::string width_text=value_of(v,"isa.nbit.width");
    const std::string backend=value_of(v,"isa.nbit.backend");
    const std::string guest=value_of(v,"isa.nbit.guest");
    const std::string personality=value_of(v,"isa.nbit.compatibility");
    const std::string resolved_guest=(guest=="auto"&&backend=="chimera-virtual")?"chimera-nbit":guest;
    const uint32_t target=backend=="compatibility"?compatibility_mask(personality):0u;
    const uint32_t width=width_text=="auto"?0u:(uint32_t)std::stoull(width_text);
    const fs::path path=nbit_profile_path();
    std::error_code ec;fs::create_directories(path.parent_path(),ec);
    if(ec)return false;
    std::ofstream f(path,std::ios::trunc);if(!f)return false;
    f<<"{\n"
     <<"  \"schema\": \"CHIMERA-NBIT-USER-PROFILE-1\",\n"
     <<"  \"selected_width_bits\": "<<width<<",\n"
     <<"  \"width_policy\": \""<<(width_text=="auto"?"auto":"explicit")<<"\",\n"
     <<"  \"backend\": \""<<backend<<"\",\n"
     <<"  \"backend_id\": "<<backend_id(backend)<<",\n"
     <<"  \"guest_isa\": \""<<resolved_guest<<"\",\n"
     <<"  \"guest_isa_id\": "<<guest_isa_id(resolved_guest)<<",\n"
     <<"  \"compatibility_personality\": ";
    if(personality=="auto") f<<"null"; else f<<"\""<<personality<<"\"";
    f<<",\n";
    f<<"  \"compatibility_target_mask\": "<<target<<",\n";
    f<<"  \"physical_native_width_is_hardware_defined\": true,\n";
    f<<"  \"arbitrary_width_virtual_abi\": true,\n";
    f<<"  \"validation_required_at_kernel_admission\": true,\n";
    f<<"  \"isa_catalog_does_not_imply_executable_backend\": true\n";
    f<<"}\n";
    f.close();
    if(f.fail())return false;
    if(!notify_nbitd(width,backend,resolved_guest,personality))
        std::cerr<<"N-bit profile saved locally; nbitd is not reachable, so the running kernel profile was not updated.\n";
    return true;
}
static std::vector<Setting> load() {
    auto v=defaults(); std::ifstream f(config_path()); std::string line;
    while(std::getline(f,line)) {
        auto eq=line.find('='); if(eq==std::string::npos) continue;
        auto key=line.substr(0,eq), value=line.substr(eq+1);
        for(auto& s:v) if(s.key==key&&valid_setting(key,value)) s.value=value;
    }
    return v;
}
static bool save(const std::vector<Setting>& v) {
    if(!valid_nbit_profile(v))return false;
    std::error_code ec; fs::create_directories(config_path().parent_path(),ec);
    if(ec)return false;
    std::ofstream f(config_path()); if(!f) return false;
    f<<"# Chimera II OS Aurora settings\n";
    for(const auto& s:v) f<<s.key<<"="<<s.value<<"\n";
    f.close();
    return f.good()&&save_nbit_profile(v);
}
static void usage() {
    std::cout<<"Aurora Settings — Chimera II OS\n"
             <<"Usage: aurora-settings [list|show KEY|set KEY VALUE|reset|category CATEGORY]\n"
             <<"N-bit: set isa.nbit.width auto|BITS; isa.nbit.backend auto|chimera-virtual|physical-native|compatibility; isa.nbit.guest ISA\n";
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
        for(auto&s:v) if(s.key==argv[2]) {
            if(!valid_setting(s.key,argv[3])){std::cerr<<"Invalid value for "<<s.key<<": "<<argv[3]<<"\n";return 1;}
            const std::string previous=s.value;s.value=argv[3];
            if(save(v)){std::cout<<"Applied: "<<s.key<<"="<<s.value<<"\nN-bit profile: "<<nbit_profile_path()<<"\n";return 0;}
            s.value=previous;
            std::cerr<<"Could not persist settings/N-bit profile; compatibility backend requires a selected compatibility personality.\n";
            return 2;
        }
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
