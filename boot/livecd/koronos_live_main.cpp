#include <cstdint>
extern "C" int koronos_live_main(){
  volatile std::uint16_t* vga=reinterpret_cast<std::uint16_t*>(0xB8000);
  const char* s="Chimera II OS - Koronos Live CD";
  for(std::uint32_t i=0;s[i];++i) vga[i]=0x0F00u|static_cast<unsigned char>(s[i]);
  return 0;
}
