#pragma once
#include <string>
#include <unordered_map>
#include <mutex>
namespace chimera::hive {
class Registry { std::unordered_map<std::string,std::string> data_; mutable std::mutex m_; public:
 void set(std::string k,std::string v){std::lock_guard<std::mutex> g(m_);data_[std::move(k)]=std::move(v);} 
 bool get(const std::string& k,std::string& v) const {std::lock_guard<std::mutex> g(m_);auto i=data_.find(k);if(i==data_.end())return false;v=i->second;return true;}
};
}
