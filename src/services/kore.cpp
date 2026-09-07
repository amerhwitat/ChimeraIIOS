#include <future>
#include <functional>
#include <iostream>
#include <string>
#include <vector>
namespace kore {
struct Unit{std::string name;std::vector<std::string> after;std::function<void()> start;};
class Manager{public:void add(Unit u){units.push_back(std::move(u));}void start_parallel(){std::vector<std::future<void>>jobs;for(auto&u:units)jobs.push_back(std::async(std::launch::async,[&u]{std::cout<<"[Kore] start "<<u.name<<"\n";if(u.start)u.start();}));for(auto&j:jobs)j.get();}private:std::vector<Unit>units;};
}
