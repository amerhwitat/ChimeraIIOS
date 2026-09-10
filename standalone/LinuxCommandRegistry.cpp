#include "LinuxCommandRegistry.hpp"

namespace chimera::userland {

void LinuxCommandRegistry::add(std::string_view name, CommandClass category,
                               ExecutionMode mode, bool requires_capability) {
    const std::size_t pos = commands_.size();
    commands_.push_back(CommandSpec{std::string(name), category, mode, requires_capability});
    index_.emplace(commands_.back().name, pos);
}

LinuxCommandRegistry::LinuxCommandRegistry() {
    constexpr std::string_view filesystem[] = {"ls","cd","pwd","mkdir","rmdir","touch","cp","mv","rm","ln","readlink","find","locate","updatedb","which","whereis","file","stat","du","df","tree"};
    constexpr std::string_view text[] = {"cat","less","more","grep","sed","awk","cut","paste","sort","uniq","tr","head","tail","wc","diff","patch","split","join","tee"};
    constexpr std::string_view system[] = {"mount","umount","fdisk","lsblk","blkid","dmesg","hexdump","od","sync"};
    constexpr std::string_view process[] = {"ps","top","kill","pkill","pgrep","killall","nice","renice","jobs","fg","bg","nohup"};
    constexpr std::string_view network[] = {"ip","ss","tc","ping","traceroute","route","ifconfig","netstat","dig","nslookup","host","ssh","scp","curl","wget","ftp","telnet"};
    constexpr std::string_view packages[] = {"apt","apt-get","dpkg","dnf","yum","rpm","pacman","zypper","emerge","snap","flatpak"};
    constexpr std::string_view development[] = {"bash","sh","ksh","cc","gcc","g++","make","cmake","ninja","meson","gdb"};
    constexpr std::string_view administration[] = {"sudo","su","login","passwd","chsh","chown","chmod","chgrp","getent","id","whoami"};

    auto add_many = [this](const auto& names, CommandClass category, ExecutionMode mode) {
        for (auto name : names) add(name, category, mode);
    };

    add_many(filesystem, CommandClass::FileSystem, ExecutionMode::AsyncIO);
    add_many(text, CommandClass::Text, ExecutionMode::BoundedParallel);
    add_many(system, CommandClass::System, ExecutionMode::Serial);
    add_many(process, CommandClass::Process, ExecutionMode::Serial);
    add_many(network, CommandClass::Network, ExecutionMode::AsyncIO);
    add_many(packages, CommandClass::Packages, ExecutionMode::AsyncIO);
    add_many(development, CommandClass::Development, ExecutionMode::BoundedParallel);
    add_many(administration, CommandClass::Administration, ExecutionMode::Serial);

    // Privileged operations are capability-gated at the execution layer.
    for (auto& command : commands_) {
        if (command.name == "sudo" || command.name == "mount" || command.name == "umount" ||
            command.name == "fdisk" || command.name == "chown" || command.name == "chmod") {
            command.requires_capability = true;
        }
    }
}

const CommandSpec* LinuxCommandRegistry::find(std::string_view name) const noexcept {
    const auto it = index_.find(std::string(name));
    return it == index_.end() ? nullptr : &commands_[it->second];
}

std::vector<std::string> LinuxCommandRegistry::list(CommandClass category) const {
    std::vector<std::string> result;
    for (const auto& command : commands_) {
        if (command.category == category) result.push_back(command.name);
    }
    std::sort(result.begin(), result.end());
    return result;
}

} // namespace chimera::userland
