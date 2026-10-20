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
static bool valid_archive_name(const uint8_t *name, uint32_t name_size) {
    if (!name || name_size < 2u || name_size > CHIMERA_CPIO_PATH_MAX || name[name_size - 1u] != 0)
        return false;
    for (uint32_t i = 0; i + 1u < name_size; ++i) if (name[i] == 0) return false;
    uint32_t begin = 0;
    while (begin + 1u < name_size && name[begin] == '.' && name[begin + 1u] == '/') begin += 2u;
    const uint32_t end = name_size - 1u;
    if (begin >= end || name[begin] == '/') return false;
    uint32_t component = begin;
    for (uint32_t i = begin; i <= end; ++i) {
        if (i == end || name[i] == '/') {
            const uint32_t len = i - component;
            if (!len || (len == 1u && name[component] == '.') ||
                (len == 2u && name[component] == '.' && name[component + 1u] == '.')) return false;
            component = i + 1u;
        }
    }
    return true;
}
static bool same_normalized_name(const uint8_t *a, uint32_t an, const uint8_t *b, uint32_t bn) {
    if (!a || !b || an < 2u || bn < 2u) return false;
    uint32_t ai = 0, bi = 0;
    while (ai + 1u < an && a[ai] == '.' && ai + 1u < an && a[ai + 1u] == '/') ai += 2u;
    while (bi + 1u < bn && b[bi] == '.' && bi + 1u < bn && b[bi + 1u] == '/') bi += 2u;
    const uint32_t al = an - 1u - ai, bl = bn - 1u - bi;
    if (al != bl) return false;
    for (uint32_t i = 0; i < al; ++i) if (a[ai + i] != b[bi + i]) return false;
    return true;
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
extern "C" int chimera_cpio_validate(const void *archive, uint64_t archive_size) {
    constexpr uint64_t HEADER_SIZE = 110u;
    constexpr uint32_t MAX_ENTRIES = 4096u;
    constexpr uint64_t MAX_ARCHIVE_SIZE = 256ull * 1024ull * 1024ull;
    if (!archive || archive_size < HEADER_SIZE || archive_size > MAX_ARCHIVE_SIZE) return -1;
    const uint8_t *bytes = static_cast<const uint8_t *>(archive);
    uint64_t offset = 0;
    uint32_t entries = 0;
    bool saw_trailer = false;
    while (offset < archive_size) {
        uint64_t header_end;
        if (add_overflow(offset, HEADER_SIZE, &header_end) || header_end > archive_size) return -1;
        const uint8_t *h = bytes + offset;
        if (!((h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&h[5]=='1') ||
              (h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&h[5]=='2')) return -1;
        uint32_t mode=0, file_size=0, name_size=0, checksum=0;
        const bool crc_format = h[5] == '2';
        if (!hex8(h+14,&mode) || !hex8(h+54,&file_size) || !hex8(h+94,&name_size) ||
            !hex8(h+102,&checksum) || name_size < 2u || name_size > CHIMERA_CPIO_PATH_MAX) return -1;
        uint64_t name_end;
        if (add_overflow(header_end, name_size, &name_end) || name_end > archive_size) return -1;
        const uint8_t *name = bytes + header_end;
        if (name[name_size - 1u] != 0) return -1;
        for (uint32_t i=0; i+1u<name_size; ++i) if (name[i] == 0) return -1;
        uint64_t data_offset;
        if (add_overflow(name_end, 3u, &data_offset)) return -1;
        data_offset &= ~3ull;
        uint64_t data_end;
        if (add_overflow(data_offset, file_size, &data_end) || data_end > archive_size) return -1;
        uint64_t next;
        if (add_overflow(data_end, 3u, &next)) return -1;
        next &= ~3ull;
        if (next > archive_size || next <= offset) return -1;
        if (crc_format) {
            uint32_t sum = 0;
            for (uint64_t i = data_offset; i < data_end; ++i) sum += bytes[i];
            if (sum != checksum) return -1;
        } else if (checksum != 0) {
            return -1;
        }
        const bool trailer = name_size == 11u &&
            name[0]=='T'&&name[1]=='R'&&name[2]=='A'&&name[3]=='I'&&name[4]=='L'&&
            name[5]=='E'&&name[6]=='R'&&name[7]=='!'&&name[8]=='!'&&name[9]=='!'&&name[10]==0;
        if (trailer) {
            if (file_size != 0) return -1;
            for (uint64_t i=next; i<archive_size; ++i) if (bytes[i] != 0) return -1;
            saw_trailer = true;
            break;
        }
        if (!valid_archive_name(name, name_size) || ++entries > MAX_ENTRIES) return -1;
        const uint32_t type = mode & 0170000u;
        if (type != 0100000u && type != 0040000u) return -1;
        if (type == 0040000u && file_size != 0) return -1;
        uint64_t prior = 0;
        while (prior < offset) {
            uint64_t prior_header_end;
            if (add_overflow(prior, HEADER_SIZE, &prior_header_end) || prior_header_end > archive_size) return -1;
            const uint8_t *ph = bytes + prior;
            uint32_t prior_mode=0, prior_size=0, prior_name_size=0;
            if (!hex8(ph+14,&prior_mode) || !hex8(ph+54,&prior_size) ||
                !hex8(ph+94,&prior_name_size) || prior_name_size < 2u ||
                prior_name_size > CHIMERA_CPIO_PATH_MAX) return -1;
            uint64_t prior_name_end, prior_data, prior_data_end, prior_next;
            if (add_overflow(prior_header_end, prior_name_size, &prior_name_end) || prior_name_end > archive_size ||
                add_overflow(prior_name_end,3u,&prior_data)) return -1;
            prior_data &= ~3ull;
            if (add_overflow(prior_data,prior_size,&prior_data_end) || prior_data_end > archive_size ||
                add_overflow(prior_data_end,3u,&prior_next)) return -1;
            prior_next &= ~3ull;
            const uint8_t *prior_name = bytes + prior_header_end;
            const bool prior_trailer = prior_name_size == 11u &&
                prior_name[0]=='T'&&prior_name[1]=='R'&&prior_name[2]=='A'&&prior_name[3]=='I'&&
                prior_name[4]=='L'&&prior_name[5]=='E'&&prior_name[6]=='R'&&prior_name[7]=='!'&&
                prior_name[8]=='!'&&prior_name[9]=='!'&&prior_name[10]==0;
            if (prior_trailer || prior_next <= prior || prior_next > offset ||
                prior_name[prior_name_size-1u] != 0) return -1;
            if (same_normalized_name(name,name_size,prior_name,prior_name_size)) return -1;
            (void)prior_mode;
            prior = prior_next;
        }
        offset = next;
    }
    return saw_trailer ? 0 : -1;
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
