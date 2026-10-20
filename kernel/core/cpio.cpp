#include "chimera/cpio.h"
namespace {
static bool add_overflow(uint64_t a, uint64_t b, uint64_t* out) {
    if (!out || b > UINT64_MAX - a) return true;
    *out = a + b;
    return false;
}
static bool hex8(const uint8_t* p, uint32_t* out) {
    uint32_t value = 0;
    for (uint32_t i = 0; i < 8; ++i) {
        const uint8_t c = p[i];
        uint32_t digit;
        if (c >= '0' && c <= '9') digit = c - '0';
        else if (c >= 'a' && c <= 'f') digit = c - 'a' + 10u;
        else if (c >= 'A' && c <= 'F') digit = c - 'A' + 10u;
        else return false;
        value = (value << 4) | digit;
    }
    *out = value;
    return true;
}
static bool eq(const char* a, const char* b) {
    if (!a || !b) return false;
    while (*a && *b && *a == *b) { ++a; ++b; }
    return *a == *b;
}
static bool normalized_eq(const char* archive_name, uint32_t name_size, const char* path) {
    if (!archive_name || !path || name_size == 0 || archive_name[name_size - 1] != 0)
        return false;
    while (*path == '/') ++path;
    while (path[0] == '.' && path[1] == '/') path += 2;
    while (archive_name[0] == '.' && archive_name[1] == '/') {
        archive_name += 2;
        if (name_size < 3) return false;
        name_size -= 2;
    }
    uint32_t i = 0;
    while (i + 1 < name_size && archive_name[i] && path[i]) {
        if (archive_name[i] != path[i]) return false;
        ++i;
    }
    return i + 1 == name_size && path[i] == 0;
}
}
extern "C" int chimera_cpio_find(const void* archive, uint64_t archive_size,
                                  const char* path, chimera_cpio_entry* out) {
    if (!archive || !path || !out || archive_size < 110u) return -1;
    uint32_t path_length = 0;
    while (path[path_length] && path_length < CHIMERA_CPIO_PATH_MAX) ++path_length;
    if (!path_length || path_length >= CHIMERA_CPIO_PATH_MAX) return -1;
    const uint8_t* bytes = static_cast<const uint8_t*>(archive);
    uint64_t offset = 0;
    while (offset < archive_size) {
        uint64_t header_end;
        if (add_overflow(offset, 110u, &header_end) || header_end > archive_size) return -1;
        const uint8_t* h = bytes + offset;
        if (!((h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&h[5]=='1') ||
              (h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&h[5]=='2'))) return -1;
        uint32_t ino, mode, uid, gid, nlink, mtime, file_size, devmajor, devminor, rdevmajor, rdevminor, name_size, check;
        if (!hex8(h+6,&ino)||!hex8(h+14,&mode)||!hex8(h+22,&uid)||!hex8(h+30,&gid)||
            !hex8(h+38,&nlink)||!hex8(h+46,&mtime)||!hex8(h+54,&file_size)||
            !hex8(h+62,&devmajor)||!hex8(h+70,&devminor)||!hex8(h+78,&rdevmajor)||
            !hex8(h+86,&rdevminor)||!hex8(h+94,&name_size)||!hex8(h+102,&check)) return -1;
        (void)ino; (void)nlink; (void)mtime; (void)devmajor; (void)devminor;
        (void)rdevmajor; (void)rdevminor; (void)check;
        if (!name_size || name_size > CHIMERA_CPIO_PATH_MAX) return -1;
        uint64_t name_end;
        if (add_overflow(header_end, name_size, &name_end) || name_end > archive_size) return -1;
        const char* name = reinterpret_cast<const char*>(bytes + header_end);
        if (name[name_size - 1] != 0) return -1;
        uint64_t data_offset;
        if (add_overflow(name_end, 3u, &data_offset)) return -1;
        data_offset &= ~3ull;
        uint64_t data_end;
        if (add_overflow(data_offset, file_size, &data_end) || data_end > archive_size) return -1;
        if (eq(name, "TRAILER!!!")) return -2;
        if (normalized_eq(name, name_size, path)) {
            out->data = bytes + data_offset;
            out->size = file_size;
            out->mode = mode;
            out->uid = uid;
            out->gid = gid;
            return 0;
        }
        if (add_overflow(data_end, 3u, &offset)) return -1;
        offset &= ~3ull;
    }
    return -1;
}
