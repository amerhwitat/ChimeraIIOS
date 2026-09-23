#pragma once
#include "aurora_input.hpp"
#include <functional>
#include <string>
#include <unordered_map>
#include <vector>
namespace aurora::input {
struct Shortcut { uint32_t key{}; uint32_t modifiers{}; std::string command; };
class InputRouter {
public:
 using EventSink=std::function<void(const Event&)>; using CommandSink=std::function<void(const std::string&,uint64_t)>;
 void set_event_sink(EventSink sink){event_sink_=std::move(sink);} void set_command_sink(CommandSink sink){command_sink_=std::move(sink);}
 void set_window_policy(uint64_t id,WindowPolicy p); void focus_window(uint64_t id); uint64_t focused_window()const noexcept{return focused_window_;}
 void register_shortcut(Shortcut s); void route(uint64_t id,const Event&e); bool dispatch_shortcut(uint64_t id,const Event&e)const;
 void set_click_policy(ClickPolicy p){click_policy_=p;} ClickPolicy click_policy()const{return click_policy_;}
private:
 struct ClickState{MouseButton button{MouseButton::Other};uint64_t last_ns{};int32_t x{},y{};uint8_t count{};};
 EventSink event_sink_;CommandSink command_sink_;std::unordered_map<uint64_t,WindowPolicy> policies_;std::vector<Shortcut> shortcuts_;std::unordered_map<uint64_t,ClickState> clicks_;uint64_t focused_window_{0};ClickPolicy click_policy_{};
};
}