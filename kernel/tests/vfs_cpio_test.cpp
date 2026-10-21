#include "chimera/cpio.h"
#include "chimera/vfs_cpio.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void hex8(char *p, uint32_t v) {
    static const char d[] = "0123456789abcdef";
    for (int i = 7; i >= 0; --i) { p[i] = d[v & 15u]; v >>= 4; }
}
static uint32_t add_entry(uint8_t *b, uint32_t off, const char *name, const char *data) {
    char h[110]; memset(h, '0', sizeof(h)); memcpy(h, "070701", 6);
    hex8(h + 14, 0100644); hex8(h + 22, 0); hex8(h + 30, 0); hex8(h + 38, 1);
    hex8(h + 54, static_cast<uint32_t>(strlen(data)));
    hex8(h + 94, static_cast<uint32_t>(strlen(name) + 1u));
    memcpy(b + off, h, sizeof(h)); off += sizeof(h);
    memcpy(b + off, name, strlen(name) + 1u); off += static_cast<uint32_t>(strlen(name) + 1u);
    off = (off + 3u) & ~3u;
    if (*data) memcpy(b + off, data, strlen(data));
    off += static_cast<uint32_t>(strlen(data));
    return (off + 3u) & ~3u;
}
int main() {
    uint8_t archive[1024] = {};
    uint32_t n = add_entry(archive, 0, "./etc/chimera/target", "installer\n");
    n = add_entry(archive, n, "./etc/chimera.conf", "mode=installer\n");
    n = add_entry(archive, n, "TRAILER!!!", "");

    if (chimera_vfs_is_mounted()) {
        fputs("FAIL: test starts with a clean VFS root\n", stderr); return 1;
    }
    if (chimera_vfs_mount_readonly(archive, n, "live") == 0) {
        fputs("FAIL: mismatched target marker must not mount\n", stderr); return 1;
    }
    if (chimera_vfs_mount_readonly(archive, n, "installer") != 0 ||
        !chimera_vfs_is_mounted()) {
        fputs("FAIL: validated installer root must mount\n", stderr); return 1;
    }
    if (chimera_vfs_mount_readonly(archive, n, "installer") == 0) {
        fputs("FAIL: root mount must be immutable\n", stderr); return 1;
    }
    if (chimera_vfs_open_for(1, "/etc/chimera.conf", 1u) >= 0) {
        fputs("FAIL: write-capable open flags must be rejected\n", stderr); return 1;
    }
    int fd = chimera_vfs_open_for(1, "/etc/chimera.conf", CHIMERA_VFS_O_RDONLY);
    if (fd != 3) { fputs("FAIL: first per-process descriptor should be 3\n", stderr); return 1; }
    char data[32] = {};
    uint64_t got = 0;
    if (chimera_vfs_read_for(2, fd, data, 5, &got) == 0) {
        fputs("FAIL: one process must not read another process descriptor\n", stderr); return 1;
    }
    if (chimera_vfs_read_for(1, fd, data, 5, &got) != 0 || got != 5 ||
        memcmp(data, "mode=", 5) != 0) {
        fputs("FAIL: bounded first read / file offset\n", stderr); return 1;
    }
    if (chimera_vfs_read_for(1, fd, data, sizeof(data), &got) != 0 ||
        got != 10 || memcmp(data, "installer\n", 10) != 0) {
        fputs("FAIL: sequential read must advance the descriptor offset\n", stderr); return 1;
    }
    if (chimera_vfs_read_for(1, fd, data, sizeof(data), &got) != 0 || got != 0) {
        fputs("FAIL: EOF must be successful with zero bytes\n", stderr); return 1;
    }
    if (chimera_vfs_close_for(1, fd) != 0 || chimera_vfs_close_for(1, fd) == 0) {
        fputs("FAIL: close must release exactly one owned descriptor\n", stderr); return 1;
    }
    int fd2 = chimera_vfs_open_for(2, "/etc/chimera/target", CHIMERA_VFS_O_RDONLY);
    if (fd2 != 3 || chimera_vfs_read_for(2, fd2, data, sizeof(data), &got) != 0 ||
        got != 10 || memcmp(data, "installer\n", 10) != 0) {
        fputs("FAIL: descriptors and offsets must be independent per PID\n", stderr); return 1;
    }
    puts("PASS: immutable CPIO root, per-PID descriptors, bounded read, EOF and close");
    return 0;
}
