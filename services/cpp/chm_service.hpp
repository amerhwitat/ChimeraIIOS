#pragma once
#include <string>
#include <vector>
namespace chm::services {
enum class State { Inactive, Starting, Active, Stopping, Failed };
struct Descriptor { std::string id, platform, backend; State state{State::Inactive}; std::vector<std::string> capabilities; };
inline bool can_transition(State from, State to) { return (from==State::Inactive&&to==State::Starting)||(from==State::Starting&&to==State::Active)||(from==State::Starting&&to==State::Failed)||(from==State::Active&&to==State::Stopping)||(from==State::Stopping&&to==State::Inactive)||(from==State::Failed&&to==State::Starting); }
}
