#include "chimera/dma.hpp"
#include <cstdlib>
#include <cstring>
#include <limits>
#ifdef _WIN32
#include <malloc.h>
#endif
namespace chimera::dma {
static void* dma_alloc(std::size_t alignment,std::size_t size){
#ifdef _WIN32
    return _aligned_malloc(size,alignment);
#else
    return std::aligned_alloc(alignment,size);
#endif
}
static void dma_free(void*p)noexcept{
#ifdef _WIN32
    _aligned_free(p);
#else
    std::free(p);
#endif
}
Buffer Manager::allocate(std::size_t bytes,std::size_t alignment){if(!bytes||alignment<sizeof(void*)||(alignment&(alignment-1)))return{};if(bytes>std::numeric_limits<std::size_t>::max()-alignment+1)return{};const auto rounded=(bytes+alignment-1)/alignment*alignment;void*p=dma_alloc(alignment,rounded);if(p)std::memset(p,0,rounded);return{p,bytes,alignment};}
void Manager::release(Buffer b)noexcept{if(b.address)dma_free(b.address);}
Token Manager::map(const Device&d,Buffer b,Direction dir){if(!b||!b.size)return{};for(const auto&m:mappings_)if(m&&m->buffer.address==b.address)return{};const auto addr=reinterpret_cast<std::uintptr_t>(b.address);if((static_cast<std::uint64_t>(addr)&~d.dma_mask)!=0)return{};for(auto&slot:mappings_)if(!slot){if(next_token_==0)next_token_=1;const Token t{next_token_++};slot=Mapping{t,d,b,dir,static_cast<std::uint64_t>(addr),false};return t;}return{};}
bool Manager::sync(Token t)noexcept{for(auto&m:mappings_)if(m&&m->token.id==t.id){m->synced=true;return true;}return false;}
bool Manager::unmap(Token t)noexcept{for(auto&m:mappings_)if(m&&m->token.id==t.id){m.reset();return true;}return false;}
std::optional<Mapping> Manager::lookup(Token t)const{for(const auto&m:mappings_)if(m&&m->token.id==t.id)return m;return std::nullopt;}
}
