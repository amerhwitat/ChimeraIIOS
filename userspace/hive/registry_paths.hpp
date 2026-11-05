#pragma once
#include <cstdlib>
#include <filesystem>
#include <string>

namespace chimera::hive::paths {
inline std::string env(const char* name) {
    const char* value=std::getenv(name);
    return value && *value ? std::string(value) : std::string();
}
inline std::string registry_directory() {
    if (auto p=env("CHIMERA_HIVE_DIR"); !p.empty()) return p;
#ifdef _WIN32
    if (auto p=env("LOCALAPPDATA"); !p.empty()) return (std::filesystem::path(p)/"Chimera"/"Hive").string();
    if (auto p=env("USERPROFILE"); !p.empty()) return (std::filesystem::path(p)/"AppData"/"Local"/"Chimera"/"Hive").string();
    return "C:/ProgramData/Chimera/Hive";
#elif defined(__APPLE__)
    if (auto p=env("HOME"); !p.empty()) return (std::filesystem::path(p)/"Library"/"Application Support"/"Chimera"/"Hive").string();
    return "/Library/Application Support/Chimera/Hive";
#else
    if (auto p=env("XDG_DATA_HOME"); !p.empty()) return (std::filesystem::path(p)/"chimera"/"hive").string();
    if (auto p=env("HOME"); !p.empty()) return (std::filesystem::path(p)/".local"/"share"/"chimera"/"hive").string();
    return "/var/lib/chimera/hive";
#endif
}
inline std::string settings_file() {
    if (auto p=env("CHIMERA_SETTINGS_FILE"); !p.empty()) return p;
#ifdef _WIN32
    if (auto p=env("APPDATA"); !p.empty()) return (std::filesystem::path(p)/"Chimera"/"settings.conf").string();
    if (auto p=env("USERPROFILE"); !p.empty()) return (std::filesystem::path(p)/"AppData"/"Roaming"/"Chimera"/"settings.conf").string();
    return "C:/ProgramData/Chimera/settings.conf";
#elif defined(__APPLE__)
    if (auto p=env("HOME"); !p.empty()) return (std::filesystem::path(p)/"Library"/"Preferences"/"Chimera"/"settings.conf").string();
    return "/Library/Preferences/Chimera/settings.conf";
#else
    if (auto p=env("XDG_CONFIG_HOME"); !p.empty()) return (std::filesystem::path(p)/"chimera"/"settings.conf").string();
    if (auto p=env("HOME"); !p.empty()) return (std::filesystem::path(p)/".config"/"chimera"/"settings.conf").string();
    return "/etc/chimera/settings.conf";
#endif
}
}
