#include "aurora_locale.hpp"
#include <algorithm>
#include <cctype>
#include <sstream>

namespace aurora::i18n {

static std::string lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return char(std::tolower(c)); });
    return s;
}

bool is_rtl(const std::string& language) {
    const auto l = lower(language);
    return l=="ar" || l=="arc" || l=="dv" || l=="fa" || l=="he" || l=="khw" ||
           l=="nqo" || l=="ps" || l=="syr" || l=="ug" || l=="ur" || l=="yi";
}

Direction direction_for_language(const std::string& language) {
    return is_rtl(language) ? Direction::RTL : Direction::LTR;
}

Locale parse_locale(const std::string& tag) {
    Locale out;
    out.tag = tag;
    std::string part;
    std::stringstream ss(tag);
    std::vector<std::string> p;
    while (std::getline(ss, part, '-')) p.push_back(part);
    if (!p.empty()) out.language = lower(p[0]);
    for (size_t i=1; i<p.size(); ++i) {
        if (p[i].size()==4) out.script = p[i];
        else if (p[i].size()==2 || p[i].size()==3) out.region = p[i];
    }
    out.direction = direction_for_language(out.language);
    return out;
}

std::string resolve_direction(const Locale& locale, Direction requested) {
    const Direction d = requested == Direction::Auto ? locale.direction : requested;
    return d == Direction::RTL ? "rtl" : "ltr";
}

std::string logical_edge(const Locale& locale, bool start) {
    const bool rtl = locale.direction == Direction::RTL;
    const bool physical_left = start ? !rtl : rtl;
    return physical_left ? "left" : "right";
}

} // namespace aurora::i18n
