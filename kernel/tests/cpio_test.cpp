#include "chimera/cpio.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static void hex8(char* p, uint32_t v) {
    static const char d[] = "0123456789abcdef";
    for (int i = 7; i >= 0; --i) { p[i] = d[v & 15u]; v >>= 4; }
}
static uint32_t entry(uint8_t* b, uint32_t off, const char* name, const char* data) {
    char h[110]; memset(h, '0', sizeof(h)); memcpy(h, "070701", 6);
    hex8(h+14, 0100644); hex8(h+22, 0); hex8(h+30, 0); hex8(h+38, 1);
    hex8(h+54, static_cast<uint32_t>(strlen(data)));
    hex8(h+94, static_cast<uint32_t>(strlen(name)+1));
    memcpy(b+off, h, sizeof(h)); off += sizeof(h);
    memcpy(b+off, name, strlen(name)+1); off += static_cast<uint32_t>(strlen(name)+1);
    off = (off+3u)&~3u;
    memcpy(b+off, data, strlen(data)); off += static_cast<uint32_t>(strlen(data));
    return (off+3u)&~3u;
}
int main() {
    uint8_t archive[512] = {};
    uint32_t n = entry(archive, 0, "./etc/chimera.conf", "mode=live\n");
    n = entry(archive, n, "TRAILER!!!", "");
    chimera_cpio_entry out{};
    if (chimera_cpio_find(archive, n, "/etc/chimera.conf", &out) != 0 ||
        out.size != 10 || memcmp(out.data, "mode=live\n", 10) != 0) {
        fputs("FAIL: exact path lookup and data bounds\n", stderr); return 1;
    }
    if (chimera_cpio_find(archive, n, "/etc/missing", &out) != -2) {
        fputs("FAIL: missing path must be reported absent\n", stderr); return 1;
    }
    if (chimera_cpio_find(archive, 109, "/etc/chimera.conf", &out) != -1) {
        fputs("FAIL: truncated archive must be rejected\n", stderr); return 1;
    }
    archive[0] = 'x';
    if (chimera_cpio_find(archive, n, "/etc/chimera.conf", &out) != -1) {
        fputs("FAIL: invalid magic must be rejected\n", stderr); return 1;
    }
    puts("PASS: bounded CPIO newc lookup tests");
    return 0;
}
