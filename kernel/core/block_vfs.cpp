#include "chimera/block.h"
#include "chimera/vfs.h"

/* Partition discovery and KoronosFS v2. Every file operation below performs
 * real 512-byte block I/O through the virtio-blk backend. There are no fixed
 * marker sectors, synthetic sector reads, or hardcoded file contents. */

namespace {

constexpr uint32_t SECTOR = KORONOS_BLOCK_SECTOR_SIZE;
constexpr uint32_t GPT_ENTRY_COUNT = 128u;
constexpr uint32_t GPT_ENTRY_SIZE = 128u;
constexpr uint32_t GPT_ENTRY_SECTORS = GPT_ENTRY_COUNT * GPT_ENTRY_SIZE / SECTOR;
constexpr uint32_t INODE_TABLE_BYTES = KORONOSFS_V2_INODE_TABLE_SECTORS * SECTOR;
constexpr uint32_t BITMAP_BYTES = KORONOSFS_V2_BITMAP_SECTORS * SECTOR;
constexpr uint32_t MAX_FILE_BLOCKS = 8u + 128u + 128u * 128u;
constexpr uint32_t MAX_FILE_SIZE = MAX_FILE_BLOCKS * SECTOR;

static_assert(sizeof(koronosfs_superblock_t) == 512u, "KoronosFS superblock must be one sector");
static_assert(sizeof(koronosfs_inode_t) == 64u, "KoronosFS inode must be 64 bytes");
static_assert(sizeof(koronosfs_dirent_t) == 64u, "KoronosFS dirent must be 64 bytes");
static_assert(KORONOSFS_V2_CONTENT_MAX <= MAX_FILE_SIZE, "content limit exceeds addressable file size");

static inline void out8_(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}
static void debug_(const char *text) {
    while (*text) out8_(0xE9, static_cast<uint8_t>(*text++));
    out8_(0xE9, '\n');
}
static void debug_u64_(const char *label, uint64_t value, bool hex) {
    char line[96];
    uint32_t pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    static const char digits[] = "0123456789ABCDEF";
    char reversed[24];
    uint32_t n = 0;
    if (value == 0) reversed[n++] = '0';
    while (value && n < sizeof(reversed)) {
        reversed[n++] = digits[static_cast<uint32_t>(value % (hex ? 16u : 10u))];
        value /= hex ? 16u : 10u;
    }
    while (n && pos + 1u < sizeof(line)) line[pos++] = reversed[--n];
    line[pos] = 0;
    debug_(line);
}

static void set_bytes_(uint8_t *dst, uint8_t value, uint32_t length) {
    for (uint32_t i = 0; i < length; ++i) dst[i] = value;
}
static void copy_bytes_(uint8_t *dst, const uint8_t *src, uint32_t length) {
    for (uint32_t i = 0; i < length; ++i) dst[i] = src[i];
}
static uint32_t load32_(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) | (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) | (static_cast<uint32_t>(p[3]) << 24);
}
static void store32_(uint8_t *p, uint32_t v) {
    for (uint32_t i = 0; i < 4; ++i) p[i] = static_cast<uint8_t>(v >> (8u * i));
}
static uint64_t load64_(const uint8_t *p) {
    uint64_t v = 0;
    for (uint32_t i = 0; i < 8; ++i) v |= static_cast<uint64_t>(p[i]) << (8u * i);
    return v;
}
static void store64_(uint8_t *p, uint64_t v) {
    for (uint32_t i = 0; i < 8; ++i) p[i] = static_cast<uint8_t>(v >> (8u * i));
}
static uint32_t crc32_(const uint8_t *data, uint32_t length) {
    uint32_t crc = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (uint32_t bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}
static uint64_t fnv64_(const uint8_t *data, uint32_t length) {
    uint64_t hash = 14695981039346656037ull;
    for (uint32_t i = 0; i < length; ++i) {
        hash ^= data[i];
        hash *= 1099511628211ull;
    }
    return hash;
}
static uint32_t text_length_(const char *text) {
    uint32_t n = 0;
    while (text && text[n] && n < 4096u) ++n;
    return n;
}
static bool guid_equal_(const uint8_t *a, const uint8_t *b) {
    for (uint32_t i = 0; i < 16; ++i) if (a[i] != b[i]) return false;
    return true;
}
static bool guid_zero_(const uint8_t *g) {
    for (uint32_t i = 0; i < 16; ++i) if (g[i]) return false;
    return true;
}
static void utf16_name_(char *dst, const uint8_t *src, uint32_t bytes) {
    uint32_t n = 0;
    for (uint32_t i = 0; i + 1 < bytes && n < 71; i += 2) {
        if (!src[i] && !src[i + 1]) break;
        dst[n++] = src[i] ? static_cast<char>(src[i]) : '?';
    }
    dst[n] = 0;
}
static void set_utf16_name_(uint8_t *dst, const char *name) {
    set_bytes_(dst, 0, 72);
    for (uint32_t i = 0; name[i] && i < 36; ++i) dst[i * 2] = static_cast<uint8_t>(name[i]);
}

/* ---- GPT partition layer ------------------------------------------------ */

struct PartitionCache {
    uint32_t count;
    koronos_partition_t entries[KORONOS_PARTITION_MAX];
};
static PartitionCache partitions_;
static bool block_scanned_ = false;
static uint64_t block_bytes_written_ = 0;
static uint64_t block_bytes_read_ = 0;
static uint64_t bytes_written_ = 0; /* payload bytes handed to the filesystem */
static uint64_t bytes_read_ = 0;    /* payload bytes returned by the filesystem */

alignas(16) static uint8_t gpt_header_[SECTOR];
alignas(16) static uint8_t gpt_entries_[GPT_ENTRY_COUNT * GPT_ENTRY_SIZE];

static bool read_sector_raw_(uint64_t lba, uint8_t *buffer) {
    return koronos_block_read(lba, buffer) == 0;
}
static bool write_sector_raw_(uint64_t lba, const uint8_t *buffer) {
    return koronos_block_write(lba, buffer) == 0;
}

static bool gpt_header_valid_(const uint8_t *header) {
    static const char signature[] = "EFI PART";
    for (uint32_t i = 0; i < 8; ++i) if (header[i] != static_cast<uint8_t>(signature[i])) return false;
    const uint32_t header_size = load32_(header + 12);
    if (header_size < 92 || header_size > SECTOR) return false;
    const uint32_t stored_crc = load32_(header + 16);
    uint8_t copy[SECTOR];
    copy_bytes_(copy, header, SECTOR);
    store32_(copy + 16, 0);
    return crc32_(copy, header_size) == stored_crc;
}

static uint32_t parse_gpt_(uint64_t total) {
    if (!read_sector_raw_(1, gpt_header_) || !gpt_header_valid_(gpt_header_)) return 0;
    const uint64_t first_usable = load64_(gpt_header_ + 40);
    const uint64_t last_usable = load64_(gpt_header_ + 48);
    const uint64_t entries_lba = load64_(gpt_header_ + 72);
    const uint32_t entry_count = load32_(gpt_header_ + 80);
    const uint32_t entry_size = load32_(gpt_header_ + 84);
    if (entry_count == 0 || entry_count > GPT_ENTRY_COUNT || entry_size != GPT_ENTRY_SIZE) return 0;
    const uint64_t table_sectors = (static_cast<uint64_t>(entry_count) * entry_size + SECTOR - 1u) / SECTOR;
    if (entries_lba == 0 || entries_lba + table_sectors > total) return 0;

    uint32_t found = 0;
    for (uint64_t sector = 0; sector < table_sectors; ++sector) {
        if (!read_sector_raw_(entries_lba + sector, gpt_entries_ + sector * SECTOR)) return found;
    }
    for (uint32_t i = 0; i < entry_count && found < KORONOS_PARTITION_MAX; ++i) {
        const uint8_t *entry = gpt_entries_ + static_cast<uint64_t>(i) * entry_size;
        if (guid_zero_(entry)) continue;
        const uint64_t start = load64_(entry + 32);
        const uint64_t end = load64_(entry + 40);
        if (end < start || start < first_usable || end > last_usable || end >= total) continue;
        koronos_partition_t &p = partitions_.entries[found];
        copy_bytes_(p.type_guid, entry, 16);
        copy_bytes_(p.unique_guid, entry + 16, 16);
        p.index = found;
        p.start_lba = start;
        p.sector_count = end - start + 1u;
        p.flags = load64_(entry + 48);
        utf16_name_(p.name, entry + 56, 72);
        ++found;
    }
    return found;
}

static uint32_t parse_mbr_(void) {
    uint8_t sector[SECTOR];
    if (!read_sector_raw_(0, sector)) return 0;
    if (sector[510] != 0x55u || sector[511] != 0xAAu) return 0;
    uint32_t found = 0;
    for (uint32_t i = 0; i < 4 && found < KORONOS_PARTITION_MAX; ++i) {
        const uint8_t *entry = sector + 446u + i * 16u;
        const uint8_t type = entry[4];
        const uint32_t start = load32_(entry + 8);
        const uint32_t count = load32_(entry + 12);
        if (!type || !start || !count) continue;
        koronos_partition_t &p = partitions_.entries[found];
        set_bytes_(p.type_guid, 0, 16);
        set_bytes_(p.unique_guid, 0, 16);
        p.type_guid[0] = type;
        p.index = found;
        p.start_lba = start;
        p.sector_count = count;
        p.flags = 0;
        p.name[0] = 0;
        ++found;
    }
    return found;
}

static void write_gpt_header_(uint64_t lba, uint64_t current, uint64_t backup,
                              uint64_t first, uint64_t last, uint64_t entries_lba,
                              const uint8_t disk_guid[16]) {
    uint8_t h[SECTOR];
    set_bytes_(h, 0, SECTOR);
    static const char signature[] = "EFI PART";
    for (uint32_t i = 0; i < 8; ++i) h[i] = static_cast<uint8_t>(signature[i]);
    store32_(h + 8, 0x00010000u);
    store32_(h + 12, 92u);
    store32_(h + 16, 0u);
    store32_(h + 20, 0u);
    store64_(h + 24, current);
    store64_(h + 32, backup);
    store64_(h + 40, first);
    store64_(h + 48, last);
    copy_bytes_(h + 56, disk_guid, 16);
    store64_(h + 72, entries_lba);
    store32_(h + 80, GPT_ENTRY_COUNT);
    store32_(h + 84, GPT_ENTRY_SIZE);
    store32_(h + 88, crc32_(gpt_entries_, GPT_ENTRY_COUNT * GPT_ENTRY_SIZE));
    store32_(h + 16, crc32_(h, 92u));
    write_sector_raw_(lba, h);
}

/* ---- In-memory mount objects -------------------------------------------- */

struct Mount {
    bool in_use;
    uint32_t partition_index;
    uint64_t start;
    uint64_t sectors;
    uint64_t token;
    koronosfs_superblock_t sb;
    uint8_t bitmap[BITMAP_BYTES];
    koronosfs_inode_t inodes[KORONOSFS_V2_INODE_COUNT];
    bool inode_valid[KORONOSFS_V2_INODE_COUNT];
};
static Mount mounts_[KORONOS_VFS_MOUNT_MAX];
static bool vfs_ready_ = false;

static void superblock_checksum_(koronosfs_superblock_t *sb) {
    store32_(reinterpret_cast<uint8_t *>(sb) + 508, 0);
    const uint32_t crc = crc32_(reinterpret_cast<const uint8_t *>(sb), 508);
    store32_(reinterpret_cast<uint8_t *>(sb) + 508, crc);
}
static bool superblock_valid_(const koronosfs_superblock_t *sb) {
    const uint8_t *bytes = reinterpret_cast<const uint8_t *>(sb);
    static const char magic[] = KORONOSFS_V2_MAGIC;
    for (uint32_t i = 0; i < 16; ++i) if (bytes[i] != static_cast<uint8_t>(magic[i])) return false;
    if (sb->version != KORONOSFS_V2_VERSION) return false;
    if (sb->inode_count != KORONOSFS_V2_INODE_COUNT ||
        sb->inode_table_start != KORONOSFS_V2_INODE_TABLE_SECTOR ||
        sb->inode_table_sectors != KORONOSFS_V2_INODE_TABLE_SECTORS ||
        sb->bitmap_start != KORONOSFS_V2_BITMAP_SECTOR ||
        sb->bitmap_sectors != KORONOSFS_V2_BITMAP_SECTORS ||
        sb->data_start != KORONOSFS_V2_DATA_SECTOR) return false;
    if (sb->data_sectors == 0 || sb->data_sectors > 32768u) return false;
    return load32_(bytes + 508) == crc32_(bytes, 508);
}
static void inode_checksum_(koronosfs_inode_t *inode) {
    uint8_t *bytes = reinterpret_cast<uint8_t *>(inode);
    store32_(bytes + 60, 0);
    store32_(bytes + 60, crc32_(bytes, 60));
}
static void refresh_inode_checksum_(koronosfs_inode_t *inode) {
    uint8_t *bytes = reinterpret_cast<uint8_t *>(inode);
    store32_(bytes + 60, crc32_(bytes, 60));
}
static bool inode_checksum_valid_(const koronosfs_inode_t *inode) {
    const uint8_t *bytes = reinterpret_cast<const uint8_t *>(inode);
    return load32_(bytes + 60) == crc32_(bytes, 60);
}
static bool mount_valid_(int mount) {
    return mount >= 0 && static_cast<uint32_t>(mount) < KORONOS_VFS_MOUNT_MAX && mounts_[mount].in_use;
}
static bool read_fs_sector_(Mount &m, uint32_t relative, uint8_t *buffer) {
    if (static_cast<uint64_t>(relative) >= m.sectors) return false;
    return read_sector_raw_(m.start + relative, buffer);
}
static bool write_fs_sector_(Mount &m, uint32_t relative, const uint8_t *buffer) {
    if (static_cast<uint64_t>(relative) >= m.sectors) return false;
    return write_sector_raw_(m.start + relative, buffer);
}
static bool load_inode_(Mount &m, uint32_t number, koronosfs_inode_t *out) {
    if (number == 0 || number >= m.sb.inode_count || !m.inode_valid[number - 1]) return false;
    if (out) *out = m.inodes[number - 1];
    return true;
}
static bool flush_inode_(Mount &m, uint32_t number) {
    if (number == 0 || number >= m.sb.inode_count) return false;
    const uint32_t slot = number - 1;
    koronosfs_inode_t &inode = m.inodes[slot];
    refresh_inode_checksum_(&inode);
    uint8_t table[INODE_TABLE_BYTES];
    for (uint32_t sector = 0; sector < m.sb.inode_table_sectors; ++sector) {
        if (!read_fs_sector_(m, m.sb.inode_table_start + sector, table + sector * SECTOR)) return false;
    }
    copy_bytes_(table + slot * sizeof(koronosfs_inode_t),
                reinterpret_cast<const uint8_t *>(&inode), sizeof(koronosfs_inode_t));
    for (uint32_t sector = 0; sector < m.sb.inode_table_sectors; ++sector) {
        if (!write_fs_sector_(m, m.sb.inode_table_start + sector, table + sector * SECTOR)) return false;
    }
    m.inode_valid[slot] = true;
    return true;
}
static void flush_bitmap_(Mount &m) {
    for (uint32_t sector = 0; sector < m.sb.bitmap_sectors; ++sector)
        write_fs_sector_(m, m.sb.bitmap_start + sector, m.bitmap + sector * SECTOR);
}
/* Returns the allocated data-block number; block 0 is reserved, so 0 means
 * allocation failed. The allocation bitmap is persisted before the pointer is
 * handed back to the caller. */
static uint32_t allocate_block_(Mount &m, koronosfs_inode_t *inode) {
    for (uint32_t byte = 0; byte < m.sb.bitmap_sectors * SECTOR; ++byte) {
        const uint32_t first_bit = byte * 8u;
        if (first_bit >= m.sb.data_sectors) return 0;
        if (m.bitmap[byte] == 0xFFu) continue;
        for (uint32_t bit = 0; bit < 8; ++bit) {
            if (first_bit + bit >= m.sb.data_sectors) return 0;
            if (m.bitmap[byte] & (1u << bit)) continue;
            m.bitmap[byte] = static_cast<uint8_t>(m.bitmap[byte] | (1u << bit));
            const uint32_t sector = m.sb.bitmap_start + byte / SECTOR;
            write_fs_sector_(m, sector, m.bitmap + static_cast<uint64_t>(sector - m.sb.bitmap_start) * SECTOR);
            if (inode) ++inode->blocks;
            return first_bit + bit;
        }
    }
    return 0;
}
static void free_block_(Mount &m, uint32_t block) {
    if (block >= m.sb.data_sectors) return;
    const uint32_t byte = block / 8u;
    m.bitmap[byte] = static_cast<uint8_t>(m.bitmap[byte] & ~(1u << (block % 8u)));
    write_fs_sector_(m, m.sb.bitmap_start + byte / SECTOR,
                     m.bitmap + static_cast<uint64_t>(byte / SECTOR) * SECTOR);
}
static bool read_table_sector_(Mount &m, uint32_t block, uint8_t *buffer) {
    if (block >= m.sb.data_sectors) return false;
    return read_fs_sector_(m, m.sb.data_start + block, buffer);
}
static bool write_table_sector_(Mount &m, uint32_t block, const uint8_t *buffer) {
    if (block >= m.sb.data_sectors) return false;
    return write_fs_sector_(m, m.sb.data_start + block, buffer);
}
static uint32_t pointer_for_block_(Mount &m, koronosfs_inode_t *inode, uint32_t block, bool create) {
    if (block >= MAX_FILE_BLOCKS) return 0;
    if (block < 8u) {
        if (!inode->direct[block] && create) {
            const uint32_t allocated = allocate_block_(m, inode);
            if (!allocated) return 0;
            inode->direct[block] = allocated;
        }
        return inode->direct[block];
    }
    uint8_t table[SECTOR];
    if (block < 136u) {
        const uint32_t slot = block - 8u;
        if (!inode->indirect) {
            if (!create) return 0;
            inode->indirect = allocate_block_(m, inode);
            if (!inode->indirect) return 0;
            set_bytes_(table, 0, SECTOR);
            write_table_sector_(m, inode->indirect, table);
        }
        if (!read_table_sector_(m, inode->indirect, table)) return 0;
        const uint32_t pointer = load32_(table + slot * 4u);
        if (pointer || !create) return pointer;
        const uint32_t allocated = allocate_block_(m, inode);
        if (!allocated) return 0;
        store32_(table + slot * 4u, allocated);
        write_table_sector_(m, inode->indirect, table);
        return allocated;
    }
    const uint32_t first = (block - 136u) / 128u;
    const uint32_t slot = (block - 136u) % 128u;
    uint8_t outer[SECTOR];
    if (!inode->double_indirect) {
        if (!create) return 0;
        inode->double_indirect = allocate_block_(m, inode);
        if (!inode->double_indirect) return 0;
        set_bytes_(outer, 0, SECTOR);
        write_table_sector_(m, inode->double_indirect, outer);
    }
    if (!read_table_sector_(m, inode->double_indirect, outer)) return 0;
    uint32_t inner_block = load32_(outer + first * 4u);
    if (!inner_block) {
        if (!create) return 0;
        inner_block = allocate_block_(m, inode);
        if (!inner_block) return 0;
        store32_(outer + first * 4u, inner_block);
        write_table_sector_(m, inode->double_indirect, outer);
        set_bytes_(table, 0, SECTOR);
        write_table_sector_(m, inner_block, table);
    }
    if (!read_table_sector_(m, inner_block, table)) return 0;
    const uint32_t pointer = load32_(table + slot * 4u);
    if (pointer || !create) return pointer;
    const uint32_t allocated = allocate_block_(m, inode);
    if (!allocated) return 0;
    store32_(table + slot * 4u, allocated);
    write_table_sector_(m, inner_block, table);
    return allocated;
}

/* ---- Directory operations ------------------------------------------------ */

static uint32_t dirent_slot_(Mount &m, uint32_t dir_inode, const char *name, bool for_write) {
    koronosfs_inode_t dir;
    if (!load_inode_(m, dir_inode, &dir) || dir.type != KORONOSFS_TYPE_DIRECTORY) return 0xFFFFFFFFu;
    uint8_t block[SECTOR];
    const uint32_t dir_blocks = (dir.size + SECTOR - 1u) / SECTOR;
    uint32_t first_empty = 0xFFFFFFFFu;
    for (uint32_t b = 0; b < dir_blocks; ++b) {
        const uint32_t pointer = pointer_for_block_(m, &dir, b, false);
        if (!pointer || !read_table_sector_(m, pointer, block)) return 0xFFFFFFFFu;
        for (uint32_t i = 0; i < 8; ++i) {
            const koronosfs_dirent_t *entry =
                reinterpret_cast<const koronosfs_dirent_t *>(block + i * sizeof(koronosfs_dirent_t));
            if (!entry->name[0]) {
                if (first_empty == 0xFFFFFFFFu && for_write) first_empty = b * 8u + i;
                continue;
            }
            uint32_t n = 0;
            while (n < KORONOSFS_V2_NAME_MAX && entry->name[n] == name[n]) {
                if (!name[n]) break;
                ++n;
            }
            if (name[n] == 0 && entry->name[n] == 0) return b * 8u + i;
        }
    }
    return for_write ? first_empty : 0xFFFFFFFFu;
}
static bool dirent_at_(Mount &m, uint32_t dir_inode, uint32_t slot, koronosfs_dirent_t *out) {
    koronosfs_inode_t dir;
    if (!load_inode_(m, dir_inode, &dir)) return false;
    const uint32_t pointer = pointer_for_block_(m, &dir, slot / 8u, false);
    if (!pointer) return false;
    uint8_t block[SECTOR];
    if (!read_table_sector_(m, pointer, block)) return false;
    *out = *reinterpret_cast<const koronosfs_dirent_t *>(block + (slot % 8u) * sizeof(koronosfs_dirent_t));
    return out->name[0] != 0;
}
static bool dirent_store_(Mount &m, uint32_t dir_inode, uint32_t slot, uint32_t inode,
                          const char *name, uint8_t type) {
    koronosfs_inode_t dir;
    if (!load_inode_(m, dir_inode, &dir)) return false;
    const uint32_t pointer = pointer_for_block_(m, &dir, slot / 8u, true);
    if (!pointer) return false;
    uint8_t block[SECTOR];
    if (!read_table_sector_(m, pointer, block)) return false;
    koronosfs_dirent_t entry;
    set_bytes_(reinterpret_cast<uint8_t *>(&entry), 0, sizeof(entry));
    for (uint32_t i = 0; i < KORONOSFS_V2_NAME_MAX; ++i) {
        entry.name[i] = name[i];
        if (!name[i]) break;
    }
    entry.inode = inode;
    entry.type = type;
    entry.flags = 1u;
    *reinterpret_cast<koronosfs_dirent_t *>(block + (slot % 8u) * sizeof(koronosfs_dirent_t)) = entry;
    if (!write_table_sector_(m, pointer, block)) return false;
    const uint32_t needed = ((slot / 8u) + 1u) * SECTOR;
    if (dir.size < needed) dir.size = needed;
    return flush_inode_(m, dir_inode);
}

} // namespace

/* ---- Block layer exports ------------------------------------------------- */

extern "C" int koronos_block_init(void) {
    if (koronos_native_block_init() != 0) return -1;
    if (!block_scanned_) {
        partitions_.count = 0;
        const uint64_t total = koronos_block_sector_count();
        if (total > 64) {
            partitions_.count = parse_gpt_(total);
            if (partitions_.count == 0) partitions_.count = parse_mbr_();
        }
        block_scanned_ = true;
        debug_u64_("[BLK ] total_sectors=", total, false);
        debug_u64_("[BLK ] partition_count=", partitions_.count, false);
    }
    return 0;
}
extern "C" int koronos_block_ready(void) { return block_scanned_ && koronos_block_sector_count() > 0 ? 1 : 0; }
extern "C" uint64_t koronos_block_sector_count(void) { return koronos_native_stack_block_sectors(); }
extern "C" int koronos_block_read(uint64_t lba, uint8_t *buffer) {
    if (!buffer || lba >= koronos_block_sector_count()) return -1;
    if (koronos_native_block_read(static_cast<uint32_t>(lba), buffer) != 0) return -1;
    block_bytes_read_ += SECTOR;
    return 0;
}
extern "C" int koronos_block_write(uint64_t lba, const uint8_t *buffer) {
    if (!buffer || lba >= koronos_block_sector_count()) return -1;
    if (koronos_native_block_write(static_cast<uint32_t>(lba), buffer) != 0) return -1;
    block_bytes_written_ += SECTOR;
    return 0;
}
extern "C" uint32_t koronos_block_partition_count(void) { return partitions_.count; }
extern "C" int koronos_block_partition(uint32_t index, koronos_partition_t *out) {
    if (!out || index >= partitions_.count) return -1;
    *out = partitions_.entries[index];
    return 0;
}
extern "C" int koronos_block_find_partition(const uint8_t type_guid[16], koronos_partition_t *out) {
    if (!type_guid || !out) return -1;
    for (uint32_t i = 0; i < partitions_.count; ++i) {
        if (guid_equal_(partitions_.entries[i].type_guid, type_guid)) {
            *out = partitions_.entries[i];
            return 0;
        }
    }
    return -1;
}
extern "C" int koronos_block_scan_partitions(void) {
    block_scanned_ = false;
    return koronos_block_init();
}
extern "C" int koronos_block_format_gpt(uint64_t root_start, uint64_t root_sectors,
                                         uint64_t journal_start, uint64_t journal_sectors,
                                         const uint8_t root_type_guid[16],
                                         const uint8_t journal_type_guid[16]) {
    if (koronos_block_init() != 0 || !root_type_guid || !journal_type_guid) return -1;
    const uint64_t total = koronos_block_sector_count();
    const uint64_t last_usable = total - 34u;
    if (total < 1024u || root_start < 34u || journal_start < root_start + root_sectors ||
        journal_start + journal_sectors - 1u > last_usable) return -1;

    uint8_t mbr[SECTOR];
    set_bytes_(mbr, 0, SECTOR);
    mbr[0] = 0xEEu;
    store32_(mbr + 8, 1u);
    const uint64_t protective = total - 1u > 0xFFFFFFFFull ? 0xFFFFFFFFull : total - 1u;
    store32_(mbr + 12, static_cast<uint32_t>(protective));
    mbr[510] = 0x55u;
    mbr[511] = 0xAAu;
    if (!write_sector_raw_(0, mbr)) return -1;

    set_bytes_(gpt_entries_, 0, sizeof(gpt_entries_));
    static const uint8_t disk_guid[16] = {0x4B, 'K', 'R', 'N', 'S', 0x20, 'G', 'P',
                                          'T', 0x5A, '3', '2', 0x12, 0x34, 0x56, 0x78};
    struct EntryLayout { const uint8_t *guid; uint64_t start; uint64_t count; const char *name; };
    const EntryLayout layouts[2] = {
        {root_type_guid, root_start, root_sectors, "KoronosRoot"},
        {journal_type_guid, journal_start, journal_sectors, "KoronosJournal"},
    };
    for (uint32_t i = 0; i < 2; ++i) {
        uint8_t *entry = gpt_entries_ + i * GPT_ENTRY_SIZE;
        copy_bytes_(entry, layouts[i].guid, 16);
        copy_bytes_(entry + 16, disk_guid, 16);
        entry[16] = static_cast<uint8_t>(entry[16] + i + 1u);
        store64_(entry + 32, layouts[i].start);
        store64_(entry + 40, layouts[i].start + layouts[i].count - 1u);
        store64_(entry + 48, 0u);
        set_utf16_name_(entry + 56, layouts[i].name);
    }
    for (uint64_t sector = 0; sector < GPT_ENTRY_SECTORS; ++sector) {
        if (!write_sector_raw_(2 + sector, gpt_entries_ + sector * SECTOR)) return -1;
    }
    write_gpt_header_(1, 1, total - 1u, 34, last_usable, 2, disk_guid);
    const uint64_t backup_entries = total - 1u - GPT_ENTRY_SECTORS;
    for (uint64_t sector = 0; sector < GPT_ENTRY_SECTORS; ++sector) {
        if (!write_sector_raw_(backup_entries + sector, gpt_entries_ + sector * SECTOR)) return -1;
    }
    write_gpt_header_(total - 1u, total - 1u, 1, 34, last_usable, backup_entries, disk_guid);

    block_scanned_ = false;
    if (koronos_block_init() != 0 || partitions_.count < 2) return -1;
    debug_u64_("[BLK ] part_count=", partitions_.count, false);
    for (uint32_t i = 0; i < partitions_.count; ++i) {
        debug_u64_("[BLK ] partition=", i, false);
        debug_u64_("[BLK ] part_start=", partitions_.entries[i].start_lba, false);
        debug_u64_("[BLK ] part_sectors=", partitions_.entries[i].sector_count, false);
    }
    return 0;
}

/* ---- Filesystem exports --------------------------------------------------- */

extern "C" int koronos_vfs_init(void) {
    if (vfs_ready_) return 0;
    if (koronos_block_init() != 0) return -1;
    set_bytes_(reinterpret_cast<uint8_t *>(mounts_), 0, sizeof(mounts_));
    vfs_ready_ = true;
    return 0;
}
extern "C" int koronos_vfs_ready(void) { return vfs_ready_ ? 1 : 0; }
extern "C" uint64_t koronos_vfs_bytes_written(void) { return bytes_written_; }
extern "C" uint64_t koronos_vfs_bytes_read(void) { return bytes_read_; }
extern "C" uint64_t koronos_vfs_digest(const uint8_t *data, uint32_t length) {
    return data ? fnv64_(data, length) : 0;
}
extern "C" int koronos_vfs_find_by_type(const uint8_t type_guid[16], koronos_partition_t *out) {
    if (koronos_block_init() != 0) return -1;
    return koronos_block_find_partition(type_guid, out);
}

extern "C" int koronos_vfs_format(uint32_t partition_index) {
    if (koronos_vfs_init() != 0) return -1;
    koronos_partition_t partition;
    if (koronos_block_partition(partition_index, &partition) != 0) return -1;
    if (partition.sector_count <= KORONOSFS_V2_DATA_SECTOR + 64u) return -1;

    koronosfs_superblock_t sb;
    set_bytes_(reinterpret_cast<uint8_t *>(&sb), 0, sizeof(sb));
    static const char magic[] = KORONOSFS_V2_MAGIC;
    for (uint32_t i = 0; i < 16; ++i) sb.magic[i] = static_cast<uint8_t>(magic[i]);
    sb.version = KORONOSFS_V2_VERSION;
    sb.state = KORONOSFS_STATE_CLEAN;
    sb.sector_count = partition.sector_count;
    sb.inode_count = KORONOSFS_V2_INODE_COUNT;
    sb.inode_table_start = KORONOSFS_V2_INODE_TABLE_SECTOR;
    sb.inode_table_sectors = KORONOSFS_V2_INODE_TABLE_SECTORS;
    sb.bitmap_start = KORONOSFS_V2_BITMAP_SECTOR;
    sb.bitmap_sectors = KORONOSFS_V2_BITMAP_SECTORS;
    sb.data_start = KORONOSFS_V2_DATA_SECTOR;
    sb.data_sectors = static_cast<uint32_t>(partition.sector_count - KORONOSFS_V2_DATA_SECTOR);
    if (sb.data_sectors > 32768u) sb.data_sectors = 32768u;
    sb.root_inode = 1u;
    sb.generation = 1u;
    sb.mount_count = 0u;
    superblock_checksum_(&sb);

    uint8_t zero[SECTOR];
    set_bytes_(zero, 0, SECTOR);
    if (koronos_block_write(partition.start_lba + KORONOSFS_V2_SUPERBLOCK_SECTOR,
                            reinterpret_cast<const uint8_t *>(&sb)) != 0) return -1;
    for (uint32_t sector = KORONOSFS_V2_INODE_TABLE_SECTOR;
         sector < KORONOSFS_V2_BITMAP_SECTOR + KORONOSFS_V2_BITMAP_SECTORS; ++sector) {
        if (koronos_block_write(partition.start_lba + sector, zero) != 0) return -1;
    }

    koronosfs_inode_t root;
    set_bytes_(reinterpret_cast<uint8_t *>(&root), 0, sizeof(root));
    root.type = KORONOSFS_TYPE_DIRECTORY;
    root.flags = 1u;
    root.size = SECTOR;
    root.blocks = 1u;
    root.direct[0] = 1u; /* block 0 is reserved; a zero pointer means unallocated */
    inode_checksum_(&root);
    uint8_t table[INODE_TABLE_BYTES];
    set_bytes_(table, 0, sizeof(table));
    copy_bytes_(table, reinterpret_cast<const uint8_t *>(&root), sizeof(root));
    for (uint32_t sector = 0; sector < KORONOSFS_V2_INODE_TABLE_SECTORS; ++sector) {
        if (koronos_block_write(partition.start_lba + KORONOSFS_V2_INODE_TABLE_SECTOR + sector,
                                table + sector * SECTOR) != 0) return -1;
    }
    uint8_t bitmap[BITMAP_BYTES];
    set_bytes_(bitmap, 0, sizeof(bitmap));
    bitmap[0] = 0x03u; /* block 0 reserved (zero pointer); block 1 = root directory */
    for (uint32_t sector = 0; sector < KORONOSFS_V2_BITMAP_SECTORS; ++sector) {
        if (koronos_block_write(partition.start_lba + KORONOSFS_V2_BITMAP_SECTOR + sector,
                                bitmap + sector * SECTOR) != 0) return -1;
    }
    if (koronos_block_write(partition.start_lba + KORONOSFS_V2_DATA_SECTOR + 1u, zero) != 0) return -1;
    debug_u64_("[VFS ] format_partition=", partition_index, false);
    debug_u64_("[VFS ] format_data_sectors=", sb.data_sectors, false);
    return 0;
}

extern "C" int koronos_vfs_mount(uint32_t partition_index, int *mount_out) {
    if (koronos_vfs_init() != 0) return -1;
    koronos_partition_t partition;
    if (koronos_block_partition(partition_index, &partition) != 0) return -1;
    int slot = -1;
    for (uint32_t i = 0; i < KORONOS_VFS_MOUNT_MAX; ++i) {
        if (!mounts_[i].in_use) { slot = static_cast<int>(i); break; }
    }
    if (slot < 0) return -1;
    Mount &m = mounts_[slot];
    set_bytes_(reinterpret_cast<uint8_t *>(&m), 0, sizeof(m));
    uint8_t sector[SECTOR];
    if (!read_sector_raw_(partition.start_lba, sector)) return -1;
    koronosfs_superblock_t sb;
    copy_bytes_(reinterpret_cast<uint8_t *>(&sb), sector, sizeof(sb));
    if (!superblock_valid_(&sb)) {
        debug_("[VFS ] mount rejected: invalid superblock checksum");
        return -1;
    }
    uint8_t table[INODE_TABLE_BYTES];
    for (uint32_t i = 0; i < sb.inode_table_sectors; ++i) {
        if (!read_sector_raw_(partition.start_lba + sb.inode_table_start + i,
                              table + i * SECTOR)) return -1;
    }
    for (uint32_t i = 0; i < sb.bitmap_sectors; ++i) {
        if (!read_sector_raw_(partition.start_lba + sb.bitmap_start + i,
                              m.bitmap + i * SECTOR)) return -1;
    }
    for (uint32_t i = 0; i < sb.inode_count && i < KORONOSFS_V2_INODE_COUNT; ++i) {
        m.inodes[i] = *reinterpret_cast<const koronosfs_inode_t *>(table + i * sizeof(koronosfs_inode_t));
        m.inode_valid[i] = (m.inodes[i].flags & 1u) && inode_checksum_valid_(&m.inodes[i]);
    }
    if (!m.inode_valid[sb.root_inode - 1]) return -1;
    m.in_use = true;
    m.partition_index = partition_index;
    m.start = partition.start_lba;
    m.sectors = partition.sector_count;
    m.token = ++sb.mount_count;
    sb.state = KORONOSFS_STATE_DIRTY;
    ++sb.generation;
    superblock_checksum_(&sb);
    m.sb = sb;
    if (!write_fs_sector_(m, KORONOSFS_V2_SUPERBLOCK_SECTOR,
                          reinterpret_cast<const uint8_t *>(&sb))) {
        m.in_use = false;
        return -1;
    }
    debug_u64_("[VFS ] mount_state=", 1, false);
    debug_u64_("[VFS ] mount_partition=", partition_index, false);
    debug_u64_("[VFS ] mount_start=", m.start, false);
    debug_u64_("[VFS ] mount_sectors=", m.sectors, false);
    if (mount_out) *mount_out = slot;
    return 0;
}
extern "C" int koronos_vfs_mount_state(void) {
    uint32_t count = 0;
    for (uint32_t i = 0; i < KORONOS_VFS_MOUNT_MAX; ++i) if (mounts_[i].in_use) ++count;
    return static_cast<int>(count);
}
extern "C" int koronos_vfs_superblock(int mount, koronosfs_superblock_t *out) {
    if (!mount_valid_(mount) || !out) return -1;
    *out = mounts_[mount].sb;
    return 0;
}
extern "C" int koronos_vfs_inode(int mount, uint32_t inode, koronosfs_inode_t *out) {
    if (!mount_valid_(mount)) return -1;
    return load_inode_(mounts_[mount], inode, out) ? 0 : -1;
}
extern "C" int koronos_vfs_sync(int mount) {
    if (!mount_valid_(mount)) return -1;
    Mount &m = mounts_[mount];
    flush_bitmap_(m);
    koronosfs_superblock_t sb = m.sb;
    superblock_checksum_(&sb);
    if (!write_fs_sector_(m, KORONOSFS_V2_SUPERBLOCK_SECTOR,
                          reinterpret_cast<const uint8_t *>(&sb))) return -1;
    return 0;
}
extern "C" int koronos_vfs_unmount(int mount) {
    if (!mount_valid_(mount)) return -1;
    Mount &m = mounts_[mount];
    for (uint32_t i = 0; i < m.sb.inode_count && i < KORONOSFS_V2_INODE_COUNT; ++i) {
        if (m.inode_valid[i]) flush_inode_(m, i + 1u);
    }
    flush_bitmap_(m);
    m.sb.state = KORONOSFS_STATE_CLEAN;
    ++m.sb.generation;
    superblock_checksum_(&m.sb);
    if (!write_fs_sector_(m, KORONOSFS_V2_SUPERBLOCK_SECTOR,
                          reinterpret_cast<const uint8_t *>(&m.sb))) return -1;
    m.in_use = false;
    debug_u64_("[VFS ] unmount_state=", 0, false);
    return 0;
}

extern "C" int koronos_vfs_lookup(int mount, const char *name, uint32_t *inode_out) {
    if (!mount_valid_(mount) || !name || !inode_out) return -1;
    Mount &m = mounts_[mount];
    const uint32_t slot = dirent_slot_(m, m.sb.root_inode, name, false);
    if (slot == 0xFFFFFFFFu) return -1;
    koronosfs_dirent_t entry;
    if (!dirent_at_(m, m.sb.root_inode, slot, &entry)) return -1;
    if (!m.inode_valid[entry.inode - 1]) return -1;
    *inode_out = entry.inode;
    return 0;
}
extern "C" int koronos_vfs_create(int mount, const char *name, uint32_t type, uint32_t *inode_out) {
    if (!mount_valid_(mount) || !name || !*name || text_length_(name) >= KORONOSFS_V2_NAME_MAX) return -1;
    Mount &m = mounts_[mount];
    if (dirent_slot_(m, m.sb.root_inode, name, false) != 0xFFFFFFFFu) return -1;
    uint32_t number = 0;
    for (uint32_t i = 2; i < m.sb.inode_count && i < KORONOSFS_V2_INODE_COUNT; ++i) {
        if (!m.inode_valid[i]) { number = i + 1u; break; }
    }
    if (!number) return -1;
    koronosfs_inode_t inode;
    set_bytes_(reinterpret_cast<uint8_t *>(&inode), 0, sizeof(inode));
    inode.type = static_cast<uint8_t>(type);
    inode.flags = 1u;
    inode.generation = ++m.sb.generation;
    inode_checksum_(&inode);
    m.inodes[number - 1] = inode;
    if (!flush_inode_(m, number) || !dirent_store_(m, m.sb.root_inode,
        dirent_slot_(m, m.sb.root_inode, name, true), number, name, static_cast<uint8_t>(type))) return -1;
    if (inode_out) *inode_out = number;
    return 0;
}
extern "C" int koronos_vfs_unlink(int mount, const char *name) {
    if (!mount_valid_(mount) || !name) return -1;
    Mount &m = mounts_[mount];
    const uint32_t slot = dirent_slot_(m, m.sb.root_inode, name, false);
    if (slot == 0xFFFFFFFFu) return -1;
    koronosfs_dirent_t entry;
    if (!dirent_at_(m, m.sb.root_inode, slot, &entry)) return -1;
    uint8_t zero_entry[sizeof(koronosfs_dirent_t)];
    set_bytes_(zero_entry, 0, sizeof(zero_entry));
    koronosfs_inode_t dir;
    if (!load_inode_(m, m.sb.root_inode, &dir)) return -1;
    const uint32_t pointer = pointer_for_block_(m, &dir, slot / 8u, false);
    if (!pointer) return -1;
    uint8_t block[SECTOR];
    if (!read_table_sector_(m, pointer, block)) return -1;
    for (uint32_t i = 0; i < sizeof(zero_entry); ++i)
        block[(slot % 8u) * sizeof(koronosfs_dirent_t) + i] = zero_entry[i];
    if (!write_table_sector_(m, pointer, block)) return -1;
    m.inode_valid[entry.inode - 1] = false;
    return 0;
}
extern "C" int koronos_vfs_truncate(int mount, uint32_t inode) {
    if (!mount_valid_(mount)) return -1;
    Mount &m = mounts_[mount];
    koronosfs_inode_t in;
    if (!load_inode_(m, inode, &in)) return -1;
    for (uint32_t b = 0; b < 8; ++b) {
        if (in.direct[b]) free_block_(m, in.direct[b]);
        in.direct[b] = 0;
    }
    uint8_t table[SECTOR];
    if (in.indirect) {
        if (read_table_sector_(m, in.indirect, table)) {
            for (uint32_t i = 0; i < 128; ++i) if (table[i * 4u] || table[i * 4u + 1u] ||
                table[i * 4u + 2u] || table[i * 4u + 3u]) free_block_(m, load32_(table + i * 4u));
        }
        free_block_(m, in.indirect);
        in.indirect = 0;
    }
    if (in.double_indirect) {
        uint8_t outer[SECTOR];
        if (read_table_sector_(m, in.double_indirect, outer)) {
            for (uint32_t i = 0; i < 128; ++i) {
                const uint32_t inner = load32_(outer + i * 4u);
                if (!inner) continue;
                if (read_table_sector_(m, inner, table)) {
                    for (uint32_t j = 0; j < 128; ++j) {
                        const uint32_t ptr = load32_(table + j * 4u);
                        if (ptr) free_block_(m, ptr);
                    }
                }
                free_block_(m, inner);
            }
        }
        free_block_(m, in.double_indirect);
        in.double_indirect = 0;
    }
    in.size = 0;
    in.blocks = 0;
    m.inodes[inode - 1] = in;
    return flush_inode_(m, inode) ? 0 : -1;
}
extern "C" int koronos_vfs_open(int mount, const char *name, koronos_vfs_file_t *file) {
    if (!mount_valid_(mount) || !name || !file) return -1;
    uint32_t inode = 0;
    if (koronos_vfs_lookup(mount, name, &inode) != 0) return -1;
    koronosfs_inode_t in;
    if (!load_inode_(mounts_[mount], inode, &in) || in.type != KORONOSFS_TYPE_FILE) return -1;
    set_bytes_(reinterpret_cast<uint8_t *>(file), 0, sizeof(*file));
    file->magic = KORONOS_VFS_FILE_MAGIC;
    file->mount = mount;
    file->inode = inode;
    file->token = mounts_[mount].token ^ (static_cast<uint64_t>(inode) << 32);
    return 0;
}
extern "C" int koronos_vfs_close(koronos_vfs_file_t *file) {
    if (!file || file->magic != KORONOS_VFS_FILE_MAGIC) return -1;
    const int rc = mount_valid_(file->mount) &&
                   flush_inode_(mounts_[file->mount], file->inode) ? 0 : -1;
    file->magic = 0;
    return rc;
}
extern "C" int koronos_vfs_read(koronos_vfs_file_t *file, uint8_t *buffer, uint32_t length, uint32_t *actual) {
    if (!file || file->magic != KORONOS_VFS_FILE_MAGIC || !buffer || !mount_valid_(file->mount)) return -1;
    Mount &m = mounts_[file->mount];
    koronosfs_inode_t in;
    if (!load_inode_(m, file->inode, &in) || in.type != KORONOSFS_TYPE_FILE) return -1;
    uint32_t done = 0;
    uint8_t block[SECTOR];
    while (done < length && file->offset < in.size) {
        const uint32_t block_index = file->offset / SECTOR;
        const uint32_t within = file->offset % SECTOR;
        const uint32_t pointer = pointer_for_block_(m, &in, block_index, false);
        if (!pointer) {
            set_bytes_(block, 0, SECTOR);
        } else if (!read_table_sector_(m, pointer, block)) {
            return -1;
        }
        const uint32_t take = SECTOR - within;
        const uint32_t remaining = in.size - file->offset;
        const uint32_t count = take < remaining ? take : remaining;
        if (count > length - done) {
            const uint32_t copy = length - done;
            for (uint32_t i = 0; i < copy; ++i) buffer[done + i] = block[within + i];
            done = length;
            file->offset += copy;
            break;
        }
        for (uint32_t i = 0; i < count; ++i) buffer[done + i] = block[within + i];
        done += count;
        file->offset += count;
    }
    if (actual) *actual = done;
    if (done) bytes_read_ += done;
    return 0;
}
extern "C" int koronos_vfs_write(koronos_vfs_file_t *file, const uint8_t *buffer, uint32_t length, uint32_t *actual) {
    if (!file || file->magic != KORONOS_VFS_FILE_MAGIC || !buffer || !mount_valid_(file->mount)) return -1;
    Mount &m = mounts_[file->mount];
    koronosfs_inode_t in;
    if (!load_inode_(m, file->inode, &in) || in.type != KORONOSFS_TYPE_FILE) return -1;
    if (file->offset > MAX_FILE_SIZE || length > MAX_FILE_SIZE - file->offset) return -1;
    uint32_t done = 0;
    uint8_t block[SECTOR];
    while (done < length) {
        const uint32_t block_index = file->offset / SECTOR;
        const uint32_t within = file->offset % SECTOR;
        const uint32_t pointer = pointer_for_block_(m, &in, block_index, true);
        if (!pointer) return -1;
        if (within || (length - done) < SECTOR) {
            if (!read_table_sector_(m, pointer, block)) return -1;
        }
        const uint32_t count = SECTOR - within < length - done ? SECTOR - within : length - done;
        for (uint32_t i = 0; i < count; ++i) block[within + i] = buffer[done + i];
        if (!write_table_sector_(m, pointer, block)) return -1;
        done += count;
        file->offset += count;
    }
    if (file->offset > in.size) in.size = file->offset;
    m.inodes[file->inode - 1] = in;
    if (!flush_inode_(m, file->inode)) return -1;
    bytes_written_ += done;
    if (actual) *actual = done;
    return 0;
}
extern "C" uint64_t koronos_vfs_file_digest(int mount, const char *name) {
    if (!mount_valid_(mount) || !name) return 0;
    koronos_vfs_file_t file;
    if (koronos_vfs_open(mount, name, &file) != 0) return 0;
    uint8_t buffer[SECTOR];
    uint64_t digest = 14695981039346656037ull;
    for (;;) {
        uint32_t actual = 0;
        if (koronos_vfs_read(&file, buffer, sizeof(buffer), &actual) != 0) { digest = 0; break; }
        for (uint32_t i = 0; i < actual; ++i) {
            digest ^= buffer[i];
            digest *= 1099511628211ull;
        }
        if (actual < sizeof(buffer)) break;
    }
    koronos_vfs_close(&file);
    return digest;
}
extern "C" int koronos_vfs_verify(int mount) {
    if (!mount_valid_(mount)) return -1;
    Mount &m = mounts_[mount];
    if (!superblock_valid_(&m.sb)) return -1;
    for (uint32_t i = 0; i < m.sb.inode_count && i < KORONOSFS_V2_INODE_COUNT; ++i) {
        if (!m.inode_valid[i]) continue;
        const koronosfs_inode_t &in = m.inodes[i];
        if (!inode_checksum_valid_(&in)) return -1;
        for (uint32_t b = 0; b < 8; ++b) if (in.direct[b] >= m.sb.data_sectors) return -1;
        if (in.indirect >= m.sb.data_sectors || in.double_indirect >= m.sb.data_sectors) return -1;
        if (in.size > MAX_FILE_SIZE) return -1;
    }
    uint8_t block[SECTOR];
    const uint32_t root_pointer = m.inodes[m.sb.root_inode - 1].direct[0];
    if (!root_pointer || !read_table_sector_(m, root_pointer, block)) return -1;
    for (uint32_t i = 0; i < 8; ++i) {
        const koronosfs_dirent_t &entry =
            *reinterpret_cast<const koronosfs_dirent_t *>(block + i * sizeof(koronosfs_dirent_t));
        if (!entry.name[0]) continue;
        if (!entry.inode || entry.inode > m.sb.inode_count || !m.inode_valid[entry.inode - 1]) return -1;
    }
    debug_u64_("[VFS ] fsck_inodes=", m.sb.inode_count, false);
    return 0;
}
extern "C" int koronos_vfs_format_disk(const uint8_t root_type_guid[16],
                                       const uint8_t journal_type_guid[16],
                                       koronos_partition_t *root_out,
                                       koronos_partition_t *journal_out) {
    if (!root_type_guid || !journal_type_guid) return -1;
    if (koronos_block_init() != 0) return -1;
    const uint64_t total = koronos_block_sector_count();
    if (total < 4096u) return -1;
    uint64_t root_start = 2048u;
    uint64_t journal_start = (total / 2u + 2047u) / 2048u * 2048u;
    if (journal_start <= root_start + 64u || journal_start + 32u > total - 34u) {
        root_start = 34u;
        journal_start = root_start + 512u;
    }
    const uint64_t root_sectors = journal_start - root_start;
    const uint64_t journal_sectors = total - 34u - journal_start;
    if (journal_sectors < 32u) return -1;
    if (koronos_block_format_gpt(root_start, root_sectors, journal_start, journal_sectors,
                                 root_type_guid, journal_type_guid) != 0) return -1;

    koronos_partition_t root_partition;
    koronos_partition_t journal_partition;
    if (koronos_block_find_partition(root_type_guid, &root_partition) != 0 ||
        koronos_block_find_partition(journal_type_guid, &journal_partition) != 0) return -1;
    if (koronos_vfs_format(root_partition.index) != 0) return -1;
    if (root_out) *root_out = root_partition;
    if (journal_out) *journal_out = journal_partition;
    debug_u64_("[VFS ] disk_format_root_start=", root_partition.start_lba, false);
    debug_u64_("[VFS ] disk_format_root_sectors=", root_partition.sector_count, false);
    return 0;
}
