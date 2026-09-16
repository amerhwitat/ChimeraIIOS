#include "chimera/data/data.h"
#include <cstdlib>

namespace chimera::data {
static bool has_binary(const std::string& name) {
#ifdef _WIN32
  const std::string cmd = "where " + name + " >NUL 2>NUL";
#else
  const std::string cmd = "command -v " + name + " >/dev/null 2>&1";
#endif
  return std::system(cmd.c_str()) == 0;
}

std::vector<Provider> built_in_providers() {
  return {
    {"sqlite","sql","embedded","sqlite3","Public Domain"},
    {"postgresql","sql","server","psql","PostgreSQL License"},
    {"mariadb","sql","server","mariadb","GPL-2.0"},
    {"duckdb","sql","embedded-analytics","duckdb","MIT"},
    {"cassandra","nosql-wide-column","distributed-server","cqlsh","Apache-2.0"},
    {"egeria","mdm-metadata","governance-service","egeria","Apache-2.0"},
    {"atlas","metadata","hadoop-governance","atlas","Apache-2.0"},
    {"hdfs","hadoop","storage","hdfs","Apache-2.0"},
    {"yarn","hadoop","resource-management","yarn","Apache-2.0"},
    {"hive","hadoop","sql-warehouse","hive","Apache-2.0"},
    {"hbase","hadoop","nosql","hbase","Apache-2.0"},
    {"spark","hadoop","distributed-compute","spark-submit","Apache-2.0"},
    {"tez","hadoop","dag-execution","tez","Apache-2.0"},
    {"openstack","cloud","infrastructure","openstack","Apache-2.0"}
  };
}

std::vector<Provider> available_providers() {
  auto result = built_in_providers();
  for (auto& p : result) p.available = has_binary(p.binary);
  return result;
}

std::vector<Provider> filter_by_kind(const std::vector<Provider>& providers, const std::string& kind) {
  std::vector<Provider> out;
  for (const auto& p : providers) if (p.kind == kind) out.push_back(p);
  return out;
}
}
