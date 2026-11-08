#include "chimera/cpio_newc.h"

namespace {
constexpr uint64_t HEADER_SIZE = 110u;
constexpr uint32_t S_IFMT = 0170000u;
constexpr uint32_t S_IFREG = 0100000u;
constexpr uint32_t S_IFDIR = 0040000u;
constexpr uint32_t S_IFLNK = 0120000u;

static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return false;
    *out = a + b;
    return true;
}
static bool align4(uint64_t value, uint64_t *out) {
    uint64_t sum = 0;
    if (!add_ok(value, 3u, &sum)) return false;
    *out = sum & ~3ull;
    return true;
}
static int hex32(const uint8_t *p, uint32_t *out) {
    uint32_t value = 0;
    for (uint32_t i = 0; i < 8u; ++i) {
        const uint8_t c = p[i];
        uint32_t digit;
        if (c >= '0' && c <= '9') digit = c - '0';
        else if (c >= 'a' && c <= 'f') digit = c - 'a' + 10u;
        else if (c >= 'A' && c <= 'F') digit = c - 'A' + 10u;
        else return -1;
        value = (value << 4) | digit;
    }
    *out = value;
    return 0;
}
static bool safe_name(const char *name, uint32_t size, uint32_t mode,
                      const char **normalized) {
    if (!name || !normalized || size < 2u ||
        size > CHIMERA_CPIO_NEWC_MAX_NAME || name[size - 1u] != 0) return false;
    for (uint32_t i = 0; i + 1u < size; ++i)
        if (name[i] == 0) return false;
    if (name[0] == '/') return false;

    const char *path = name;
    if (size >= 3u && path[0] == '.' && path[1] == '/') path += 2;
    if (path[0] == 0 || (path[0] == '.' && path[1] == 0)) {
        if ((mode & S_IFMT) != S_IFDIR) return false;
        *normalized = path[0] == '.' ? path + 1 : path;
        return true;
    }

    uint32_t path_size = 0;
    while (path[path_size]) ++path_size;
    if (path_size && path[path_size - 1u] == '/') {
        if ((mode & S_IFMT) != S_IFDIR) return false;
        --path_size;
    }
    if (!path_size) return false;
    uint32_t component_start = 0;
    for (uint32_t i = 0; i <= path_size; ++i) {
        if (i != path_size && path[i] != '/') continue;
        const uint32_t length = i - component_start;
        if (length == 0u || (length == 1u && path[component_start] == '.') ||
            (length == 2u && path[component_start] == '.' && path[component_start + 1u] == '.'))
            return false;
        component_start = i + 1u;
    }
    *normalized = path;
    return true;
}
static uint32_t byte_sum(const uint8_t *data, uint32_t size) {
    uint32_t sum = 0;
    for (uint32_t i = 0; i < size; ++i) sum += data[i];
    return sum;
}
}

extern "C" int chimera_cpio_newc_walk(const void *archive, uint64_t archive_size,
                                       const chimera_cpio_newc_ops *ops, void *context,
                                       chimera_cpio_newc_summary *summary) {
    if (!archive || !ops || !ops->entry || !summary || archive_size < HEADER_SIZE)
        return -1;
    *summary = {};
    summary->abi = CHIMERA_CPIO_NEWC_ABI;
    const auto *bytes = static_cast<const uint8_t *>(archive);
    uint64_t offset = 0;
    bool trailer_seen = false;

    while (offset < archive_size) {
        uint64_t header_end = 0;
        if (!add_ok(offset, HEADER_SIZE, &header_end) || header_end > archive_size)
            return -5;
        const uint8_t *header = bytes + offset;
        const bool crc = header[0] == '0' && header[1] == '7' &&
                         header[2] == '0' && header[3] == '7' &&
                         header[4] == '0' && header[5] == '2';
        const bool newc = header[0] == '0' && header[1] == '7' &&
                          header[2] == '0' && header[3] == '7' &&
                          header[4] == '0' && header[5] == '1';
        if (!crc && !newc) return -2;

        uint32_t fields[13]{};
        for (uint32_t i = 0; i < 13u; ++i)
            if (hex32(header + 6u + i * 8u, &fields[i]) != 0) return -3;
        const uint32_t mode = fields[1];
        const uint32_t uid = fields[2];
        const uint32_t gid = fields[3];
        const uint32_t file_size = fields[6];
        const uint32_t name_size = fields[11];
        const uint32_t expected_sum = fields[12];
        if (name_size == 0u || name_size > CHIMERA_CPIO_NEWC_MAX_NAME) return -4;

        uint64_t name_end = 0, data_start = 0, data_end = 0, next = 0;
        if (!add_ok(header_end, name_size, &name_end) ||
            name_end > archive_size || !align4(name_end, &data_start) ||
            !add_ok(data_start, file_size, &data_end) ||
            data_end > archive_size || !align4(data_end, &next) ||
            next > archive_size) return -5;

        const char *name = reinterpret_cast<const char *>(bytes + header_end);
        const char *normalized = nullptr;
        if (!safe_name(name, name_size, mode, &normalized)) return -4;
        const bool is_trailer = name_size == 11u;
        if (is_trailer) {
            static const char trailer[] = "TRAILER!!!";
            uint32_t i = 0;
            while (i < 10u && name[i] == trailer[i]) ++i;
            if (i == 10u && name[10] == 0) {
                if (file_size != 0u) return -4;
                trailer_seen = true;
                offset = next;
                break;
            }
        }
        if (trailer_seen) return -2;

        const uint32_t type = mode & S_IFMT;
        if (type != S_IFREG && type != S_IFDIR && type != S_IFLNK) return -6;
        if (type == S_IFDIR && file_size != 0u) return -4;
        const uint8_t *data = bytes + data_start;
        if (crc && byte_sum(data, file_size) != expected_sum) return -7;
        if (ops->entry(context, normalized, mode, uid, gid, data, file_size) != 0)
            return -9;

        ++summary->entries;
        if (type == S_IFREG) ++summary->regular_files;
        else if (type == S_IFDIR) ++summary->directories;
        else ++summary->symlinks;
        summary->data_bytes += file_size;
        offset = next;
    }

    if (!trailer_seen) return -8;
    for (; offset < archive_size; ++offset)
        if (bytes[offset] != 0u) return -10;
    return 0;
}
