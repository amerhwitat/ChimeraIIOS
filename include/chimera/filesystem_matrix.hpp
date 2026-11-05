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

inline constexpr std::array<FilesystemProfile, 48> kFilesystemMatrix = {{
    {"ext4", SupportMode::CatalogOnly, "POSIX/VFS", "Linux"},
    {"xfs", SupportMode::CatalogOnly, "POSIX/VFS", "Linux/SGI"},
    {"btrfs", SupportMode::CatalogOnly, "POSIX/VFS", "Linux"},
    {"zfs", SupportMode::CatalogOnly, "POSIX/VFS", "OpenZFS"},
    {"jfs", SupportMode::CatalogOnly, "POSIX/VFS", "IBM/AIX"},
    {"jfs2", SupportMode::CatalogOnly, "AIX JFS2 compatibility", "IBM/AIX"},
    {"ufs", SupportMode::CatalogOnly, "POSIX/VFS", "BSD/Unix"},
    {"sysv", SupportMode::CatalogOnly, "POSIX/VFS", "System V/Xenix/Coherent"},
    {"f2fs", SupportMode::CatalogOnly, "POSIX/VFS", "Linux"},
    {"nilfs2", SupportMode::CatalogOnly, "POSIX/VFS", "Linux"},
    {"erofs", SupportMode::CatalogOnly, "POSIX/VFS", "Linux"},
    {"squashfs", SupportMode::CatalogOnly, "POSIX/VFS", "Linux"},
    {"ntfs3", SupportMode::CatalogOnly, "Win32/POSIX bridge", "Windows/Linux"},
    {"fat32", SupportMode::CatalogOnly, "DOS/POSIX bridge", "DOS/Windows"},
    {"iso9660", SupportMode::CatalogOnly, "ISO filesystem", "Optical"},
    {"udf", SupportMode::CatalogOnly, "UDF filesystem", "Optical"},
    {"amiga-ofs", SupportMode::CatalogOnly, "AmigaDOS handler compatibility", "Amiga"},
    {"amiga-ffs", SupportMode::CatalogOnly, "AmigaDOS handler compatibility", "Amiga"},
    {"crossdos", SupportMode::CatalogOnly, "AmigaDOS handler compatibility", "Amiga/DOS"},
    {"hp-ux-vxfs", SupportMode::CatalogOnly, "HP-UX VxFS compatibility", "HP-UX"},
    {"openvms-ods2", SupportMode::CatalogOnly, "RMS/Files-11 compatibility", "OpenVMS"},
    {"openvms-ods5", SupportMode::CatalogOnly, "RMS/Files-11 compatibility", "OpenVMS"},
    {"hfs", SupportMode::CatalogOnly, "POSIX/VFS", "Classic Mac"},
    {"hfsplus", SupportMode::CatalogOnly, "POSIX/VFS", "Apple"},
    {"qnx6", SupportMode::CatalogOnly, "QNX compatibility", "QNX"},
    {"adfs", SupportMode::CatalogOnly, "RISC OS compatibility", "Acorn/RISC OS"},
    {"afs", SupportMode::CatalogOnly, "AFS compatibility", "Unix/Network"},
    {"9p", SupportMode::CatalogOnly, "Plan 9 namespace compatibility", "Plan 9"},
    {"nfs", SupportMode::CatalogOnly, "Network VFS", "Unix"},
    {"smb3", SupportMode::CatalogOnly, "Network VFS", "Windows/Unix"},
    {"gfs2", SupportMode::CatalogOnly, "POSIX/VFS", "Linux cluster"},
    {"ocfs2", SupportMode::CatalogOnly, "POSIX/VFS", "Linux cluster"},
    {"ceph", SupportMode::CatalogOnly, "Network VFS", "Distributed"},
    {"orangefs", SupportMode::CatalogOnly, "Network VFS", "Distributed"},
    {"overlayfs", SupportMode::CatalogOnly, "Union VFS", "Linux"},
    {"proc", SupportMode::CatalogOnly, "Pseudo-filesystem", "Linux"},
    {"sysfs", SupportMode::CatalogOnly, "Pseudo-filesystem", "Linux"},
    {"tmpfs", SupportMode::CatalogOnly, "Memory VFS", "Unix/Linux"},
    {"ramfs", SupportMode::CatalogOnly, "Memory VFS", "Linux"},
    {"ubifs", SupportMode::CatalogOnly, "MTD/flash VFS", "Linux"},
    {"jffs2", SupportMode::CatalogOnly, "MTD/flash VFS", "Linux"},
    {"bfs", SupportMode::CatalogOnly, "POSIX/VFS", "Unix"},
    {"minix", SupportMode::CatalogOnly, "POSIX/VFS", "Unix/Linux"},
    {"befs", SupportMode::CatalogOnly, "POSIX/VFS", "BeOS"},
    {"reiserfs", SupportMode::CatalogOnly, "POSIX/VFS", "Linux"},
    {"hamer2", SupportMode::CatalogOnly, "BSD VFS compatibility", "DragonFly BSD"},
    {"apfs", SupportMode::CatalogOnly, "Apple filesystem compatibility", "Apple"},
    {"qfs", SupportMode::CatalogOnly, "Chimera Native VFS / QFS", "Chimera"}
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
