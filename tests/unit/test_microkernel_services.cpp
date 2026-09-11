#include <cassert>
#include "chimera/microkernel_services.hpp"
int main() {
    using namespace chimera::kernel;
    assert(service_count() >= 11);
    assert(find_service("scheduler") != nullptr);
    assert(find_service("database") != nullptr);
    assert(find_service("missing") == nullptr);
    return 0;
}
