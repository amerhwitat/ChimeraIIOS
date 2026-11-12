#include <cassert>
#include "chimera/db_backend.hpp"
int main() {
    using namespace chimera::db;
    assert(backend_count() >= 11);
    assert(find_backend("MariaDB Community Server") != nullptr);
    assert(find_backend("PostgreSQL") != nullptr);
    assert(find_backend("Firebird") != nullptr);
    assert(find_backend("MySQL Community Server") != nullptr);
    assert(find_backend("SQLite") != nullptr);
    assert(find_backend("Valkey") != nullptr);
    return 0;
}
