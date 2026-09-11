#include <cassert>
#include "chimera/db_backend.hpp"
int main() {
    using namespace chimera::db;
    assert(backend_count() >= 9);
    assert(find_backend("MariaDB Community Server") != nullptr);
    assert(find_backend("PostgreSQL") != nullptr);
    assert(find_backend("SQLite") != nullptr);
    assert(find_backend("Valkey") != nullptr);
    return 0;
}
