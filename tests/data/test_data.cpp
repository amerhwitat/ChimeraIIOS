#include "chimera/data/data.h"
#include <cassert>
int main() {
  const auto all = chimera::data::built_in_providers();
  assert(all.size() >= 13);
  const auto sql = chimera::data::filter_by_kind(all, "sql");
  assert(sql.size() >= 4);
  const auto available = chimera::data::available_providers();
  assert(available.size() == all.size());
  return 0;
}
