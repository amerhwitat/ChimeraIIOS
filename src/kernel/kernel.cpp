#include <atomic>
#include <cstdint>
#include <vector>
#include <iostream>
namespace koronos {
struct Task{std::uint64_t id;int priority;std::atomic<bool> runnable{true};};
class Scheduler{public:void add(Task&t){tasks.push_back(&t);}void run_once(){for(auto*t:tasks)if(t->runnable.load())std::cout<<"Koronos dispatch T"<<t->id<<"\n";}private:std::vector<Task*>tasks;};
void boot(const char*mode){std::cout<<"Koronos research kernel: firmware="<<mode<<"\n";}
}
