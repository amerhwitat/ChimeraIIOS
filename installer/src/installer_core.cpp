#include "chimera/installer_core.hpp"
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sys/utsname.h>
namespace fs=std::filesystem;
namespace chimera::installer {
Hardware Installer::detect_hardware() const {
  Hardware h; struct utsname u{};
  if(uname(&u)==0) h.architecture=u.machine;
  h.network=fs::exists("/sys/class/net"); h.nvme=fs::exists("/sys/class/nvme");
  h.sata=fs::exists("/sys/class/ata"); h.graphics=fs::exists("/dev/dri");
  h.firmware=fs::exists("/sys/firmware/efi")?Firmware::UEFI:Firmware::BIOS;
  return h;
}
std::string Installer::firmware_name(Firmware f) {
  if(f==Firmware::BIOS) return "BIOS"; if(f==Firmware::UEFI) return "UEFI"; return "Unknown";
}
std::vector<Step> Installer::build_plan(const InstallPlan&) const {
  return {
    {"detect","Hardware detection","Firmware, architecture, CPU, storage, graphics, network and firmware capabilities"},
    {"locale","Language / Keyboard / Accessibility","Locale, keyboard, console, screen-reader and high-contrast options"},
    {"time","Date / Time / Timezone","Timezone, RTC policy and optional NTP synchronization"},
    {"source","Installation source","Live ISO, local repository, HTTP/HTTPS, NFS and network-share sources"},
    {"network","Network / Proxy","DHCP, static IPv4/IPv6, VLAN, bond, bridge and proxy"},
    {"software","Software Selection","Base system, development, compatibility, desktop and optional package groups"},
    {"partition","Storage layout","Guided/custom partitioning, GPT/MBR, NVMe/SATA/HDD/USB, LVM, RAID, iSCSI and multipath"},
    {"format","Filesystem / Encryption","Create/mount qfs, xfs, zfs, ext4, btrfs, ntfs, FAT and optional LUKS2"},
    {"copy","System deployment","Copy Koronos, Spit Fire/Jasper, Kore, Aurora, userland and compatibility payloads"},
    {"boot","Bootloader / Secure Boot","Install Spit Fire/Jasper/GRUB2, BIOS/UEFI fallback, Secure Boot and bootloader target"},
    {"configure","System configuration","Hostname, services, firewall, security policy, SSH, shells, desktops, drivers and compatibility profiles"},
    {"accounts","Accounts / SSH","Create administrator/user accounts, password policy and optional SSH keys/server"},
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
  if(!confirmed){std::cerr<<"Explicit destructive confirmation required.\n";return 3;}
  if(copy_tree(p.source_root,p.target_root)!=0) return 4;
  fs::path sdk = p.source_root/"sdk";
  if(fs::exists(sdk)) { fs::remove_all(p.target_root/"opt/chimera-sdk"); if(copy_tree(sdk,p.target_root/"opt/chimera-sdk")!=0) return 5; }
  fs::create_directories(p.target_root/"etc/chimera");
  std::ofstream f(p.target_root/"etc/chimera/install.conf");
  f<<"kernel="<<p.kernel<<"\nbootloader="<<p.bootloader<<"\nfilesystem="<<p.filesystem<<"\n";
  std::cout<<"Payload deployed. Platform-specific partition/boot operations are selected by the backend.\n";
  return 0;
}
}
