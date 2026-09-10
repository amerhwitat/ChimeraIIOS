#include <cassert>
#include "chimera/filesystem_matrix.hpp"

int main() {
    using namespace chimera::filesystem;
    const auto &m = filesystem_matrix();

    // Native / compatible Unix-family filesystems.
    assert(m.has("ext4"));
    assert(m.has("xfs"));
    assert(m.has("btrfs"));
    assert(m.has("jfs"));
    assert(m.has("jfs2"));
    assert(m.has("ufs"));
    assert(m.has("sysv"));
    assert(m.has("zfs"));

    // Legacy / foreign filesystem families.
    assert(m.has("amiga-ofs"));
    assert(m.has("amiga-ffs"));
    assert(m.has("crossdos"));
    assert(m.has("hp-ux-vxfs"));
    assert(m.has("openvms-ods2"));
    assert(m.has("openvms-ods5"));

    // The matrix must distinguish POSIX VFS semantics from native on-disk
    // compatibility and must not falsely claim native write support.
    assert(m.at("openvms-ods5").semantic_layer == "RMS/Files-11 compatibility");
    assert(m.at("amiga-ffs").semantic_layer == "AmigaDOS handler compatibility");
    assert(m.at("hp-ux-vxfs").mode == SupportMode::UserspaceCompatibility);

    return 0;
}
