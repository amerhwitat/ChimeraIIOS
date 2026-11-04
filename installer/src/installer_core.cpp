#include "chimera/installer_core.hpp"
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <thread>
#include <algorithm>
#include <cstdio>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <process.h>
#define CHIMERA_POPEN _popen
#define CHIMERA_PCLOSE _pclose
#else
#include <sys/utsname.h>
#define CHIMERA_POPEN popen
#define CHIMERA_PCLOSE pclose
#endif
namespace fs=std::filesystem;
namespace chimera::installer {
Hardware Installer::detect_hardware() const {
  Hardware h;
#ifdef _WIN32
  SYSTEM_INFO info{}; GetNativeSystemInfo(&info);
  const char* arch=std::getenv("PROCESSOR_ARCHITECTURE");
  h.architecture=arch?arch:(info.wProcessorArchitecture==PROCESSOR_ARCHITECTURE_AMD64?"x86_64":"unknown");
#else
  struct utsname u{};
  if(uname(&u)==0) h.architecture=u.machine;
#endif
  h.cpu_cores=std::max(1u,std::thread::hardware_concurrency());
  #ifndef _WIN32
  { std::ifstream f("/proc/cpuinfo"); std::string line; while(std::getline(f,line)){ if(line.rfind("vendor_id",0)==0){ auto p=line.find(":"); if(p!=std::string::npos) h.cpu_vendor=line.substr(p+2); break; } } }
#else
  if(const char* vendor=std::getenv("PROCESSOR_IDENTIFIER")) h.cpu_vendor=vendor;
#endif
  h.koronos_compatibility = !(h.architecture=="x86_64" || h.architecture=="amd64" || h.architecture=="aarch64" || h.architecture=="riscv64");
  #ifdef _WIN32
  h.network=false; h.nvme=false; h.sata=false; h.graphics=false; h.firmware=Firmware::Unknown;
#else
  h.network=fs::exists("/sys/class/net"); h.nvme=fs::exists("/sys/class/nvme");
  h.sata=fs::exists("/sys/class/ata"); h.graphics=fs::exists("/dev/dri");
  h.firmware=fs::exists("/sys/firmware/efi")?Firmware::UEFI:Firmware::BIOS;
  if(fs::exists("/sys/class/drm")) h.graphics=true;
#endif
  return h;
}
std::string Installer::firmware_name(Firmware f) {
  if(f==Firmware::BIOS) return "BIOS"; if(f==Firmware::UEFI) return "UEFI"; return "Unknown";
}
std::vector<Step> Installer::build_plan(const InstallPlan&) const {
  return {
    {"detect","Hardware / CPU detection","Detect architecture, CPU vendor, logical cores, firmware, PCI/USB/ACPI devices, storage, graphics and network capabilities"},
    {"cpucompat","Koronos CPU compatibility","Select native or conservative compatibility mode from detected CPU capabilities while preserving all detected logical cores"},
    {"driverscan","Deep driver discovery","Enumerate PCI/USB/ACPI/SMBIOS device IDs and match the staged Koronos driver registry and approved Linux/Unix driver catalog"},
    {"driverrecommend","Driver recommendation","Recommend native Koronos drivers first, then verified Linux/Windows/macOS compatibility adapters, with evidence, provenance, fallback and unresolved-device warnings"},
    {"driverpolicy","Driver trust policy","Allow only signed or cryptographically verified packages; keep proprietary/unknown binaries quarantined unless explicitly enabled"},
    {"driverdownload","Driver acquisition","Download compatible driver/firmware packages, verify hashes/signatures and quarantine untrusted artifacts"},
    {"driverinstall","Driver deployment","Install selected native Koronos modules and compatibility drivers into the target rootfs and regenerate module/firmware indexes"},
    {"locale","Language / Keyboard / Accessibility","Locale, keyboard, console, screen-reader and high-contrast options"},
    {"time","Date / Time / Timezone","Timezone, RTC policy and optional NTP synchronization"},
    {"source","Installation source","Live ISO, local repository, HTTP/HTTPS, NFS and network-share sources"},
    {"network","Network / Proxy","DHCP, static IPv4/IPv6, VLAN, bond, bridge and proxy"},
    {"software","Software Selection","Base system, development, compatibility, desktop and optional package groups"},
    {"partition","Storage layout (planned; backend unavailable)","Selection is collected and validated only; GPT/MBR creation, device topology checks, RAID/LVM and partition mutation are blocked"},
    {"format","Filesystem / Encryption (planned; backend unavailable)","No filesystem is created or mounted; formats and encryption are offered only when a verified backend exists"},
    {"copy","System deployment (blocked)","Requires verified production Koronos ELF, installed-system initramfs and signed/hash-checked payload manifest"},
    {"boot","Bootloader / Secure Boot (blocked)","GRUB BIOS/UEFI installation is not integrated into this transaction; no boot sector or EFI variable is changed"},
    {"configure","System configuration","Hostname, services, firewall, security policy, SSH, shells, desktops, drivers and compatibility profiles"},
    {"accounts","Accounts / SSH","Create administrator/user accounts, password policy and optional SSH keys/server"},
    {"toolchain","Compiler / Assembler / JIT / Runtime","Install the staged multi-language toolchain bundle, cross-toolchains, binary utilities, debuggers and runtime libraries"},
    {"sdk","Developer SDK","Install Chimera C/C++/C#/Objective-C/Java/Python SDK, source and manuals"},
    {"recovery","Recovery / Backup","Recovery partition, rescue environment, rollback plan and backup configuration"},
    {"review","Review","Summarize every selected disk, partition, package, desktop, security and boot option before commit"},
    {"verify","Verification (required before commit)","Must verify installed ELF/initramfs hashes, filesystem mounts, boot configuration and durable post-install state before success"},
    {"logs","Installation logs","Persist hardware, storage, network, transaction and verification logs"},
    {"finish","Finish (gated)","Flush and unmount only transaction-owned mounts; reboot may be offered only after durable verification and cleanup"}
  };
}
int Installer::run(const std::string& cmd,bool allow_failure) const {
  std::cout<<"[installer] "<<cmd<<"\n"; int rc=std::system(cmd.c_str());
  if(rc!=0&&!allow_failure) std::cerr<<"[installer] command failed: "<<rc<<"\n"; return rc;
}
static std::string capture_command(const std::string& cmd) {
  std::string out;
  FILE* pipe=CHIMERA_POPEN(cmd.c_str(),"r");
  if(!pipe) return out;
  char buf[4096];
  while(fgets(buf,sizeof(buf),pipe)) out+=buf;
  CHIMERA_PCLOSE(pipe);
  return out;
}
int Installer::copy_tree(const fs::path& src,const fs::path& dst) const {
  if(!fs::exists(src)) return 2; fs::create_directories(dst);
  for(auto& e:fs::recursive_directory_iterator(src)){ auto out=dst/fs::relative(e.path(),src);
    if(e.is_directory()) fs::create_directories(out);
    else if(e.is_regular_file()){fs::create_directories(out.parent_path());fs::copy_file(e.path(),out,fs::copy_options::overwrite_existing);}
  } return 0;
}
int Installer::execute(const InstallPlan& p,bool confirmed) {
  std::cout<<"Chimera II Setup — Koronos installation transaction\n";
  for(const auto&s:build_plan(p)) std::cout<<"["<<s.id<<"] "<<s.title<<" — "<<s.detail<<"\n";
  if(p.dry_run){std::cout<<"Dry-run: no disk changes.\n";return 0;}
  if(!confirmed || p.destructive_confirmation_token!="ERASE-AND-INSTALL"){std::cerr<<"Explicit destructive confirmation token required.\n";return 3;}
#ifndef _WIN32
  auto is_block_device=[](const fs::path& path){ std::error_code ec; return !path.empty() && fs::exists(path,ec) && !ec && fs::is_block_file(path,ec) && !ec; };
  if(p.boot_device.empty() || p.root_partition.empty() || !is_block_device(p.boot_device) || !is_block_device(p.root_partition)) { std::cerr<<"Selected boot disk and root partition must be existing block devices.\n"; return 5; }
  if(p.firmware==Firmware::Unknown || p.firmware!=detect_hardware().firmware) { std::cerr<<"Firmware selection must match the running firmware mode.\n"; return 5; }
  if(p.firmware==Firmware::UEFI && (p.efi_partition.empty() || !is_block_device(p.efi_partition))) { std::cerr<<"UEFI installation requires an existing EFI System Partition block device.\n"; return 5; }
#else
  std::cerr<<"Native disk installation is not supported by this backend.\n"; return 5;
#endif
  // Fail closed until a tested partition/mount/deploy/verify/GRUB transaction backend is linked.
  // Never copy an installation tree into an arbitrary host directory and call it installed.
  std::cerr<<"STORAGE TRANSACTION BLOCKED: partitioning, formatting, mount ownership, installed initramfs verification, GRUB installation and rollback backend are not integrated. No disk was modified.\n";
  return 6;
}
}
