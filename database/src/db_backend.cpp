#include "chimera/db_backend.hpp"
namespace chimera::db {
const Backend* find_backend(std::string_view name) noexcept {
    for (const auto& backend : kBackends) if (backend.name == name) return &backend;
    return nullptr;
}
}
