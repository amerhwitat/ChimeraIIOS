#include "chimera/registry.h"

namespace {
static uint16_t read_u16(const uint8_t *p) {
    return static_cast<uint16_t>(p[0]) |
           (static_cast<uint16_t>(p[1]) << 8);
}

static uint32_t read_u32(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
}

static uint64_t read_u64(const uint8_t *p) {
    return static_cast<uint64_t>(read_u32(p)) |
           (static_cast<uint64_t>(read_u32(p + 4)) << 32);
}

static bool valid_path(const uint8_t *path, uint16_t length) {
    if (!path || length == 0 || path[0] == '/' || path[length - 1] == '/') {
        return false;
    }

    uint16_t segment_length = 0;
    for (uint16_t i = 0; i < length; ++i) {
        const uint8_t ch = path[i];
        if (ch == '/') {
            if (segment_length == 0 ||
                (segment_length == 1 && path[i - 1] == '.') ||
                (segment_length == 2 && path[i - 1] == '.' && path[i - 2] == '.')) {
                return false;
            }
            segment_length = 0;
            continue;
        }

        const bool allowed = (ch >= 'a' && ch <= 'z') ||
                             (ch >= '0' && ch <= '9') ||
                             ch == '.' || ch == '_' || ch == '-';
        if (!allowed) {
            return false;
        }
        ++segment_length;
    }

    return !((segment_length == 1 && path[length - 1] == '.') ||
             (segment_length == 2 && path[length - 1] == '.' &&
              path[length - 2] == '.'));
}

static bool path_equals(const uint8_t *path, uint16_t length, const char *key) {
    uint16_t i = 0;
    for (; i < length && key[i] != 0; ++i) {
        if (path[i] != static_cast<uint8_t>(key[i])) {
            return false;
        }
    }
    return i == length && key[i] == 0;
}
} // namespace

extern "C" uint32_t koronos_registry_crc32(const uint8_t *data, uint32_t size) {
    if (!data && size != 0) {
        return 0;
    }

    uint32_t crc = 0xffffffffu;
    for (uint32_t i = 0; i < size; ++i) {
        crc ^= data[i];
        for (uint32_t bit = 0; bit < 8; ++bit) {
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
        }
    }
    return ~crc;
}

extern "C" int koronos_registry_validate(const void *raw, uint32_t size,
                                           koronos_registry_view *out) {
    static const uint8_t magic[8] = {'C', 'H', 'M', 'R', 'G', '0', '1', 0};
    constexpr uint32_t header_size = 40;
    constexpr uint32_t max_entries = 4096;
    constexpr uint32_t max_value_size = 1u << 20;
    constexpr uint32_t max_hive_size = 16u << 20;

    if (!raw || !out || size < header_size || size > max_hive_size) {
        return 0;
    }

    const uint8_t *data = static_cast<const uint8_t *>(raw);
    for (uint32_t i = 0; i < sizeof(magic); ++i) {
        if (data[i] != magic[i]) {
            return 0;
        }
    }

    const uint32_t entry_count = read_u32(data + 20);
    if (read_u16(data + 8) != 1 ||
        read_u16(data + 10) != 0 ||
        read_u32(data + 12) != header_size ||
        read_u32(data + 16) != size ||
        entry_count > max_entries ||
        read_u32(data + 36) != koronos_registry_crc32(data, 36) ||
        read_u32(data + 32) != koronos_registry_crc32(data + header_size,
                                                       size - header_size)) {
        return 0;
    }

    uint32_t offset = header_size;
    for (uint32_t i = 0; i < entry_count; ++i) {
        if (offset > size || size - offset < 8) {
            return 0;
        }

        const uint16_t path_length = read_u16(data + offset);
        const uint8_t type = data[offset + 2];
        const uint8_t flags = data[offset + 3];
        const uint32_t value_length = read_u32(data + offset + 4);
        offset += 8;

        if (path_length == 0 || path_length > 255 || flags != 0 ||
            type < KORONOS_REG_U32 || type > KORONOS_REG_BYTES ||
            value_length > max_value_size ||
            static_cast<uint64_t>(offset) + path_length + value_length > size) {
            return 0;
        }

        const uint8_t *path = data + offset;
        if (!valid_path(path, path_length)) {
            return 0;
        }

        uint32_t previous = header_size;
        for (uint32_t j = 0; j < i; ++j) {
            const uint16_t previous_path_length = read_u16(data + previous);
            const uint32_t previous_value_length = read_u32(data + previous + 4);
            if (previous_path_length == path_length) {
                bool equal = true;
                for (uint32_t k = 0; k < path_length; ++k) {
                    if (data[previous + 8 + k] != path[k]) {
                        equal = false;
                        break;
                    }
                }
                if (equal) {
                    return 0;
                }
            }
            previous += 8u + previous_path_length + previous_value_length;
        }

        const uint8_t *value = path + path_length;
        if ((type == KORONOS_REG_BOOL &&
             (value_length != 1 || value[0] > 1)) ||
            (type == KORONOS_REG_U32 && value_length != 4) ||
            (type == KORONOS_REG_U64 && value_length != 8)) {
            return 0;
        }

        offset += static_cast<uint32_t>(path_length) + value_length;
    }

    if (offset != size) {
        return 0;
    }

    out->data = data;
    out->size = size;
    out->entry_count = entry_count;
    out->generation = read_u64(data + 24);
    return 1;
}

extern "C" int koronos_registry_find(const koronos_registry_view *view,
                                      const char *path, uint8_t expected_type,
                                      const uint8_t **value,
                                      uint32_t *value_size) {
    if (!view || !view->data || !path || !value || !value_size ||
        view->size < 40) {
        return 0;
    }

    uint32_t offset = 40;
    for (uint32_t i = 0; i < view->entry_count; ++i) {
        if (offset > view->size || view->size - offset < 8) {
            return 0;
        }
        const uint16_t path_length = read_u16(view->data + offset);
        const uint8_t type = view->data[offset + 2];
        const uint32_t length = read_u32(view->data + offset + 4);
        offset += 8;
        if (static_cast<uint64_t>(offset) + path_length + length > view->size) {
            return 0;
        }

        if (path_equals(view->data + offset, path_length, path) &&
            (expected_type == 0 || expected_type == type)) {
            *value = view->data + offset + path_length;
            *value_size = length;
            return 1;
        }
        offset += static_cast<uint32_t>(path_length) + length;
    }
    return 0;
}
extern "C" int koronos_registry_read_u64(const koronos_registry_view *view,
                                          const char *path, uint64_t *out) {
    const uint8_t *value = nullptr;
    uint32_t size = 0;
    if (!out) {
        return 0;
    }

    if (koronos_registry_find(view, path, KORONOS_REG_U32, &value, &size) &&
        size == 4) {
        *out = read_u32(value);
        return 1;
    }
    if (koronos_registry_find(view, path, KORONOS_REG_U64, &value, &size) &&
        size == 8) {
        *out = read_u64(value);
        return 1;
    }
    return 0;
}

extern "C" int koronos_registry_read_bool(const koronos_registry_view *view,
                                           const char *path, uint8_t *out) {
    const uint8_t *value = nullptr;
    uint32_t size = 0;
    if (!out ||
        !koronos_registry_find(view, path, KORONOS_REG_BOOL, &value, &size) ||
        size != 1 || value[0] > 1) {
        return 0;
    }

    *out = value[0];
    return 1;
}
