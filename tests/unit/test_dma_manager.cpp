#include "chimera/dma.hpp"
#include <cassert>
int main(){
    chimera::dma::Manager dma;
    chimera::dma::Device dev{7,0xFFFFFFFFULL};
    auto buf=dma.allocate(8192,4096);
    assert(buf);
    const auto token=dma.map(dev,buf,chimera::dma::Direction::ToDevice);
    assert(token.valid());
    assert(dma.lookup(token).has_value());
    assert(!dma.map(dev,buf,chimera::dma::Direction::ToDevice).valid());
    assert(dma.sync(token));
    assert(dma.unmap(token));
    assert(!dma.lookup(token).has_value());
    dma.release(buf);
    return 0;
}
