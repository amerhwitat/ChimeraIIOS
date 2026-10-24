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
std::vector<Step> Installer::build_plan(const InstallPlan& p) const {
  return {
    {"detect","Hardware / CPU detection","Detect architecture, CPU vendor, logical cores, firmware, PCI/USB/ACPI devices, storage, graphics and network capabilities"},
    {"cpucompat","Koronos CPU compatibility","Select native or conservative compatibility mode from detected CPU capabilities while preserving all detected logical cores"},
    {"driverscan","Deep driver discovery","Enumerate PCI/USB/ACPI/SMBIOS device IDs and match the staged Koronos driver registry and approved Linux/Unix driver catalog"},
    {"driverrecommend","Driver recommendation","Recommend native Koronos drivers first, then verified Linux/Windows/macOS compatibility adapters, with evidence, provenance, fallback and unresolved-device warnings"},
    {"driverpolicy","Driver trust policy","Allow only signed or cryptographically verified packages; keep proprietary/unknown binaries quarantined unless explicitly enabled"},
    {"driverdownload","Driver acquisition","Download compatible driver/firmware packages, verify hashes/signatures and quarantine untrusted artifacts"},
    {"driverinstall","Driver deployment","Install selected native Koronos modules and compatibility drivers into the target rootfs and regenerate module/firmware indexes"},
    {"locale","Language / Keyboard / Accessibility","Selected locale=" + p.locale + "; keyboard=" + p.keyboard_layout + "; input languages=" + p.input_languages + ". Target config must include locale, console keymap and input-method setup."},
    {"time","Date / Time / Timezone","Selected timezone=" + p.timezone + "; hardware clock UTC=" + (p.hardware_clock_utc ? "yes" : "no") + "; NTP=" + (p.enable_ntp ? "enabled" : "disabled") + ". Configure timezone, RTC policy and time-sync service only during a verified transaction."},
    {"source","Installation source","Selected source=" + p.source_type + "; validate media/repository identity and package signatures before use. Supported patterns: Live ISO, local repository, HTTP/HTTPS and NFS where built into the image."},
    {"network","Network / Proxy","Selected network mode=" + p.network_mode + "; validate connectivity and never persist secrets to logs. DHCP/static IPv4/IPv6 and proxy are planned only where the runtime backend supports them."},
    {"software","Software Selection","System role=" + p.edition + "; desktop=" + p.desktop_profile + ". Base system, development, compatibility, desktop and optional package groups; install only verified payloads present in the selected image."},
    {"partition","Storage layout","Mode=" + p.storage_mode + "; preserve existing OS=" + (p.preserve_existing_os ? "yes" : "no") + "; encrypt root=" + (p.encrypt_root ? "yes" : "no") + ". Guided/custom partitioning, GPT/MBR, NVMe/SATA/HDD/USB, LVM, RAID, iSCSI and multipath; destructive actions remain blocked until device identity and rollback are verified."},
    {"format","Filesystem / Encryption","Select a supported native filesystem; identify NTFS, FAT16 and FAT32 partitions read-only during discovery. Writable NTFS requires a verified NTFS driver/helper; FAT requires the FAT/VFAT driver. Never format or mount writable until capability and target-device identity are verified."},
    {"fstab","Linux filesystem layout","Stage Linux hierarchy: /etc, /usr, /var, /home, /root, /boot, /dev, /proc, /sys, /run, /tmp, /opt, /mnt and /media; generate fstab only from verified partition UUIDs and tested mount options."},
    {"copy","System deployment","Copy Koronos, Spit Fire/Jasper, Kore, Aurora, userland and compatibility payloads"},
    {"boot","Bootloader / Secure Boot","Selected bootloader=" + p.bootloader + "; Secure Boot policy=" + (p.secure_boot ? "enabled" : "disabled") + ". Install Spit Fire/Jasper/GRUB2 and BIOS/UEFI fallback only after target and firmware verification."},
    {"configure","System configuration","Hostname=" + p.hostname + "; firewall=" + (p.firewall_enabled ? "enabled" : "review-required") + ". Persist and verify services, security policy, SSH, shells, desktops, drivers and compatibility profiles in the target root."},
    {"accounts","Accounts / SSH","Administrator username=" + p.admin_username + ". Create accounts, password policy and optional SSH keys/server only through a verified target-root transaction."},
    {"toolchain","Compiler / Assembler / JIT / Runtime","Install the staged multi-language toolchain bundle, cross-toolchains, binary utilities, debuggers and runtime libraries"},
    {"sdk","Developer SDK","Install Chimera C/C++/C#/Objective-C/Java/Python SDK, source and manuals"},
    {"recovery","Recovery / Backup","Recovery partition, rescue environment, rollback plan and backup configuration"},
    {"review","Review","Summarize every selected disk, partition, package, desktop, security and boot option before commit"},
    {"verify","Verification","Check required binaries, manifests, hashes, filesystem, boot configuration and post-install boot path"},
    {"logs","Installation logs","Persist hardware, storage, network, transaction and verification logs"},
    {"finish","Finish","Flush, unmount, offer first-boot setup and reboot"}
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
  for(const auto& s:build_plan(p))
    std::cout<<"["<<s.id<<"] "<<s.title<<" — "<<s.detail<<"\n";
  if(p.dry_run) {
    std::cout<<"DRY RUN ONLY: no disk changes; no installation success is claimed.\n";
    return 0;
  }
  (void)confirmed;
  std::cerr<<"INSTALLATION BLOCKED: this shared executor does not yet implement transactional partition/filesystem/mount operations, durable journal and rollback, verified writes, bootloader installation, locale/timezone/keymap persistence, or post-install cold-boot verification.\n";
  std::cerr<<"No disk changes were attempted. GUI and text frontends are both blocked by this backend gate.\n";
  return 78;
}
}
