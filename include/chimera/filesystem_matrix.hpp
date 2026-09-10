#pragma once

#include <array>
#include <string_view>

namespace chimera::filesystem {

enum class SupportMode {
    NativeReadWrite,
    NativeReadOnly,
    UserspaceCompatibility,
    EmulatorOnly
};

struct FilesystemProfile {
    std::string_view name;
    SupportMode mode;
    std::string_view semantic_layer;
    std::string_view family;
};

inline constexpr std::array<FilesystemProfile, 22> kFilesystemMatrix = {{
    {"ext4", SupportMode::NativeReadWrite, "POSIX/VFS", "Linux"},
    {"xfs", SupportMode::NativeReadWrite, "POSIX/VFS", "Linux/SGI"},
    {"btrfs", SupportMode::NativeReadWrite, "POSIX/VFS", "Linux"},
    {"zfs", SupportMode::NativeReadWrite, "POSIX/VFS", "OpenZFS"},
    {"jfs", SupportMode::NativeReadWrite, "POSIX/VFS", "IBM/AIX"},
    {"jfs2", SupportMode::UserspaceCompatibility, "AIX JFS2 compatibility", "IBM/AIX"},
    {"ufs", SupportMode::NativeReadWrite, "POSIX/VFS", "BSD/Unix"},
    {"sysv", SupportMode::NativeReadOnly, "POSIX/VFS", "System V/Xenix/Coherent"},
    {"f2fs", SupportMode::NativeReadWrite, "POSIX/VFS", "Linux"},
    {"nilfs2", SupportMode::NativeReadWrite, "POSIX/VFS", "Linux"},
    {"erofs", SupportMode::NativeReadOnly, "POSIX/VFS", "Linux"},
    {"squashfs", SupportMode::NativeReadOnly, "POSIX/VFS", "Linux"},
    {"ntfs3", SupportMode::NativeReadWrite, "Win32/POSIX bridge", "Windows/Linux"},
    {"fat32", SupportMode::NativeReadWrite, "DOS/POSIX bridge", "DOS/Windows"},
    {"iso9660", SupportMode::NativeReadOnly, "ISO filesystem", "Optical"},
    {"udf", SupportMode::NativeReadWrite, "UDF filesystem", "Optical"},
    {"amiga-ofs", SupportMode::UserspaceCompatibility, "AmigaDOS handler compatibility", "Amiga"},
    {"amiga-ffs", SupportMode::UserspaceCompatibility, "AmigaDOS handler compatibility", "Amiga"},
    {"crossdos", SupportMode::UserspaceCompatibility, "AmigaDOS handler compatibility", "Amiga/DOS"},
    {"hp-ux-vxfs", SupportMode::UserspaceCompatibility, "HP-UX VxFS compatibility", "HP-UX"},
    {"openvms-ods2", SupportMode::UserspaceCompatibility, "RMS/Files-11 compatibility", "OpenVMS"},
    {"openvms-ods5", SupportMode::UserspaceCompatibility, "RMS/Files-11 compatibility", "OpenVMS"}
}};

class FilesystemMatrix {
public:
    constexpr bool has(std::string_view name) const noexcept {
        for (const auto &p : kFilesystemMatrix) if (p.name == name) return true;
        return false;
    }

    constexpr const FilesystemProfile &at(std::string_view name) const noexcept {
        for (const auto &p : kFilesystemMatrix) if (p.name == name) return p;
        return kFilesystemMatrix[0];
    }
};

inline constexpr FilesystemMatrix filesystem_matrix{};

} // namespace chimera::filesystem
