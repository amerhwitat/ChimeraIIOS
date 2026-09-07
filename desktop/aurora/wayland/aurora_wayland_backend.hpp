#ifndef AURORA_WAYLAND_BACKEND_HPP
#define AURORA_WAYLAND_BACKEND_HPP
#include "aurora_desktop.hpp"
#include <wayland-server-core.h>
#include <wayland-server-protocol.h>
#include <memory>
#include <unordered_map>
namespace aurora::wayland {
struct WaylandSurface { wl_resource* resource{nullptr}; wl_resource* pending_buffer{nullptr}; int32_t buffer_damage_x{0}; int32_t buffer_damage_y{0}; uint32_t buffer_width{0}; uint32_t buffer_height{0}; uint64_t aurora_window_id{0}; bool committed{false}; };
struct WaylandSeat { wl_resource* seat_resource{nullptr}; wl_resource* pointer_resource{nullptr}; wl_resource* keyboard_resource{nullptr}; wl_resource* focused_surface_resource{nullptr}; uint32_t pointer_serial{0}; uint32_t keyboard_serial{0}; };
class WaylandBackend {
public:
 explicit WaylandBackend(std::shared_ptr<aurora::desktop::AuroraCompositor> compositor); ~WaylandBackend();
 WaylandBackend(const WaylandBackend&)=delete; WaylandBackend& operator=(const WaylandBackend&)=delete;
 bool initialize(const char* socket_name=nullptr); void dispatch_events(int timeout_ms=0); void handle_surface_commit(WaylandSurface* surface); void set_pointer_focus(uint64_t window_id,int32_t surface_x,int32_t surface_y); void set_keyboard_focus(uint64_t window_id); void send_key_event(uint32_t key,uint32_t state); [[nodiscard]] wl_display* get_display() const noexcept{return display_;}
private: void register_globals(); std::shared_ptr<aurora::desktop::AuroraCompositor> compositor_; wl_display* display_{nullptr}; wl_event_loop* event_loop_{nullptr}; wl_global* compositor_global_{nullptr}; wl_global* seat_global_{nullptr}; std::unordered_map<wl_resource*,std::unique_ptr<WaylandSurface>> surfaces_; std::unordered_map<uint64_t,WaylandSurface*> window_surface_map_; WaylandSeat seat_{}; static const wl_compositor_interface compositor_implementation_; static const wl_surface_interface surface_implementation_; static const wl_seat_interface seat_implementation_;
}; }
#endif
