#pragma once
#include <cstdint>
#include <string>
namespace aurora::input {
enum class Type { MouseMove, MouseButtonDown, MouseButtonUp, MouseWheel, MouseClick, MouseDoubleClick, MouseTripleClick, KeyDown, KeyUp, TextInput, Touch, Gesture, Tablet };
enum class MouseButton { Left, Middle, Right, Back, Forward, Other };
enum class ClickCount : uint8_t { None=0, Single=1, Double=2, Triple=3 };
struct Event { Type type; uint64_t timestamp_ns{}; int32_t x{},y{},dx{},dy{},wheel_x{},wheel_y{}; MouseButton button{MouseButton::Other}; ClickCount clicks{ClickCount::None}; uint32_t key{},scan_code{},modifiers{}; std::string text; };
struct DeviceProperties { std::string id,name,vendor,product,transport; int buttons{}; bool touch{},tablet{},high_resolution_wheel{}; };
struct WindowPolicy { bool focus=true,accept_mouse=true,accept_keyboard=true,context_menu=true; };
struct ClickPolicy { uint32_t double_click_ms=400,triple_click_ms=600; int32_t distance_px=6; };
}