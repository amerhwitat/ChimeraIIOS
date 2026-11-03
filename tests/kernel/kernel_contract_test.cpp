#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <initializer_list>
#include <string>
#include <vector>
#include "chimera/cpio_newc.h"
#include "chimera/vfs.h"
#include "chimera/interrupt.h"
#include "chimera/service.h"

namespace {
struct ArchiveEntry {
    const char* name;
    uint32_t mode;
    const char* data;
    uint32_t size;
    bool crc;
    uint32_t check_override;
};
void pad4(std::vector<uint8_t>& out) {
    while (out.size() & 3u) out.push_back(0);
}
void append_entry(std::vector<uint8_t>& out, const ArchiveEntry& entry) {
    char header[111]{};
    std::memcpy(header, entry.crc ? "070702" : "070701", 6);
    const uint32_t namesize = static_cast<uint32_t>(std::strlen(entry.name) + 1u);
    uint32_t sum = 0;
    for (uint32_t i = 0; i < entry.size; ++i)
        sum += static_cast<uint8_t>(entry.data[i]);
    const uint32_t fields[13] = {
        1u, entry.mode, 0u, 0u, 1u, 0u, entry.size,
        0u, 0u, 0u, 0u, namesize,
        entry.check_override == UINT32_MAX ? (entry.crc ? sum : 0u) : entry.check_override
    };
    for (uint32_t i = 0; i < 13u; ++i)
        std::snprintf(header + 6u + i * 8u, 9u, "%08X", fields[i]);
    out.insert(out.end(), header, header + 110);
    out.insert(out.end(), entry.name, entry.name + namesize);
    pad4(out);
    if (entry.size)
        out.insert(out.end(), entry.data, entry.data + entry.size);
    pad4(out);
}
struct Visitor {
    std::vector<std::string> paths;
    uint32_t files = 0;
    uint32_t directories = 0;
};
int visit(void* opaque, const char* path, uint32_t mode, uint32_t,
          uint32_t, const void*, uint32_t) {
    auto& visitor = *static_cast<Visitor*>(opaque);
    for (const auto& old : visitor.paths)
        if (old == path) return -1;
    visitor.paths.emplace_back(path);
    if ((mode & 0170000u) == 0100000u) ++visitor.files;
    if ((mode & 0170000u) == 0040000u) ++visitor.directories;
    return 0;
}
std::vector<uint8_t> archive(std::initializer_list<ArchiveEntry> entries) {
    std::vector<uint8_t> out;
    for (const auto& entry : entries) append_entry(out, entry);
    append_entry(out, {"TRAILER!!!", 0u, "", 0u, false, UINT32_MAX});
    return out;
}
}

int main() {
    static_assert(offsetof(chimera_interrupt_frame, vector) == 120u);
    static_assert(offsetof(chimera_interrupt_frame, cpu_frame) == 128u);

    chimera_interrupt_frame frame{};
    frame.cpu_frame[0] = 0x1111222233334444ull;
    frame.cpu_frame[1] = 0x23u;
    frame.cpu_frame[2] = 0xDEADu;
    assert(chimera_interrupt_frame_rip(&frame, 6u) == 0x1111222233334444ull);
    assert(chimera_interrupt_frame_cs(&frame, 6u) == 0x23u);
    assert(chimera_interrupt_frame_rip(&frame, 13u) == 0x23u);
    assert(chimera_interrupt_frame_cs(&frame, 13u) == 0xDEADu);
    assert(chimera_interrupt_vector_has_error_code(14u) == 1u);
    assert(chimera_interrupt_vector_has_error_code(0x80u) == 0u);

    const char* storage_deps[] = {"device"};
    chimera_service_manifest services[] = {
        {CHIMERA_SERVICE_ABI, "desktop", CHM_SVC_DECLARED, CHM_RESTART_FAILURE, 0, 1, storage_deps},
        {CHIMERA_SERVICE_ABI, "device", CHM_SVC_DECLARED, CHM_RESTART_FAILURE, 1, 0, nullptr},
        {CHIMERA_SERVICE_ABI, "storage", CHM_SVC_DECLARED, CHM_RESTART_FAILURE, 1, 1, storage_deps}
    };
    const char* ordered[3]{};
    chimera_service_plan plan{0, 3, ordered};
    assert(chimera_service_validate(services, 3) == 0);
    assert(chimera_service_resolve(services, 3, &plan) == 0);
    assert(plan.count == 3);
    assert(ordered[0] == services[1].id);
    assert(ordered[1] == services[0].id || ordered[1] == services[2].id);

    const char* cycle_a[] = {"cycle-b"};
    const char* cycle_b[] = {"cycle-a"};
    chimera_service_manifest cycle[] = {
        {CHIMERA_SERVICE_ABI, "cycle-a", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 0, 1, cycle_a},
        {CHIMERA_SERVICE_ABI, "cycle-b", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 0, 1, cycle_b}
    };
    assert(chimera_service_resolve(cycle, 2, &plan) == -6);
    assert(plan.count == 0);

    chimera_service_manifest null_dependencies[] = {
        {CHIMERA_SERVICE_ABI, "bad", CHM_SVC_DECLARED, CHM_RESTART_NEVER, 0, 1, nullptr}
    };
    assert(chimera_service_validate(null_dependencies, 1) == -2);
    assert(chimera_service_set_state("chimera.device", CHM_SVC_DECLARED) == 0);
    assert(chimera_service_get_state("chimera.device") == CHM_SVC_DECLARED);
    assert(chimera_service_set_state("chimera.device", CHM_SVC_RUNNING) == 0);
    assert(chimera_service_get_state("chimera.device") == CHM_SVC_RUNNING);
    assert(chimera_service_set_state("bad", 999u) == -1);

    const auto good = archive({
        {"./", 0040755u, "", 0u, false, UINT32_MAX},
        {"./init", 0100755u, "hello", 5u, false, UINT32_MAX},
        {"./crc", 0100644u, "ok", 2u, true, UINT32_MAX},
        {"./etc/", 0040755u, "", 0u, false, UINT32_MAX},
        {"./etc/config", 0100644u, "conf", 4u, false, UINT32_MAX}
    });
    Visitor visitor;
    chimera_cpio_newc_ops ops{visit};
    chimera_cpio_newc_summary summary{};
    assert(chimera_cpio_newc_walk(good.data(), good.size(), &ops, &visitor, &summary) == 0);
    assert(summary.abi == CHIMERA_CPIO_NEWC_ABI);
    assert(summary.entries == 5u && summary.regular_files == 3u && summary.directories == 2u);
    assert(summary.data_bytes == 11u && visitor.files == 3u && visitor.directories == 2u);
    assert(visitor.paths[0].empty());
    assert(visitor.paths[1] == "init");

    chimera_vfs_tree published_tree{};
    chimera_vfs_node published_nodes[8]{};
    assert(chimera_vfs_mount_newc(good.data(), good.size(), &published_tree,
                                  published_nodes, 8u) == 0);
    assert(chimera_vfs_root() == &published_tree);
    const chimera_vfs_node *init_node = chimera_vfs_lookup("/init");
    assert(init_node && init_node->kind == CHIMERA_VFS_REGULAR);
    assert(init_node->size == 5u && std::memcmp(init_node->data, "hello", 5u) == 0);
    const chimera_vfs_node *etc_node = chimera_vfs_lookup("etc");
    assert(etc_node && etc_node->kind == CHIMERA_VFS_DIRECTORY);
    const chimera_vfs_node *config_node = chimera_vfs_lookup("/etc/config");
    assert(config_node && config_node->size == 4u);

    Visitor bad_path;
    const auto empty_name = archive({{"", 0100644u, "x", 1u, false, UINT32_MAX}});
    assert(chimera_cpio_newc_walk(empty_name.data(), empty_name.size(), &ops, &bad_path, &summary) == -4);
    const auto traversal = archive({{"../escape", 0100644u, "x", 1u, false, UINT32_MAX}});
    assert(chimera_cpio_newc_walk(traversal.data(), traversal.size(), &ops, &bad_path, &summary) == -4);
    const auto absolute = archive({{"/etc/passwd", 0100644u, "x", 1u, false, UINT32_MAX}});
    assert(chimera_cpio_newc_walk(absolute.data(), absolute.size(), &ops, &bad_path, &summary) == -4);

    const auto bad_crc = archive({{"./init", 0100755u, "hello", 5u, true, 0u}});
    assert(chimera_cpio_newc_walk(bad_crc.data(), bad_crc.size(), &ops, &bad_path, &summary) == -7);
    const auto unsupported = archive({{"./dev/null", 0020666u, "", 0u, false, UINT32_MAX}});
    assert(chimera_cpio_newc_walk(unsupported.data(), unsupported.size(), &ops, &bad_path, &summary) == -6);
    const auto duplicate = archive({
        {"./init", 0100755u, "a", 1u, false, UINT32_MAX},
        {"./init", 0100755u, "b", 1u, false, UINT32_MAX}
    });
    Visitor duplicate_visitor;
    assert(chimera_cpio_newc_walk(duplicate.data(), duplicate.size(), &ops, &duplicate_visitor, &summary) == -9);
    assert(summary.entries == 1u);

    auto truncated = good;
    truncated.pop_back();
    assert(chimera_cpio_newc_walk(truncated.data(), truncated.size(), &ops, &bad_path, &summary) == -5);

    chimera_vfs_tree rejected_tree{};
    chimera_vfs_node rejected_nodes[8]{};
    assert(chimera_vfs_mount_newc(traversal.data(), traversal.size(), &rejected_tree,
                                  rejected_nodes, 8u) != 0);
    assert(chimera_vfs_root() == &published_tree);
    assert(chimera_vfs_lookup("/init") == init_node);

    const auto missing_parent = archive({
        {"./etc/settings", 0100644u, "x", 1u, false, UINT32_MAX}
    });
    chimera_vfs_tree orphan_tree{};
    chimera_vfs_node orphan_nodes[8]{};
    assert(chimera_vfs_mount_newc(missing_parent.data(), missing_parent.size(),
                                  &orphan_tree, orphan_nodes, 8u) != 0);
    assert(chimera_vfs_root() == &published_tree);
    return 0;
}
