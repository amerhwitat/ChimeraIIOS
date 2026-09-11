#include "chimera/microkernel_services.hpp"
namespace chimera::kernel {
const ServiceDescriptor* find_service(std::string_view name) noexcept {
    for (const auto& service : kServices) if (service.name == name) return &service;
    return nullptr;
}
}
