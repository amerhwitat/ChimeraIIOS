#pragma once
#include <string>
#include <vector>
namespace aurora::i18n {
enum class Direction { LTR, RTL, Auto };
struct Locale {
    std::string tag;
    std::string language;
    std::string script;
    std::string region;
    Direction direction{Direction::Auto};
};
Direction direction_for_language(const std::string& language);
bool is_rtl(const std::string& language);
Locale parse_locale(const std::string& tag);
std::string resolve_direction(const Locale& locale, Direction requested = Direction::Auto);
std::string logical_edge(const Locale& locale, bool start);
}
