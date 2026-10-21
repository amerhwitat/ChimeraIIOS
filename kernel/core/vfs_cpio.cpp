#include "chimera/vfs_cpio.h"
#include "chimera/cpio.h"
#include <stddef.h>
#include <stdint.h>

namespace {
constexpr uint64_t MAX_READ = 65536u;
constexpr uint32_t FIRST_FD = 3u;
constexpr uint32_t FD_COUNT = CHIMERA_VFS_FDS_PER_PROCESS;
struct open_file {
    const uint8_t *data;
    uint32_t size;
    uint32_t offset;
    uint32_t in_use;
};
static const uint8_t *g_archive = nullptr;
static uint64_t g_archive_size = 0;
static volatile uint32_t g_mounted = 0;
static volatile uint32_t g_lock = 0;
static open_file g_fds[CHIMERA_VFS_MAX_PROCESSES][FD_COUNT];

static void lock() { while (__sync_lock_test_and_set(&g_lock, 1u)) {} }
static void unlock() { __sync_lock_release(&g_lock); }
static bool same(const char *a, const char *b) {
    if (!a || !b) return false;
    while (*a && *b) { if (*a++ != *b++) return false; }
    return *a == 0 && *b == 0;
}
static bool valid_pid(uint32_t pid) { return pid > 0 && pid <= CHIMERA_VFS_MAX_PROCESSES; }
static bool valid_path(const char *path) {
    if (!path || !*path) return false;
    uint32_t n = 0;
    while (path[n] && n <= CHIMERA_CPIO_PATH_MAX) ++n;
    return n > 0 && n <= CHIMERA_CPIO_PATH_MAX;
}
static bool valid_target(const char *target) {
    return same(target, "live") || same(target, "installer") || same(target, "recovery");
}
}

extern "C" int chimera_vfs_mount_readonly(const void *archive, uint64_t archive_size,
                                            const char *expected_target) {
    if (!archive || archive_size < 110u || !valid_target(expected_target)) return -1;
    if (chimera_cpio_validate(archive, archive_size) != 0) return -4;
    chimera_cpio_entry marker{};
    if (chimera_cpio_find(archive, archive_size, "/etc/chimera/target", &marker) != 0)
        return -2;
    const uint32_t target_len = same(expected_target, "installer") ? 10u :
                                (same(expected_target, "recovery") ? 9u : 5u);
    if (marker.size != target_len || !marker.data || marker.data[target_len - 1u] != '\n')
        return -3;
    for (uint32_t i = 0; i + 1u < target_len; ++i)
        if (marker.data[i] != static_cast<uint8_t>(expected_target[i])) return -3;

    /* Force the parser to walk to TRAILER!!!. A successful target-marker lookup
       alone would not detect a malformed record later in the archive. */
    chimera_cpio_entry absent{};
    if (chimera_cpio_find(archive, archive_size, "/.__chimera_mount_validation_absent__", &absent) != -2)
        return -4;

    lock();
    if (g_mounted) { unlock(); return -5; }
    g_archive = static_cast<const uint8_t *>(archive);
    g_archive_size = archive_size;
    __sync_synchronize();
    g_mounted = 1;
    unlock();
    return 0;
}

extern "C" int chimera_vfs_is_mounted(void) {
    return __atomic_load_n(&g_mounted, __ATOMIC_ACQUIRE) ? 1 : 0;
}

extern "C" int chimera_vfs_open_for(uint32_t pid, const char *path, uint32_t flags) {
    if (!valid_pid(pid) || !valid_path(path) || flags != CHIMERA_VFS_O_RDONLY) return -1;
    if (!chimera_vfs_is_mounted()) return -2;
    chimera_cpio_entry entry{};
    if (chimera_cpio_find(g_archive, g_archive_size, path, &entry) != 0) return -3;
    if ((entry.mode & 0170000u) != 0100000u) return -5; /* only regular files are openable */
    lock();
    for (uint32_t i = 0; i < FD_COUNT; ++i) {
        open_file &f = g_fds[pid - 1u][i];
        if (!f.in_use) {
            f.data = entry.data;
            f.size = entry.size;
            f.offset = 0;
            f.in_use = 1;
            unlock();
            return static_cast<int>(FIRST_FD + i);
        }
    }
    unlock();
    return -4;
}

extern "C" int chimera_vfs_read_for(uint32_t pid, int fd, void *buffer, uint64_t count,
                                      uint64_t *read_count) {
    if (read_count) *read_count = 0;
    if (!valid_pid(pid) || fd < static_cast<int>(FIRST_FD) ||
        fd >= static_cast<int>(FIRST_FD + FD_COUNT) || !read_count || (!buffer && count) ||
        count > MAX_READ) return -1;
    lock();
    open_file &f = g_fds[pid - 1u][static_cast<uint32_t>(fd) - FIRST_FD];
    if (!f.in_use) { unlock(); return -2; }
    uint64_t n = static_cast<uint64_t>(f.size - f.offset);
    if (n > count) n = count;
    uint8_t *out = static_cast<uint8_t *>(buffer);
    for (uint64_t i = 0; i < n; ++i) out[i] = f.data[f.offset + i];
    f.offset += static_cast<uint32_t>(n);
    *read_count = n;
    unlock();
    return 0; /* EOF is success with read_count == 0, like read(2). */
}

extern "C" int chimera_vfs_close_for(uint32_t pid, int fd) {
    if (!valid_pid(pid) || fd < static_cast<int>(FIRST_FD) ||
        fd >= static_cast<int>(FIRST_FD + FD_COUNT)) return -1;
    lock();
    open_file &f = g_fds[pid - 1u][static_cast<uint32_t>(fd) - FIRST_FD];
    if (!f.in_use) { unlock(); return -2; }
    f = {};
    unlock();
    return 0;
}
