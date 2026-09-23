#pragma once
#include <cstdint>
#include <string>
namespace aurora::input {
enum class Type { MouseMove, MouseButtonDown, MouseButtonUp, MouseWheel, KeyDown, KeyUp, TextInput, Touch, Gesture, Tablet };
enum class MouseButton { Left, Middle, Right, Back, Forward, Other };
struct Event {
 Type type; uint64_t timestamp_ns{}; int32_t x{},y{},dx{},dy{},wheel_x{},wheel_y{};
 MouseButton button{MouseButton::Other}; uint32_t key{},scan_code{},modifiers{}; std::string text;
};
struct DeviceProperties {
 std::string id,name,vendor,product,transport; int buttons{}; bool touch{},tablet{},high_resolution_wheel{};
};
struct WindowPolicy { bool focus=true; bool accept_mouse=true; bool accept_keyboard=true; bool context_menu=true; };
}
