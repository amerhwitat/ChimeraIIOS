#pragma once
#include <cstddef>
#include <cstdint>
namespace chimera {
struct NetFrame { const void* data=nullptr; std::size_t len=0; uint64_t dma_addr=0; uint32_t handle=0; };
class Spotnik {
public:
    virtual ~Spotnik() = default;
    virtual bool send_zc(const NetFrame&) = 0;
    virtual bool recv_zc(NetFrame&) = 0;
    virtual void release_rx(const NetFrame&) = 0;
};
}
