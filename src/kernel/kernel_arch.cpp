#include "chimera/kernel_arch.hpp"
#include <cstdlib>
namespace chimera::kernel {
void Scheduler::enqueue(Task* t){ if(t && count_<queue_.size()) queue_[count_++]=t; }
Task* Scheduler::pick_next(){ if(!count_) return nullptr; Task* t=queue_[0]; for(std::size_t i=1;i<count_;++i) queue_[i-1]=queue_[i]; --count_; return t; }
void Scheduler::tick(){}
void* MemoryManager::alloc_page(){ return std::aligned_alloc(4096,4096); }
void MemoryManager::free_page(void* p){ std::free(p); }
bool MemoryManager::map(uint64_t,uint64_t,uint64_t){ return true; }
void Kernel::init(){}
void Kernel::schedule(){ scheduler_.tick(); (void)scheduler_.pick_next(); }
void Kernel::handle_irq(uint32_t){}
long Kernel::syscall(uint64_t n,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t){ return static_cast<long>(n); }
}
