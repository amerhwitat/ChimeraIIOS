#include "aurora_input_router.hpp"
#include <algorithm>
#include <utility>

namespace aurora::input {

void InputRouter::set_window_policy(uint64_t window_id, WindowPolicy policy) {
    policies_[window_id] = policy;
}

void InputRouter::focus_window(uint64_t window_id) {
    focused_window_ = window_id;
}

void InputRouter::register_shortcut(Shortcut shortcut) {
    shortcuts_.push_back(std::move(shortcut));
}

bool InputRouter::dispatch_shortcut(uint64_t window_id, const Event& event) const {
    if (event.type != Type::KeyDown) return false;
    for (const auto& shortcut : shortcuts_) {
        if (shortcut.key == event.key && shortcut.modifiers == event.modifiers) {
            if (command_sink_) command_sink_(shortcut.command, window_id);
            return true;
        }
    }
    return false;
}

void InputRouter::route(uint64_t window_id, const Event& event) {
    const auto it = policies_.find(window_id);
    const WindowPolicy policy = (it == policies_.end()) ? WindowPolicy{} : it->second;

    if (event.type == Type::KeyDown || event.type == Type::KeyUp || event.type == Type::TextInput) {
        if (!policy.accept_keyboard) return;
    }
    if (event.type == Type::MouseMove || event.type == Type::MouseButtonDown ||
        event.type == Type::MouseButtonUp || event.type == Type::MouseWheel ||
        event.type == Type::Touch || event.type == Type::Gesture || event.type == Type::Tablet) {
        if (!policy.accept_mouse) return;
    }
    if (event.type == Type::MouseButtonDown && event.button == MouseButton::Right && policy.context_menu) {
        if (command_sink_) command_sink_("context-menu", window_id);
    }
    if (event.type == Type::KeyDown && policy.context_menu &&
        ((event.key == 121u && (event.modifiers & 1u)) || event.key == 93u)) {
        if (command_sink_) command_sink_("context-menu", window_id);
    }
    if (event.type == Type::KeyDown && dispatch_shortcut(window_id, event)) return;
    if (event_sink_) event_sink_(event);
}

} // namespace aurora::input
