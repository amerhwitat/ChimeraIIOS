#include "chimera/kernel_arch.hpp"
#include <cstdlib>
#include <cstring>
#include <limits>
#ifdef _WIN32
#include <malloc.h>
#endif
namespace chimera::kernel {
static void* page_alloc(){
#ifdef _WIN32
    return _aligned_malloc(MemoryManager::kPageSize,MemoryManager::kPageSize);
#else
    return std::aligned_alloc(MemoryManager::kPageSize,MemoryManager::kPageSize);
#endif
}
static void page_release(void*p){
#ifdef _WIN32
    _aligned_free(p);
#else
    std::free(p);
#endif
}
bool Scheduler::contains(const Task*t)const noexcept{for(std::size_t i=0;i<count_;++i)if(queue_[i]==t)return true;return false;}
void Scheduler::enqueue(Task*t){if(!t||count_>=kMaxTasks||contains(t)||t->state==TaskState::Terminated)return;t->state=TaskState::Ready;queue_[count_++]=t;}
Task* Scheduler::pick_next(){if(!count_)return nullptr;std::size_t best=0;for(std::size_t i=1;i<count_;++i){const Task*a=queue_[i];const Task*b=queue_[best];if(a->priority>b->priority||(a->priority==b->priority&&(a->vruntime<b->vruntime||(a->vruntime==b->vruntime&&a->id<b->id))))best=i;}Task*t=queue_[best];for(std::size_t i=best+1;i<count_;++i)queue_[i-1]=queue_[i];--count_;t->state=TaskState::Running;return t;}
void Scheduler::tick(){++ticks_;for(std::size_t i=0;i<count_;++i)++queue_[i]->vruntime;}
void Scheduler::yield(Task*t){if(!t||t->state==TaskState::Terminated)return;t->state=TaskState::Ready;enqueue(t);}
void Scheduler::block(Task*t){if(t)t->state=TaskState::Blocked;}
void Scheduler::wake(Task*t){if(t&&t->state==TaskState::Blocked)enqueue(t);}
void* MemoryManager::alloc_page(){void*p=page_alloc();if(p)std::memset(p,0,kPageSize);return p;}
void MemoryManager::free_page(void*p){page_release(p);}
bool MemoryManager::map(std::uint64_t va,std::uint64_t pa,std::uint64_t flags){if((va%kPageSize)||(pa%kPageSize)||!flags||mapping_count_>=kMaxMappings||va>std::numeric_limits<std::uint64_t>::max()-kPageSize)return false;if(is_mapped(va))return false;mappings_[mapping_count_++]={va,va+kPageSize,pa,flags};return true;}
bool MemoryManager::unmap(std::uint64_t va){if(va%kPageSize)return false;for(std::size_t i=0;i<mapping_count_;++i)if(mappings_[i].start==va){for(std::size_t j=i+1;j<mapping_count_;++j)mappings_[j-1]=mappings_[j];--mapping_count_;return true;}return false;}
bool MemoryManager::is_mapped(std::uint64_t va)const noexcept{for(std::size_t i=0;i<mapping_count_;++i)if(va>=mappings_[i].start&&va<mappings_[i].end)return true;return false;}
bool MemoryManager::validate_range(std::uint64_t address,std::uint64_t length)const noexcept{if(!length||address>std::numeric_limits<std::uint64_t>::max()-length)return false;const auto end=address+length;auto p=address&~(kPageSize-1);while(p<end){if(!is_mapped(p))return false;if(p>std::numeric_limits<std::uint64_t>::max()-kPageSize)break;p+=kPageSize;}return true;}
void Kernel::init(){}
void Kernel::schedule(){scheduler_.tick();(void)scheduler_.pick_next();}
void Kernel::handle_irq(std::uint32_t){}
long Kernel::syscall(std::uint64_t n,std::uint64_t,std::uint64_t,std::uint64_t,std::uint64_t,std::uint64_t){return static_cast<long>(n);}
}
