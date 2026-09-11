#pragma once
#include <string>
#include <vector>
namespace iso_tool { struct ToolchainResult { std::string name, executable, environment, path, status; }; std::vector<ToolchainResult> DetectToolchains(); std::string ToolchainsJson(); }
