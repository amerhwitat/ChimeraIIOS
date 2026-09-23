#include "aurora_input_router.hpp"
#include <cmath>
namespace aurora::input {
void InputRouter::set_window_policy(uint64_t id,WindowPolicy p){policies_[id]=p;}
void InputRouter::focus_window(uint64_t id){focused_window_=id;}
void InputRouter::register_shortcut(Shortcut s){shortcuts_.push_back(std::move(s));}
bool InputRouter::dispatch_shortcut(uint64_t id,const Event&e)const{if(e.type!=Type::KeyDown||id!=focused_window_)return false;for(const auto&s:shortcuts_)if(s.key==e.key&&s.modifiers==e.modifiers){if(command_sink_)command_sink_(s.command,id);return true;}return false;}
void InputRouter::route(uint64_t id,const Event&e){
 auto p=policies_.find(id);if(p!=policies_.end()){bool mouse=e.type==Type::MouseMove||e.type==Type::MouseButtonDown||e.type==Type::MouseButtonUp||e.type==Type::MouseClick||e.type==Type::MouseDoubleClick||e.type==Type::MouseTripleClick||e.type==Type::MouseWheel;if(mouse&&!p->second.accept_mouse)return;if((e.type==Type::KeyDown||e.type==Type::KeyUp||e.type==Type::TextInput)&&!p->second.accept_keyboard)return;}
 if(dispatch_shortcut(id,e))return;
 if(e.type==Type::MouseButtonDown){auto&s=clicks_[id];uint64_t delta=e.timestamp_ns-s.last_ns;int dx=e.x-s.x,dy=e.y-s.y;double dist=std::sqrt(double(dx*dx+dy*dy));if(s.button==e.button&&s.last_ns&&delta<=uint64_t(click_policy_.triple_click_ms)*1000000ULL&&dist<=click_policy_.distance_px)s.count=s.count==2?3:2;else{s.button=e.button;s.count=1;}s.last_ns=e.timestamp_ns;s.x=e.x;s.y=e.y;Event click=e;click.type=s.count==3?Type::MouseTripleClick:(s.count==2?Type::MouseDoubleClick:Type::MouseClick);click.clicks=static_cast<ClickCount>(s.count);if(event_sink_)event_sink_(click);}
 if(event_sink_)event_sink_(e);
}
}