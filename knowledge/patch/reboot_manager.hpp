#pragma once
#include <filesystem>
#include <string>
namespace chm::reboot { struct Request { bool required=false; std::string reason; std::string artifact; }; std::filesystem::path state_path(); bool save(const Request&); Request load(); bool mark_later(); bool clear(); }
