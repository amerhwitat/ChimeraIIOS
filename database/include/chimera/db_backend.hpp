#pragma once
#include <cstdint>
#include <string_view>

namespace chimera::db {

enum class Model : std::uint8_t { Relational, EmbeddedRelational, Analytical, KeyValue, Document, WideColumn, Graph, TimeSeries };
struct Backend { std::string_view name; Model model; std::string_view license; std::string_view integration; };

inline constexpr Backend kBackends[] = {
 {"MariaDB Community Server",Model::Relational,"GPLv2","client/service"},
 {"PostgreSQL",Model::Relational,"PostgreSQL License","client/service"},
 {"SQLite",Model::EmbeddedRelational,"Public Domain","in-process"},
 {"DuckDB",Model::Analytical,"MIT","in-process"},
 {"RocksDB",Model::KeyValue,"Apache-2.0/GPLv2","storage-engine"},
 {"LevelDB",Model::KeyValue,"BSD-3-Clause","storage-engine"},
 {"Valkey",Model::KeyValue,"BSD-3-Clause","service"},
 {"Apache Cassandra",Model::WideColumn,"Apache-2.0","cluster/service"},
 {"Apache CouchDB",Model::Document,"Apache-2.0","service"}
};
constexpr std::size_t backend_count() noexcept { return sizeof(kBackends)/sizeof(kBackends[0]); }
const Backend* find_backend(std::string_view) noexcept;

} // namespace chimera::db
