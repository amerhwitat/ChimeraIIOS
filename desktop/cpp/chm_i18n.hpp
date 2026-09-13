#pragma once
#include <string_view>
#include <string>
#include <unordered_map>
#include <utility>

namespace chimera::i18n {
enum class Direction { LTR, RTL };
struct Locale { std::string_view id; std::string_view language; Direction direction; std::string_view script; };
inline constexpr Locale ArabicSA{"ar-SA", "ar", Direction::RTL, "Arabic"};
inline constexpr Locale EnglishUS{"en-US", "en", Direction::LTR, "Latin"};
inline Direction direction_for(std::string_view locale) { return locale.rfind("ar", 0) == 0 || locale.rfind("he", 0) == 0 ? Direction::RTL : Direction::LTR; }
inline std::string mirror_text_controls(std::string_view text, Direction direction) { return direction == Direction::RTL ? std::string{text} : std::string{text}; }
}
