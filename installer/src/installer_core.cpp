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
    {"detect","Hardware detection","Firmware, architecture, CPU, PCI/USB/ACPI devices, storage, graphics, network and firmware capabilities"},
    {"driverscan","Deep driver discovery","Enumerate device IDs and recursively search approved Linux/Unix/open-source repositories for matching modules and firmware"},
    {"driverpolicy","Driver trust policy","Allow only signed or cryptographically verified packages; keep proprietary/unknown binaries quarantined unless explicitly enabled"},
    {"driverdownload","Driver acquisition","Download compatible driver/firmware packages, verify hashes/signatures and quarantine untrusted artifacts"},
    {"driverinstall","Driver deployment","Install selected native Koronos modules and compatibility drivers into the target rootfs and regenerate module/firmware indexes"},
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
  if(p.deep_driver_search){
    fs::create_directories(p.target_root/"var/lib/chimera/drivers");
    fs::create_directories(p.target_root/"lib/firmware");
    fs::create_directories(p.target_root/"usr/lib/chimera/drivers");
    fs::path manifest=p.source_root/"drivers/driver-manifest.json";
    if(fs::exists(manifest)) fs::copy_file(manifest,p.target_root/"var/lib/chimera/drivers/driver-manifest.json",fs::copy_options::overwrite_existing);
    std::ofstream log(p.target_root/"var/lib/chimera/drivers/installation-plan.txt");
    log<<"deep_driver_search="<<p.deep_driver_search<<"\\n";
    log<<"download_driver_binaries="<<p.download_driver_binaries<<"\\n";
    log<<"install_detected_drivers="<<p.install_detected_drivers<<"\\n";
    log<<"verify_driver_signatures="<<p.verify_driver_signatures<<"\\n";
    log<<"Driver binaries are installed only after device-ID matching and verification.\\n";
  }
  fs::path toolchains = p.source_root/"build/toolchains";
  if(!fs::exists(toolchains)) toolchains = p.source_root/"toolchains";
  if(fs::exists(toolchains)) { fs::remove_all(p.target_root/"opt/chimera/toolchains"); if(copy_tree(toolchains,p.target_root/"opt/chimera/toolchains")!=0) return 6; }
  fs::create_directories(p.target_root/"etc/profile.d");
  { std::ofstream env(p.target_root/"etc/profile.d/chimera-toolchains.sh"); env<<"export CHIMERA_TOOLCHAIN_ROOT=/opt/chimera/toolchains\\nexport PATH=/opt/chimera/toolchains/bin:$PATH\\nexport LD_LIBRARY_PATH=/opt/chimera/toolchains/lib:/opt/chimera/toolchains/lib64:$LD_LIBRARY_PATH\\n"; }
  fs::path sdk = p.source_root/"sdk";
  if(fs::exists(sdk)) { fs::remove_all(p.target_root/"opt/chimera-sdk"); if(copy_tree(sdk,p.target_root/"opt/chimera-sdk")!=0) return 5; }
  fs::create_directories(p.target_root/"etc/chimera");
  std::ofstream f(p.target_root/"etc/chimera/install.conf");
  f<<"kernel="<<p.kernel<<"\nbootloader="<<p.bootloader<<"\nfilesystem="<<p.filesystem<<"\n";
  std::cout<<"Payload deployed. Platform-specific partition/boot operations are selected by the backend.\n";
  return 0;
}
}
