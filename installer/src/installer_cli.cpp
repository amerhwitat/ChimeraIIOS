#include "chimera/installer_core.hpp"
#include <iostream>
#include <string>
int main(int argc,char**argv){
  chimera::installer::Installer i; auto h=i.detect_hardware();
  std::cout<<"Chimera II Setup — text mode\nArchitecture: "<<h.architecture
    <<" Firmware: "<<chimera::installer::Installer::firmware_name(h.firmware)
    <<" NVMe:"<<h.nvme<<" SATA:"<<h.sata<<" Network:"<<h.network<<" Graphics:"<<h.graphics<<"\n";
  chimera::installer::InstallPlan p;
  std::string a;
  p.source_root=argc>1?argv[1]:"/run/chimera/live"; p.target_root=argc>2?argv[2]:"/target";
  std::cout<<"Firmware mode detected as "<<chimera::installer::Installer::firmware_name(h.firmware)<<". Type BIOS or UEFI to confirm: "; std::getline(std::cin,a);
  if(a=="BIOS") p.firmware=chimera::installer::Firmware::BIOS; else if(a=="UEFI") p.firmware=chimera::installer::Firmware::UEFI; else { std::cerr<<"Invalid firmware selection.\\n"; return 2; }
  std::cout<<"Target whole-disk device (e.g. /dev/nvme0n1; blank for dry-run): "; std::getline(std::cin,a); p.boot_device=a;
  std::cout<<"Root partition (e.g. /dev/nvme0n1p2): "; std::getline(std::cin,a); p.root_partition=a;
  if(p.firmware==chimera::installer::Firmware::UEFI){ std::cout<<"EFI System Partition (e.g. /dev/nvme0n1p1): "; std::getline(std::cin,a); p.efi_partition=a; }
  std::cout<<"Start installation plan? [y/N] "; std::getline(std::cin,a);
  if(a!="y"&&a!="Y") return 0;
  std::cout<<"Type ERASE-AND-INSTALL to authorize destructive storage operations, anything else for dry-run: "; std::getline(std::cin,a);
  p.destructive_confirmation_token=a; p.dry_run=(a!="ERASE-AND-INSTALL"); return i.execute(p,!p.dry_run);
}
