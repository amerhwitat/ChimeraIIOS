#pragma once
#include <filesystem>
#include <string>
#include <vector>
namespace iso_tool { struct SourceFile{std::filesystem::path path;std::string language;}; std::vector<SourceFile> ScanPythonParity(const std::filesystem::path& root); std::string LanguageOf(const std::filesystem::path& file); }
