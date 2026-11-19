#include "chimera/initramfs_newc.h"
#include "chimera/initramfs_fs.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <vector>

static void hexfield(std::vector<uint8_t>& out, uint32_t value) {
    static const char digits[] = "0123456789abcdef";
    for (int i = 7; i >= 0; --i) out.push_back((uint8_t)digits[(value >> (i * 4)) & 15u]);
}
static void pad4(std::vector<uint8_t>& out) { while (out.size() & 3u) out.push_back(0); }
static void append(std::vector<uint8_t>& out, const char* name, const char* data,
                   uint32_t mode, bool crc = false) {
    const uint32_t n = (uint32_t)strlen(name) + 1u;
    const uint32_t z = data ? (uint32_t)strlen(data) : 0u;
    uint32_t sum = 0;
    for (uint32_t i = 0; i < z; ++i) sum += (uint8_t)data[i];
    const char* magic = crc ? "070702" : "070701";
    out.insert(out.end(), magic, magic + 6);
    hexfield(out, 1); hexfield(out, mode); hexfield(out, 0); hexfield(out, 0);
    hexfield(out, 1); hexfield(out, 0); hexfield(out, z); hexfield(out, 0);
    hexfield(out, 0); hexfield(out, 0); hexfield(out, 0); hexfield(out, n);
    hexfield(out, crc ? sum : 0);
    out.insert(out.end(), name, name + n); pad4(out);
    if (z) out.insert(out.end(), data, data + z);
    pad4(out);
}
static int visit(void* context, const koronos_newc_entry* entry) {
    uint32_t* count = (uint32_t*)context;
    ++*count;
    assert(entry->name_size > 0);
    assert(entry->name[entry->name_size] == 0);
    return 0;
}
int main() {
    koronos_newc_result result{};
    std::vector<uint8_t> archive;
    append(archive, ".", "", KORONOS_NEWC_DIR);
    append(archive, "./etc", "", KORONOS_NEWC_DIR);
    append(archive, "./init", "hello", KORONOS_NEWC_REG, true);
    append(archive, "./tmp", "", KORONOS_NEWC_DIR);
    append(archive, "./tmp/old.log", "archive-stale", KORONOS_NEWC_REG);
    append(archive, "TRAILER!!!", nullptr, KORONOS_NEWC_REG);
    uint32_t visited = 0;
    assert(koronos_newc_walk(archive.data(), archive.size(), visit, &visited, &result) == 0);
    assert(visited == 5 && result.entries == 5 && result.directories == 3);
    assert(result.regular_files == 2 && result.payload_bytes == 18);
    assert(koronos_initramfs_mount(archive.data(), archive.size()) == 0);
    uint32_t init_node = 0, etc_node = 0;
    assert(koronos_initramfs_lookup("/init", &init_node) == 0);
    assert(koronos_initramfs_lookup("/etc", &etc_node) == 0);
    koronos_initramfs_stat init_stat{};
    assert(koronos_initramfs_stat_node(init_node, &init_stat) == 0);
    assert(init_stat.type == 2 && init_stat.size == 5);
    char contents[8] = {};
    uint64_t bytes_read = 0;
    assert(koronos_initramfs_read(init_node, 0, contents, 5, &bytes_read) == 0);
    assert(bytes_read == 5 && memcmp(contents, "hello", 5) == 0);
    assert(koronos_initramfs_read(etc_node, 0, contents, 5, &bytes_read) != 0);
    assert(koronos_initramfs_node_count() == 4); // root, etc, init, and RAM-backed /tmp
    uint32_t stale_tmp_node = 0;
    assert(koronos_initramfs_lookup("/tmp/old.log", &stale_tmp_node) != 0); // archive /tmp is masked
    uint32_t tmp_node = 0;
    assert(koronos_initramfs_lookup("/tmp", &tmp_node) == 0);
    koronos_initramfs_stat tmp_stat{};
    assert(koronos_initramfs_stat_node(tmp_node, &tmp_stat) == 0 && tmp_stat.type == 1);
    uint32_t log_node = 0;
    assert(koronos_tmpfs_create("/tmp/session.log", &log_node) == 0);
    uint64_t bytes_written = 0;
    assert(koronos_tmpfs_write(log_node, 0, "tmpfs", 5, &bytes_written) == 0);
    assert(bytes_written == 5);
    memset(contents, 0, sizeof(contents));
    assert(koronos_initramfs_read(log_node, 0, contents, 5, &bytes_read) == 0);
    assert(bytes_read == 5 && memcmp(contents, "tmpfs", 5) == 0);
    assert(koronos_tmpfs_write(init_node, 0, "no", 2, &bytes_written) != 0);
    assert(koronos_tmpfs_create("/etc/forbidden", &log_node) != 0);
    assert(koronos_tmpfs_create("/tmp/.", &log_node) != 0);
    assert(koronos_tmpfs_create("/tmp/..", &log_node) != 0);
    koronos_initramfs_unmount();

    std::vector<uint8_t> badpath;
    append(badpath, "../escape", "x", KORONOS_NEWC_REG);
    append(badpath, "TRAILER!!!", nullptr, KORONOS_NEWC_REG);
    assert(koronos_newc_walk(badpath.data(), badpath.size(), nullptr, nullptr, &result) == -6);

    std::vector<uint8_t> badlink;
    append(badlink, "./escape", "../etc/passwd", KORONOS_NEWC_SYMLINK);
    append(badlink, "TRAILER!!!", nullptr, KORONOS_NEWC_REG);
    assert(koronos_newc_walk(badlink.data(), badlink.size(), nullptr, nullptr, &result) == -14);

    std::vector<uint8_t> absolute_link;
    append(absolute_link, "./messages", "/var/log/messages", KORONOS_NEWC_SYMLINK);
    append(absolute_link, "TRAILER!!!", nullptr, KORONOS_NEWC_REG);
    assert(koronos_newc_walk(absolute_link.data(), absolute_link.size(), nullptr, nullptr, &result) == 0);

    archive.pop_back();
    assert(koronos_newc_walk(archive.data(), archive.size(), nullptr, nullptr, &result) != 0);
    puts("Koronos newc initramfs parser tests: OK");
    return 0;
}
