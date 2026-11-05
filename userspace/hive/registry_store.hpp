#pragma once
#include <map>
#include <mutex>
#include <string>
#include <vector>
namespace chimera::hive {
class RegistryStore {
public:
 explicit RegistryStore(std::string directory);
 bool open();
 bool get(const std::string&,std::string&) const;
 std::vector<std::pair<std::string,std::string>> entries() const;
 bool set(const std::string&,const std::string&);
 bool set_many(const std::vector<std::pair<std::string,std::string>>&);
 bool erase(const std::string&);
 bool compact();
 const std::string& last_error() const noexcept{return error_;}
private:
 bool recover_locked(); bool append_locked(const std::string&); bool write_snapshot_locked();
 std::string directory_,error_; mutable std::mutex mutex_;
 std::map<std::string,std::string> values_; unsigned long long sequence_{0};
};
}