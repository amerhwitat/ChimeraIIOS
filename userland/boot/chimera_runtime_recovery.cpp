#include <algorithm>
#include <chrono>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>
#include <sys/types.h>
#include <unistd.h>

namespace fs = std::filesystem;

static fs::path root(){
  if(const char*p=std::getenv("CHIMERA_BOOT_LEARNING_ROOT");p&&*p)return p;
  return "/var/lib/chimera/boot-learning";
}
static fs::path error_log(){
  if(const char*p=std::getenv("CHIMERA_BOOT_ERROR_LOG");p&&*p)return p;
  return root()/"errors.log";
}
static std::string lower(std::string s){
  for(char &c:s)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
  return s;
}
static bool has(const std::string&s,const char*a){return s.find(a)!=std::string::npos;}

static std::string classify(const std::string&line){
  const auto s=lower(line);
  if(has(s,"no space left")||has(s,"enospc")) return "storage";
  if(has(s,"out of memory")||has(s,"oom")||has(s,"cannot allocate")) return "memory";
  if(has(s,"permission denied")||has(s,"eacces")) return "permission";
  if(has(s,"module not found")||has(s,"driver not found")||has(s,"firmware not found")) return "driver";
  if(has(s,"mount")&&has(s,"failed")) return "filesystem";
  if(has(s,"network")&&has(s,"failed")) return "network";
  if(has(s,"timeout")||has(s,"timed out")) return "timeout";
  if(has(s,"segmentation fault")||has(s,"sigsegv")||has(s,"panic")) return "crash";
  if(has(s,"linker")||has(s,"undefined reference")) return "build";
  return "unknown";
}

static int safe_fix(const std::string&type){
  const fs::path r=root();
  std::error_code ec;
  if(type=="storage"){
    fs::create_directories(r/"quarantine",ec);
    return ec?1:0;
  }
  if(type=="memory"){
    fs::create_directories(r/"deferred",ec);
    return ec?1:0;
  }
  if(type=="permission"){
    fs::create_directories(r,ec);
    return ec?1:0;
  }
  if(type=="filesystem"){
    fs::create_directories(r/"recovery",ec);
    return ec?1:0;
  }
  if(type=="driver"){
    fs::create_directories(r/"driver-retry",ec);
    return ec?1:0;
  }
  if(type=="network"||type=="timeout"){
    fs::create_directories(r/"retry",ec);
    return ec?1:0;
  }
  return 0;
}

/*
 * Runtime recovery is intentionally constrained:
 * - observes boot/runtime errors;
 * - classifies them and records a proposed fix;
 * - only performs non-destructive local preparation (directories/state);
 * - never overwrites kernel/driver binaries, kills arbitrary processes,
 *   changes boot order, or reboots the machine.
 * Administrator-approved patching remains in chm-patch.
 */
static int once(){
  const fs::path r=root();
  fs::create_directories(r);
  std::ifstream in(error_log());
  if(!in)return 0;
  std::ofstream actions(r/"runtime-actions.log",std::ios::app);
  std::string line; size_t count=0;
  while(std::getline(in,line)){
    if(line.empty())continue;
    const auto type=classify(line);
    const int rc=safe_fix(type);
    actions<<"pid="<<static_cast<long>(::getpid())<<" type="<<type
           <<" result="<<(rc==0?"prepared":"failed")<<" error="<<line<<"\n";
    ++count;
  }
  std::ofstream rec(r/"runtime-remediation.json");
  rec<<"{\n  \"schema\":\"CHIMERA-RUNTIME-REMEDIATION-1\",\n"
     <<"  \"observed_errors\":"<<count<<",\n"
     <<"  \"mode\":\"safe-preparation\",\n"
     <<"  \"next_step\":\"administrator-approved patching only\"\n}\n";
  return 0;
}

int main(int argc,char**argv){
  if(argc>1&&std::string(argv[1])=="once")return once();
  if(argc>1&&std::string(argv[1])=="daemon"){
    for(;;){once();std::this_thread::sleep_for(std::chrono::seconds(10));}
  }
  if(argc>1&&std::string(argv[1])=="status"){
    std::ifstream f(root()/"runtime-remediation.json");
    std::cout<<(f?"runtime-recovery=active":"runtime-recovery=no-data")<<"\n";
    return 0;
  }
  std::cerr<<"usage: "<<argv[0]<<" [once|daemon|status]\n";
  return 2;
}
