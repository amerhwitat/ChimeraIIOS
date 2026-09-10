#include <cassert>
#include "chimera/filesystem_matrix.hpp"

int main() {
    using namespace chimera::filesystem;
    const auto &m = filesystem_matrix;

    assert(m.has("ext4"));
    assert(m.has("xfs"));
    assert(m.has("btrfs"));
    assert(m.has("jfs"));
    assert(m.has("jfs2"));
    assert(m.has("ufs"));
    assert(m.has("sysv"));
    assert(m.has("zfs"));
    assert(m.has("amiga-ofs"));
    assert(m.has("amiga-ffs"));
    assert(m.has("crossdos"));
    assert(m.has("hp-ux-vxfs"));
    assert(m.has("openvms-ods2"));
    assert(m.has("openvms-ods5"));
    assert(m.at("openvms-ods5").semantic_layer == "RMS/Files-11 compatibility");
    assert(m.at("amiga-ffs").semantic_layer == "AmigaDOS handler compatibility");
    assert(m.at("hp-ux-vxfs").mode == SupportMode::UserspaceCompatibility);
    return 0;
}
