#include "chimera/installer_core.hpp"
#include <iostream>
int main(){
  chimera::installer::Installer i; auto h=i.detect_hardware();
  std::cout<<"Aurora Wayland Glass — Chimera II Setup\n";
  std::cout<<"Background: Aurora Wayland Glass Desktop.png (Library asset)\n";
  std::cout<<"Firmware: "<<chimera::installer::Installer::firmware_name(h.firmware)<<" Architecture: "<<h.architecture<<"\n";
  std::cout<<"GUI flow: Welcome -> Language -> Keyboard -> Network -> Storage -> Filesystem -> User -> Desktop -> Bootloader -> Install -> Verify -> Reboot\n";
  return 0;
}
