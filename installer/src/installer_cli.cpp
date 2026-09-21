#include "chimera/installer_core.hpp"
#include <iostream>
#include <string>
int main(int argc,char**argv){
  chimera::installer::Installer i; auto h=i.detect_hardware();
  std::cout<<"Chimera II Setup — text mode\nArchitecture: "<<h.architecture
    <<" Firmware: "<<chimera::installer::Installer::firmware_name(h.firmware)
    <<" NVMe:"<<h.nvme<<" SATA:"<<h.sata<<" Network:"<<h.network<<" Graphics:"<<h.graphics<<"\n";
  chimera::installer::InstallPlan p;
  p.source_root=argc>1?argv[1]:"/run/chimera/live"; p.target_root=argc>2?argv[2]:"/target";
  std::string a; std::cout<<"Start installation plan? [y/N] "; std::getline(std::cin,a);
  if(a!="y"&&a!="Y") return 0;
  std::cout<<"Type INSTALL for destructive execution, anything else for dry-run: "; std::getline(std::cin,a);
  p.dry_run=(a!="INSTALL"); return i.execute(p,!p.dry_run);
}
