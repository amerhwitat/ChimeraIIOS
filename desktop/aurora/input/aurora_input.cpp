#include "aurora_input.hpp"
#include <iostream>
namespace aurora::input {
static const char* type_name(Type t){switch(t){case Type::MouseMove:return"MouseMove";case Type::MouseButtonDown:return"MouseButtonDown";case Type::MouseButtonUp:return"MouseButtonUp";case Type::MouseWheel:return"MouseWheel";case Type::KeyDown:return"KeyDown";case Type::KeyUp:return"KeyUp";case Type::TextInput:return"TextInput";case Type::Touch:return"Touch";case Type::Gesture:return"Gesture";default:return"Tablet";}}
void debug_event(const Event& e){std::cout<<"AuroraInput "<<type_name(e.type)<<" x="<<e.x<<" y="<<e.y<<" key="<<e.key<<" modifiers="<<e.modifiers<<"\n";}
}
