#pragma once
#include <string_view>
namespace aurora::icons{struct Icon{const char* name;const char* svg;};const Icon* find(std::string_view);}