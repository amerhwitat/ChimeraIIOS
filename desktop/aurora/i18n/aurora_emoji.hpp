#pragma once
#include <string>
#include <string_view>
#include <vector>
namespace aurora::emoji {
struct Entry{const char* name;const char* glyph;const char* category;};
const std::vector<Entry>& catalog();
const Entry* find(std::string_view);
bool contains_emoji(std::string_view);
std::string replace_aliases(std::string_view);
}