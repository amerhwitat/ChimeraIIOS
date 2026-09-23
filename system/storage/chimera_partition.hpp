#pragma once
#include <cstdint>
#include <string>
#include <vector>
namespace chimera::storage {
struct Partition { uint32_t number{}; uint64_t start_lba{}; uint64_t sectors{}; uint8_t mbr_type{}; std::string type_guid; std::string name; bool bootable{}; };
struct Disk { uint64_t bytes{}; uint32_t sector_size{512}; std::string label; std::string disk_guid; std::vector<Partition> partitions; };
bool inspect(const std::string&,Disk&,std::string&);
bool write_mbr(const std::string&,const std::vector<Partition>&,std::string&);
bool write_gpt(const std::string&,const std::vector<Partition>&,const std::string&,std::string&);
bool create_partition(const std::string&,const std::string&,uint64_t,uint64_t,uint8_t,const std::string&,const std::string&,std::string&);
bool delete_partition(const std::string&,uint32_t,std::string&);
bool wipe_partition_table(const std::string&,std::string&);
bool confirmation_required(const std::string&);
std::string format_bytes(uint64_t);
void print_disk(const Disk&,std::string&);
}