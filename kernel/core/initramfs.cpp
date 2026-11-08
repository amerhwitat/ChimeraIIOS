#include <stddef.h>
#include <stdint.h>
#include "chimera/initramfs.h"

namespace {
static char g_seen_paths[CHIMERA_INITRAMFS_MAX_ENTRIES][CHIMERA_INITRAMFS_PATH_MAX + 1u];
static uint32_t g_seen_count = 0;

static bool add_ok(uint64_t a, uint64_t b, uint64_t limit, uint64_t* out) {
    if (!out || a > limit || b > limit - a) return false;
    *out = a + b;
    return true;
}

static bool align4(uint64_t value, uint64_t limit, uint64_t* out) {
    if (value > limit || value > UINT64_MAX - 3u) return false;
    const uint64_t aligned = (value + 3u) & ~3ull;
    if (aligned > limit) return false;
    *out = aligned;
    return true;
}

static bool hex8(const uint8_t* p, uint32_t* out) {
    if (!p || !out) return false;
    uint32_t value = 0;
    for (uint32_t i = 0; i < 8u; ++i) {
        const uint8_t c = p[i];
        uint32_t digit;
        if (c >= '0' && c <= '9') digit = (uint32_t)(c - '0');
        else if (c >= 'a' && c <= 'f') digit = (uint32_t)(c - 'a' + 10u);
        else if (c >= 'A' && c <= 'F') digit = (uint32_t)(c - 'A' + 10u);
        else return false;
        value = (value << 4u) | digit;
    }
    *out = value;
    return true;
}

static bool same_path(const char* a, const char* b) {
    if (!a || !b) return false;
    uint32_t i = 0;
    while (a[i] && b[i] && a[i] == b[i]) ++i;
    return a[i] == 0 && b[i] == 0;
}

static int normalize_path(const uint8_t* name, uint32_t name_size,
                          char* out, uint32_t* out_length) {
    if (!name || !out || !out_length || name_size == 0u ||
        name_size > CHIMERA_INITRAMFS_PATH_MAX + 1u) return -1;
    if (name[name_size - 1u] != 0u) return -2;
    for (uint32_t i = 0; i + 1u < name_size; ++i)
        if (name[i] == 0u) return -3;
    if (name[0] == '/') return -4;
    if (name_size == 2u && name[0] == '.') {
        out[0] = 0;
        *out_length = 0;
        return 0;
    }

    uint32_t start = 0;
    if (name_size >= 3u && name[0] == '.' && name[1] == '/') start = 2u;
    const uint32_t end = name_size - 1u;
    if (start == end && name_size == 2u && name[0] == '.') {
        out[0] = 0;
        *out_length = 0;
        return 0;
    }
    if (start == end) {
        out[0] = 0;
        *out_length = 0;
        return 0;
    }

    uint32_t used = 0;
    uint32_t component_start = start;
    for (uint32_t i = start; i <= end; ++i) {
        if (i != end && name[i] != '/') continue;
        const uint32_t component_length = i - component_start;
        if (component_length == 0u) return -5;
        if (component_length == 1u && name[component_start] == '.') return -6;
        if (component_length == 2u && name[component_start] == '.' &&
            name[component_start + 1u] == '.') return -7;
        if (used && used >= CHIMERA_INITRAMFS_PATH_MAX) return -8;
        if (used) out[used++] = '/';
        if (component_length > CHIMERA_INITRAMFS_PATH_MAX - used) return -8;
        for (uint32_t j = 0; j < component_length; ++j)
            out[used++] = (char)name[component_start + j];
        component_start = i + 1u;
    }
    out[used] = 0;
    *out_length = used;
    return 0;
}

static int parse_archive(const uint8_t* bytes, uint64_t size, bool emit,
                         chimera_initramfs_visit_fn visitor, void* context,
                         chimera_initramfs_report* report) {
    if (!bytes || size < 110u) return -1;
    uint64_t offset = 0;
    bool trailer = false;
    chimera_initramfs_report local{};
    uint32_t seen = 0;

    while (offset < size) {
        if (size - offset < 110u) return -2;
        const uint8_t* h = bytes + offset;
        const bool crc = h[0] == '0' && h[1] == '7' && h[2] == '0' &&
                         h[3] == '7' && h[4] == '0' && h[5] == '2';
        const bool newc = h[0] == '0' && h[1] == '7' && h[2] == '0' &&
                          h[3] == '7' && h[4] == '0' && h[5] == '1';
        if (!crc && !newc) return -3;

        uint32_t fields[13]{};
        for (uint32_t i = 0; i < 13u; ++i)
            if (!hex8(h + 6u + i * 8u, &fields[i])) return -4;
        const uint32_t inode = fields[0];
        const uint32_t mode = fields[1];
        const uint32_t file_size = fields[6];
        const uint32_t name_size = fields[11];
        const uint32_t checksum = fields[12];
        if (name_size == 0u || name_size > CHIMERA_INITRAMFS_PATH_MAX + 1u)
            return -5;

        uint64_t name_offset = 0, name_end = 0, data_offset = 0, data_end = 0;
        if (!add_ok(offset, 110u, size, &name_offset) ||
            !add_ok(name_offset, name_size, size, &name_end) ||
            !align4(name_end, size, &data_offset) ||
            !add_ok(data_offset, file_size, size, &data_end)) return -6;
        const uint8_t* name = bytes + name_offset;
        if (name[name_size - 1u] != 0u) return -7;
        bool is_trailer = name_size == 11u;
        if (is_trailer) {
            const char trailer_name[] = "TRAILER!!!";
            for (uint32_t i = 0; i < 10u; ++i)
                if (name[i] != (uint8_t)trailer_name[i]) is_trailer = false;
        } else {
            is_trailer = false;
        }
        if (is_trailer) {
            if (file_size != 0u) return -8;
            trailer = true;
            offset = data_offset;
            uint64_t trailer_end = 0;
            if (!align4(offset, size, &trailer_end)) return -6;
            offset = trailer_end;
            while (offset < size) {
                if (bytes[offset++] != 0u) return -9;
            }
            break;
        }

        char path[CHIMERA_INITRAMFS_PATH_MAX + 1u];
        uint32_t path_length = 0;
        const int normalized = normalize_path(name, name_size, path, &path_length);
        if (normalized != 0) return -10 + normalized;

        const uint32_t file_type = mode & 0170000u;
        uint32_t entry_type = 0;
        if (file_type == 0100000u) entry_type = CHM_INITRAMFS_REGULAR;
        else if (file_type == 0040000u) {
            entry_type = CHM_INITRAMFS_DIRECTORY;
            if (file_size != 0u) return -11;
        } else if (file_type == 0120000u) entry_type = CHM_INITRAMFS_SYMLINK;
        else return -12;

        const uint8_t* data = bytes + data_offset;
        if (crc) {
            uint32_t sum = 0;
            for (uint32_t i = 0; i < file_size; ++i) sum += data[i];
            if (sum != checksum) return -13;
        }
        if (!emit) {
            if (seen >= CHIMERA_INITRAMFS_MAX_ENTRIES) return -14;
            for (uint32_t i = 0; i < seen; ++i)
                if (same_path(g_seen_paths[i], path)) return -15;
            for (uint32_t i = 0; i <= path_length; ++i)
                g_seen_paths[seen][i] = path[i];
            ++seen;
        } else if (visitor) {
            chimera_initramfs_entry entry{};
            entry.path = path;
            entry.data = data;
            entry.path_length = path_length;
            entry.size = file_size;
            entry.mode = mode;
            entry.inode = inode;
            entry.type = entry_type;
            if (visitor(&entry, context) != 0) return -16;
        }

        if (local.entries == UINT32_MAX || local.payload_bytes > UINT64_MAX - file_size)
            return -17;
        ++local.entries;
        local.payload_bytes += file_size;
        if (entry_type == CHM_INITRAMFS_REGULAR) ++local.regular_files;
        else if (entry_type == CHM_INITRAMFS_DIRECTORY) ++local.directories;
        else if (entry_type == CHM_INITRAMFS_SYMLINK) ++local.symlinks;

        if (!align4(data_end, size, &offset)) return -6;
    }
    if (!trailer) return -18;
    if (!emit) g_seen_count = seen;
    if (report) *report = local;
    return 0;
}
}

extern "C" int chimera_initramfs_scan(const void* archive, uint64_t archive_size,
                                      chimera_initramfs_visit_fn visitor, void* context,
                                      chimera_initramfs_report* report) {
    g_seen_count = 0;
    if (report) {
        report->entries = 0;
        report->regular_files = 0;
        report->directories = 0;
        report->symlinks = 0;
        report->payload_bytes = 0;
    }
    chimera_initramfs_report validated{};
    const int validation = parse_archive(static_cast<const uint8_t*>(archive),
                                         archive_size, false, nullptr, nullptr,
                                         &validated);
    if (validation != 0) return validation;
    if (g_seen_count == 0u) return -19;
    chimera_initramfs_report emitted{};
    const int publish = parse_archive(static_cast<const uint8_t*>(archive),
                                      archive_size, true, visitor, context,
                                      &emitted);
    if (publish != 0) return publish;
    if (report) *report = validated;
    return 0;
}
