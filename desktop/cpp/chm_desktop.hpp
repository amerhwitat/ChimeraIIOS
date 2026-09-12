#pragma once
#include <cstdint>
#include <functional>
#include <string>
#include <unordered_map>

namespace chimera::desktop {
enum class Platform { LinuxGtk, LinuxQt, WindowsWin32, WindowsModern, MacOSAppKit, MacOSSwiftUI, Classic };
enum class EventType { WindowCreate, WindowClose, WindowMove, WindowResize, FocusIn, FocusOut, KeyDown, KeyUp, TextInput, PointerMove, PointerDown, PointerUp, Wheel, TouchBegin, TouchUpdate, TouchEnd, Gesture, DragBegin, DragUpdate, DragEnd, MenuCommand, DisplayChange, ThemeChange, Quit };
struct Event { EventType type{}; std::uint64_t timestamp_ns{}; std::string device_id; std::string window_id; double x{}, y{}, dx{}, dy{}; std::uint32_t modifiers{}, buttons{}; std::string key, text; };
using Handler = std::function<void(const Event&)>;
class EventRouter {
 public:
  void on(EventType type, Handler handler) { handlers_[type] = std::move(handler); }
  void dispatch(const Event& event) const { auto it=handlers_.find(event.type); if(it!=handlers_.end() && it->second) it->second(event); }
 private: std::unordered_map<EventType, Handler> handlers_;
};
struct DesktopProfile { Platform platform; const char* name; bool dark_mode; bool menu_bar; bool gestures; bool accessibility; };
inline DesktopProfile profile(Platform p) {
 switch(p) {
  case Platform::LinuxGtk: return {p,"linux-gtk",true,true,true,true};
  case Platform::LinuxQt: return {p,"linux-qt",true,true,true,true};
  case Platform::WindowsWin32: return {p,"windows-win32",true,true,true,true};
  case Platform::WindowsModern: return {p,"windows-modern",true,true,true,true};
  case Platform::MacOSAppKit: return {p,"macos-appkit",true,true,true,true};
  case Platform::MacOSSwiftUI: return {p,"macos-swiftui",true,true,true,true};
  default: return {p,"classic",false,true,false,true};
 }
}
} // namespace chimera::desktop
