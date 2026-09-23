#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
namespace aurora::utf8 {
struct CodePoint { char32_t value{}; std::size_t byte_offset{}; std::size_t byte_length{}; };
bool valid(std::string_view);
std::size_t codepoint_count(std::string_view);
std::vector<CodePoint> decode(std::string_view);
std::string encode(char32_t);
std::string sanitize(std::string_view, char32_t replacement=0xFFFD);
bool is_combining(char32_t);
bool is_variation_selector(char32_t);
bool is_emoji(char32_t);
bool is_rtl_codepoint(char32_t);
bool is_whitespace(char32_t);
int display_width(char32_t);
}