#include "../../userspace/hive/registry_store.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>
#include <chrono>
int main(){auto d=(std::filesystem::temp_directory_path()/("hive-test-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()))).string();std::filesystem::remove_all(d);{chimera::hive::RegistryStore r(d);assert(r.open());assert(r.set_many({{"system/theme","glass"},{"network/domain","example.test"},{"empty/value",""}}));assert(!r.set("../escape","bad"));assert(!r.set_many({{"path/collision","value"},{"path/collision/child","value"}}));std::string v;assert(r.get("system/theme",v)&&v=="glass");assert(r.erase("network/domain"));assert(r.compact());}{std::ofstream wal(d+"/registry.wal",std::ios::app);wal<<"S 4 6576696c 7374616c65\n";}{chimera::hive::RegistryStore r(d);assert(r.open());std::string v;assert(r.get("system/theme",v)&&v=="glass");assert(!r.get("network/domain",v));assert(!r.get("evil",v));assert(r.get("empty/value",v)&&v.empty());assert(r.set("system/theme","dark"));}{chimera::hive::RegistryStore r(d);assert(r.open());std::string v;assert(r.get("system/theme",v)&&v=="dark");}std::filesystem::remove_all(d);}