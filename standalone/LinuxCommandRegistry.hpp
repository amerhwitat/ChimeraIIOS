#pragma once

#include <algorithm>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace chimera::userland {

enum class CommandClass { FileSystem, Text, System, Process, Network, Packages, Development, Administration };

enum class ExecutionMode { Serial, BoundedParallel, AsyncIO };

struct CommandSpec {
    std::string name;
    CommandClass category;
    ExecutionMode mode;
    bool requires_capability{false};
};

class LinuxCommandRegistry final {
public:
    LinuxCommandRegistry();

    [[nodiscard]] const CommandSpec* find(std::string_view name) const noexcept;
    [[nodiscard]] std::vector<std::string> list(CommandClass category) const;
    [[nodiscard]] const std::vector<CommandSpec>& all() const noexcept { return commands_; }

private:
    std::vector<CommandSpec> commands_;
    std::unordered_map<std::string, std::size_t> index_;

    void add(std::string_view name, CommandClass category,
             ExecutionMode mode = ExecutionMode::Serial,
             bool requires_capability = false);
};

} // namespace chimera::userland
