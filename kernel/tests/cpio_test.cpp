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
    if (chimera_cpio_validate(archive, n) != 0) {
        fputs("FAIL: complete valid newc archive should validate\\n", stderr); return 1;
    }
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
    uint8_t unsafe[512] = {};
    uint32_t u = entry(unsafe, 0, "./../escape", "x");
    u = entry(unsafe, u, "TRAILER!!!", "");
    if (chimera_cpio_validate(unsafe, u) == 0) {
        fputs("FAIL: parent traversal path must be rejected\\n", stderr); return 1;
    }
    uint8_t duplicate[512] = {};
    uint32_t d = entry(duplicate, 0, "./etc/same", "a");
    d = entry(duplicate, d, "etc/same", "b");
    d = entry(duplicate, d, "TRAILER!!!", "");
    if (chimera_cpio_validate(duplicate, d) == 0) {
        fputs("FAIL: duplicate normalized paths must be rejected\\n", stderr); return 1;
    }
    uint8_t crc_archive[512] = {};
    uint32_t cr = entry(crc_archive, 0, "etc/crc", "abc");
    cr = entry(crc_archive, cr, "TRAILER!!!", "");
    crc_archive[5] = '2';
    const uint32_t trailer_off = cr - 124u;
    crc_archive[trailer_off + 5u] = '2';
    hex8(reinterpret_cast<char *>(crc_archive) + 102u, 294u); /* 'a' + 'b' + 'c' */
    if (chimera_cpio_validate(crc_archive, cr) != 0) {
        fputs("FAIL: valid 070702 data checksum should validate\\n", stderr); return 1;
    }
    hex8(reinterpret_cast<char *>(crc_archive) + 102u, 0u);
    if (chimera_cpio_validate(crc_archive, cr) == 0) {
        fputs("FAIL: invalid 070702 data checksum must be rejected\\n", stderr); return 1;
    }
    puts("PASS: bounded CPIO newc lookup and archive validation tests");
    return 0;
}
