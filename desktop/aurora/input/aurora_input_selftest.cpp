#include "aurora_input_router.hpp"
#include "../i18n/aurora_locale.hpp"
#include <cassert>
#include <string>

int main() {
    aurora::input::InputRouter router;
    bool context = false;
    std::string command;
    router.set_command_sink([&](const std::string& c, uint64_t){ command = c; if(c=="context-menu") context=true; });
    router.set_event_sink([](const aurora::input::Event&){});
    router.set_window_policy(42, {});
    router.focus_window(42);
    router.register_shortcut({65u, 2u, "select-all"});

    aurora::input::Event right{};
    right.type = aurora::input::Type::MouseButtonDown;
    right.button = aurora::input::MouseButton::Right;
    router.route(42, right);
    assert(context);

    aurora::input::Event key{};
    key.type = aurora::input::Type::KeyDown;
    key.key = 65u;
    key.modifiers = 2u;
    router.route(42, key);
    assert(command == "select-all");

    const auto ar = aurora::i18n::parse_locale("ar-JO");
    assert(ar.direction == aurora::i18n::Direction::RTL);
    assert(aurora::i18n::logical_edge(ar, true) == "right");

    const auto en = aurora::i18n::parse_locale("en-US");
    assert(en.direction == aurora::i18n::Direction::LTR);
    assert(aurora::i18n::logical_edge(en, true) == "left");
    return 0;
}
