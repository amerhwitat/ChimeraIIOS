#include "chimera/bootinfo.hpp"
#include <cstddef>
#include <cstdint>

namespace chimera::boot {
namespace {
std::uint32_t crc32_update(std::uint32_t crc,const std::uint8_t* p,std::size_t n) noexcept {
    while(n--){ crc ^= *p++; for(int i=0;i<8;++i) crc=(crc>>1) ^ (0xEDB88320u & static_cast<std::uint32_t>(-(crc&1u))); }
    return crc;
}
}
std::uint32_t crc32(const void* data,std::size_t size) noexcept {
    if(!data && size) return 0;
    return ~crc32_update(0xFFFFFFFFu,static_cast<const std::uint8_t*>(data),size);
}
void BootInfo::finalize_crc() noexcept { crc32=0; crc32=chimera::boot::crc32(this,sizeof(BootInfo)); }
bool BootInfo::valid() const noexcept {
    if(magic!=kBootMagic || version!=kBootVersion || size!=sizeof(BootInfo) || memory_map_count>kMaxMemoryMapEntries) return false;
    BootInfo copy=*this; const auto expected=copy.crc32; copy.crc32=0;
    return expected==chimera::boot::crc32(&copy,sizeof(BootInfo));
}
} // namespace chimera::boot
