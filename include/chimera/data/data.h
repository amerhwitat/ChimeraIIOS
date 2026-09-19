#pragma once
#include <string>
#include <vector>

namespace chimera::data {
struct Provider {
  std::string id;
  std::string kind;
  std::string role;
  std::string binary;
  std::string license;
  bool available = false;
};
std::vector<Provider> built_in_providers();
std::vector<Provider> available_providers();
std::vector<Provider> filter_by_kind(const std::vector<Provider>& providers, const std::string& kind);
}
