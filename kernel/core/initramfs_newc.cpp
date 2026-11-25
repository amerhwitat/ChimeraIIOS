#include "chimera/initramfs_newc.h"

namespace {
static uint32_t hex8(const uint8_t *p, bool *ok) {
    uint32_t value = 0;
    for (uint32_t i = 0; i < 8; ++i) {
        const uint8_t c = p[i];
        uint32_t digit = 0;
        if (c >= '0' && c <= '9') digit = c - '0';
        else if (c >= 'a' && c <= 'f') digit = c - 'a' + 10u;
        else if (c >= 'A' && c <= 'F') digit = c - 'A' + 10u;
        else { *ok = false; return 0; }
        value = (value << 4) | digit;
    }
    return value;
}
static bool range_ok(uint64_t offset, uint64_t length, uint64_t total) {
    return offset <= total && length <= total - offset;
}
static uint64_t align4(uint64_t value, bool *ok) {
    if (value > UINT64_MAX - 3u) { *ok = false; return 0; }
    return (value + 3u) & ~3ull;
}
static bool safe_name(const char *name, uint32_t size) {
    if (!name || size < 2 || name[size - 1u] != 0) return false;
    for (uint32_t i = 0; i + 1u < size; ++i) if (name[i] == 0) return false;
    if ((size == 2u && name[0] == '.') ||
        (size == 3u && name[0] == '.' && name[1] == '/')) return true;
    uint32_t start = 0;
    if (size >= 3 && name[0] == '.' && name[1] == '/') start = 2;
    if (start >= size - 1u || name[start] == '/') return false;
    for (uint32_t i = start; i < size - 1u;) {
        uint32_t end = i;
        while (end < size - 1u && name[end] != '/') {
            if (name[end] == '\\') return false;
            ++end;
        }
        const uint32_t length = end - i;
        if (length == 0 || (length == 1 && name[i] == '.') ||
            (length == 2 && name[i] == '.' && name[i + 1u] == '.')) return false;
        i = end + 1u;
    }
    return true;
}
}

extern "C" int koronos_newc_walk(const void *archive, uint64_t archive_size,
                                  koronos_newc_visit_fn visitor, void *context,
                                  koronos_newc_result *result) {
    if (!archive || !result || archive_size < 110u) return -1;
    *result = {};
    const uint8_t *bytes = static_cast<const uint8_t *>(archive);
    uint64_t offset = 0;
    bool trailer = false;
    while (range_ok(offset, 110u, archive_size)) {
        const uint8_t *h = bytes + offset;
        const bool crc = h[0] == '0' && h[1] == '7' && h[2] == '0' &&
                         h[3] == '7' && h[4] == '0' && h[5] == '2';
        const bool newc = h[0] == '0' && h[1] == '7' && h[2] == '0' &&
                          h[3] == '7' && h[4] == '0' && h[5] == '1';
        if (!crc && !newc) return -2;
        bool ok = true;
        uint32_t fields[13]{};
        for (uint32_t i = 0; i < 13; ++i) fields[i] = hex8(h + 6u + i * 8u, &ok);
        if (!ok) return -3;
        const uint32_t mode = fields[1], file_size = fields[6], name_size = fields[11];
        if (name_size < 2u || name_size > KORONOS_NEWC_MAX_NAME) return -4;
        uint64_t name_at = offset + 110u;
        if (!range_ok(name_at, name_size, archive_size)) return -5;
        const char *name = reinterpret_cast<const char *>(bytes + name_at);
        if (!safe_name(name, name_size)) return -6;
        bool align_ok = true;
        uint64_t data_at = align4(name_at + name_size, &align_ok);
        if (!align_ok || !range_ok(data_at, file_size, archive_size)) return -7;
        uint64_t next = align4(data_at + file_size, &align_ok);
        if (!align_ok || next > archive_size) return -8;
        if (name_size == 11u && name[0] == 'T' && name[1] == 'R' &&
            name[2] == 'A' && name[3] == 'I' && name[4] == 'L' &&
            name[5] == 'E' && name[6] == 'R' && name[7] == '!' &&
            name[8] == '!' && name[9] == '!' && name[10] == 0) {
            if (file_size != 0) return -9;
            trailer = true;
            result->archive_bytes = next;
            break;
        }
        if (result->entries >= 65536u) return -15;
        const uint32_t type = mode & KORONOS_NEWC_TYPE_MASK;
        if (type != KORONOS_NEWC_REG && type != KORONOS_NEWC_DIR &&
            type != KORONOS_NEWC_SYMLINK) return -10;
        if (type == KORONOS_NEWC_SYMLINK) {
            if (file_size == 0) return -14;
            uint32_t part = 0;
            for (uint32_t i = 0; i <= file_size; ++i) {
                if (i < file_size && (bytes[data_at + i] == '\\' || bytes[data_at + i] == 0)) return -14;
                if (i == file_size || bytes[data_at + i] == '/') {
                    if (part == 2u && bytes[data_at + i - 2u] == '.' && bytes[data_at + i - 1u] == '.') return -14;
                    part = 0;
                } else {
                    if (part < 2u) {
                        if (bytes[data_at + i] != '.') part = 3u;
                        else ++part;
                    } else if (part == 2u) part = 3u;
                }
            }
        }
        if (crc) {
            uint32_t sum = 0;
            for (uint32_t i = 0; i < file_size; ++i) sum += bytes[data_at + i];
            if (sum != fields[12]) return -11;
        }
        koronos_newc_entry entry{};
        entry.name = name;
        entry.data = bytes + data_at;
        entry.name_size = name_size - 1u;
        entry.mode = mode;
        entry.uid = fields[2];
        entry.gid = fields[3];
        entry.links = fields[4];
        entry.mtime = fields[5];
        entry.file_size = file_size;
        entry.device_major = fields[7];
        entry.device_minor = fields[8];
        if (visitor && visitor(context, &entry) != 0) return -12;
        ++result->entries;
        result->payload_bytes += file_size;
        if (type == KORONOS_NEWC_REG) ++result->regular_files;
        else if (type == KORONOS_NEWC_DIR) ++result->directories;
        else ++result->symlinks;
        offset = next;
    }
    if (!trailer) return -13;
    return 0;
}
