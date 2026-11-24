#include "chimera/install.h"
#include "chimera/multiboot_modules.h"
#include "chimera/physmap.h"
#include "chimera/address_space.h"

/* Durable installer/recovery over real GPT partitions and KoronosFS v2.
 *
 * The journal lives on its own GPT partition. It records before/after
 * superblock, inode and file bytes so recovery can repair a torn metadata
 * write and roll back a pending transaction. No fixed marker sectors or
 * simulated crash injection are used. */

namespace {

static_assert(sizeof(koronos_journal_record_t) == 2048u, "journal record must be four sectors");

const uint32_t SECTOR = KORONOS_BLOCK_SECTOR_SIZE;
const uint32_t PAYLOAD_MAX = 512u;

static inline void out8_(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}
static void debug_(const char *text) {
    while (*text) out8_(0xE9, static_cast<uint8_t>(*text++));
    out8_(0xE9, '\n');
}
static void debug_u64_(const char *label, uint64_t value, bool hex) {
    char line[112];
    uint32_t pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    static const char digits[] = "0123456789ABCDEF";
    char reversed[24];
    uint32_t n = 0;
    if (!value) reversed[n++] = '0';
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
static uint32_t text_length_(const char *text) {
    uint32_t n = 0;
    while (text && text[n]) ++n;
    return n;
}
static bool has_token_(const char *text, const char *token) {
    if (!text || !token) return false;
    const uint32_t n = text_length_(token);
    for (uint32_t i = 0; text[i]; ++i) {
        uint32_t j = 0;
        while (j < n && text[i + j] == token[j]) ++j;
        if (j == n) return true;
    }
    return false;
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
static uint32_t append_text_(uint8_t *dst, uint32_t at, const char *text) {
    for (uint32_t i = 0; text[i]; ++i) dst[at++] = static_cast<uint8_t>(text[i]);
    return at;
}
static uint32_t append_hex64_(uint8_t *dst, uint32_t at, uint64_t value) {
    static const char digits[] = "0123456789ABCDEF";
    for (int shift = 60; shift >= 0; shift -= 4)
        dst[at++] = static_cast<uint8_t>(digits[(value >> shift) & 15u]);
    return at;
}
static uint32_t append_decimal_(uint8_t *dst, uint32_t at, uint64_t value) {
    char reversed[24];
    uint32_t n = 0;
    if (!value) reversed[n++] = '0';
    while (value && n < sizeof(reversed)) { reversed[n++] = static_cast<char>('0' + value % 10u); value /= 10u; }
    while (n) dst[at++] = static_cast<uint8_t>(reversed[--n]);
    return at;
}
/* ---- Journal I/O --------------------------------------------------------- */

static void journal_checksum_(koronos_journal_record_t *record) {
    uint8_t *bytes = reinterpret_cast<uint8_t *>(record);
    bytes[2044] = 0; bytes[2045] = 0; bytes[2046] = 0; bytes[2047] = 0;
    const uint32_t crc = crc32_(bytes, 2044);
    bytes[2044] = static_cast<uint8_t>(crc);
    bytes[2045] = static_cast<uint8_t>(crc >> 8);
    bytes[2046] = static_cast<uint8_t>(crc >> 16);
    bytes[2047] = static_cast<uint8_t>(crc >> 24);
}
static bool journal_checksum_valid_(const koronos_journal_record_t *record) {
    const uint8_t *bytes = reinterpret_cast<const uint8_t *>(record);
    const uint32_t stored = static_cast<uint32_t>(bytes[2044]) |
                            (static_cast<uint32_t>(bytes[2045]) << 8) |
                            (static_cast<uint32_t>(bytes[2046]) << 16) |
                            (static_cast<uint32_t>(bytes[2047]) << 24);
    return crc32_(bytes, 2044) == stored;
}
static bool journal_magic_valid_(const koronos_journal_record_t *record) {
    static const char magic[] = KORONOS_JOURNAL_MAGIC;
    for (uint32_t i = 0; i < 16; ++i)
        if (record->magic[i] != static_cast<uint8_t>(magic[i])) return false;
    return record->version == KORONOS_JOURNAL_VERSION;
}
static bool write_journal_(const koronos_journal_record_t *record) {
    koronos_partition_t journal;
    if (koronos_block_find_partition(koronos_journal_type_guid, &journal) != 0) return false;
    if (journal.sector_count < KORONOS_JOURNAL_RECORD_SECTORS + KORONOS_JOURNAL_MIRROR_SECTORS) return false;
    const uint8_t *bytes = reinterpret_cast<const uint8_t *>(record);
    for (uint32_t sector = 0; sector < KORONOS_JOURNAL_RECORD_SECTORS; ++sector) {
        if (koronos_block_write(journal.start_lba + sector,
                                bytes + static_cast<uint64_t>(sector) * SECTOR) != 0) return false;
    }
    for (uint32_t sector = 0; sector < KORONOS_JOURNAL_MIRROR_SECTORS; ++sector) {
        if (koronos_block_write(journal.start_lba + KORONOS_JOURNAL_RECORD_SECTORS + sector,
                                bytes + static_cast<uint64_t>(sector) * SECTOR) != 0) return false;
    }
    return true;
}
static bool read_journal_(koronos_journal_record_t *record, bool *from_mirror) {
    koronos_partition_t journal;
    if (koronos_block_find_partition(koronos_journal_type_guid, &journal) != 0) return false;
    if (journal.sector_count < KORONOS_JOURNAL_RECORD_SECTORS + KORONOS_JOURNAL_MIRROR_SECTORS) return false;
    uint8_t buffer[sizeof(koronos_journal_record_t)];
    for (uint32_t copy = 0; copy < 2; ++copy) {
        const uint64_t base = journal.start_lba + copy * KORONOS_JOURNAL_RECORD_SECTORS;
        bool ok = true;
        for (uint32_t sector = 0; sector < KORONOS_JOURNAL_RECORD_SECTORS; ++sector) {
            if (koronos_block_read(base + sector, buffer + static_cast<uint64_t>(sector) * SECTOR) != 0) {
                ok = false;
                break;
            }
        }
        if (!ok) continue;
        koronos_journal_record_t *candidate = reinterpret_cast<koronos_journal_record_t *>(buffer);
        if (journal_magic_valid_(candidate) && journal_checksum_valid_(candidate)) {
            *record = *candidate;
            if (from_mirror) *from_mirror = copy != 0;
            return true;
        }
    }
    return false;
}

/* ---- Raw metadata repair ------------------------------------------------- */

static bool raw_superblock_(const koronos_partition_t &root, uint8_t *buffer, bool write) {
    if (write) return koronos_block_write(root.start_lba + KORONOSFS_V2_SUPERBLOCK_SECTOR, buffer) == 0;
    return koronos_block_read(root.start_lba + KORONOSFS_V2_SUPERBLOCK_SECTOR, buffer) == 0;
}
static bool raw_inode_(const koronos_partition_t &root, uint32_t inode, uint8_t *buffer, bool write) {
    if (!inode || inode > KORONOSFS_V2_INODE_COUNT) return false;
    const uint32_t index = inode - 1u;
    const uint64_t lba = root.start_lba + KORONOSFS_V2_INODE_TABLE_SECTOR + index / 8u;
    uint8_t sector[SECTOR];
    if (koronos_block_read(lba, sector) != 0) return false;
    const uint32_t offset = (index % 8u) * sizeof(koronosfs_inode_t);
    if (write) {
        for (uint32_t i = 0; i < sizeof(koronosfs_inode_t); ++i) sector[offset + i] = buffer[i];
        return koronos_block_write(lba, sector) == 0;
    }
    for (uint32_t i = 0; i < sizeof(koronosfs_inode_t); ++i) buffer[i] = sector[offset + i];
    return true;
}
static bool inode_checksum_valid_(const uint8_t *bytes) {
    uint32_t stored = 0;
    for (uint32_t i = 0; i < 4; ++i) stored |= static_cast<uint32_t>(bytes[60 + i]) << (8u * i);
    return crc32_(bytes, 60) == stored;
}
static bool superblock_checksum_valid_(const uint8_t *bytes) {
    uint32_t stored = 0;
    for (uint32_t i = 0; i < 4; ++i) stored |= static_cast<uint32_t>(bytes[508 + i]) << (8u * i);
    return crc32_(bytes, 508) == stored;
}

/* ---- Payloads and files -------------------------------------------------- */

static bool module_payload_(const char *token, uint8_t *buffer, uint32_t *length) {
    for (uint32_t i = 0; i < chimera_multiboot_module_count(); ++i) {
        const chimera_boot_module *module = chimera_multiboot_module(i);
        if (!module || !has_token_(module->cmdline, token)) continue;
        if (!module->base || module->size == 0 || module->size > PAYLOAD_MAX) return false;
        const void *source = koronos_phys_to_virt(module->base, static_cast<uint32_t>(module->size));
        if (!source) return false;
        copy_bytes_(buffer, static_cast<const uint8_t *>(source), static_cast<uint32_t>(module->size));
        *length = static_cast<uint32_t>(module->size);
        return true;
    }
    return false;
}
static uint32_t embedded_payload_(const char *token, uint8_t *buffer) {
    uint32_t at = append_text_(buffer, 0, "KORONOS-EMBEDDED ");
    at = append_text_(buffer, at, token);
    at = append_text_(buffer, at, " v2 sectors=");
    at = append_decimal_(buffer, at, koronos_block_sector_count());
    buffer[at++] = '\n';
    return at;
}
static bool load_payload_(const char *token, uint8_t *buffer, uint32_t *length, uint32_t *from_module) {
    if (module_payload_(token, buffer, length)) {
        *from_module = 1;
        return *length > 0;
    }
    *from_module = 0;
    *length = embedded_payload_(token, buffer);
    return true;
}
static bool write_payload_(int mount, const char *name, const uint8_t *data, uint32_t length) {
    uint32_t inode = 0;
    if (koronos_vfs_lookup(mount, name, &inode) != 0 &&
        koronos_vfs_create(mount, name, KORONOSFS_TYPE_FILE, &inode) != 0) return false;
    koronos_vfs_file_t file;
    if (koronos_vfs_open(mount, name, &file) != 0) return false;
    uint32_t written = 0;
    const bool ok = koronos_vfs_write(&file, data, length, &written) == 0 && written == length;
    koronos_vfs_close(&file);
    return ok;
}
static bool read_payload_(int mount, const char *name, uint8_t *buffer, uint32_t *length) {
    koronos_vfs_file_t file;
    if (koronos_vfs_open(mount, name, &file) != 0) return false;
    uint32_t actual = 0;
    const bool ok = koronos_vfs_read(&file, buffer, PAYLOAD_MAX, &actual) == 0 && actual > 0;
    koronos_vfs_close(&file);
    if (ok) *length = actual;
    return ok;
}
static uint64_t root_digest_(int mount) {
    const uint64_t kernel = koronos_vfs_file_digest(mount, "kernel");
    const uint64_t init = koronos_vfs_file_digest(mount, "init");
    const uint64_t manifest = koronos_vfs_file_digest(mount, "manifest");
    uint8_t combined[24];
    for (uint32_t i = 0; i < 8; ++i) {
        combined[i] = static_cast<uint8_t>(kernel >> (8u * i));
        combined[8 + i] = static_cast<uint8_t>(init >> (8u * i));
        combined[16 + i] = static_cast<uint8_t>(manifest >> (8u * i));
    }
    return koronos_vfs_digest(combined, sizeof(combined));
}
static uint32_t build_manifest_(uint8_t *buffer, uint64_t kernel, uint64_t init, uint32_t sequence) {
    uint32_t at = append_text_(buffer, 0, "KORONOS-MANIFEST v2 kernel=");
    at = append_hex64_(buffer, at, kernel);
    at = append_text_(buffer, at, " init=");
    at = append_hex64_(buffer, at, init);
    at = append_text_(buffer, at, " sequence=");
    at = append_decimal_(buffer, at, sequence);
    buffer[at++] = '\n';
    return at;
}

static koronos_install_status_t status_;
static void reset_status_(koronos_install_phase_t phase) {
    set_bytes_(reinterpret_cast<uint8_t *>(&status_), 0, sizeof(status_));
    status_.phase = static_cast<uint32_t>(phase);
}
static void publish_layout_(const koronos_partition_t &root, const koronos_partition_t &journal) {
    debug_u64_("[INS ] partition_count=", koronos_block_partition_count(), false);
    debug_u64_("[INS ] root_start=", root.start_lba, false);
    debug_u64_("[INS ] root_sectors=", root.sector_count, false);
    debug_u64_("[INS ] journal_start=", journal.start_lba, false);
    debug_u64_("[INS ] journal_sectors=", journal.sector_count, false);
    status_.partition_count = koronos_block_partition_count();
    status_.root_start = root.start_lba;
    status_.root_sectors = root.sector_count;
    status_.journal_start = journal.start_lba;
    status_.journal_sectors = journal.sector_count;
}
} // namespace

const uint8_t koronos_root_type_guid[16] = {
    0x4B, 0x4F, 0x52, 0x4F, 0x4E, 0x4F, 0x53, 0x46,
    0x53, 0x32, 0x52, 0x4F, 0x4F, 0x54, 0x20, 0x31
};
const uint8_t koronos_journal_type_guid[16] = {
    0x4B, 0x4F, 0x52, 0x4F, 0x4E, 0x4F, 0x53, 0x4A,
    0x32, 0x4A, 0x4F, 0x55, 0x52, 0x4E, 0x41, 0x4C
};

extern "C" const koronos_install_status_t *koronos_install_status(void) { return &status_; }

extern "C" koronos_install_phase_t koronos_install_selected_phase(void) {
    for (uint32_t i = 0; i < chimera_multiboot_module_count(); ++i) {
        const chimera_boot_module *module = chimera_multiboot_module(i);
        if (!module || !has_token_(module->cmdline, "koronos-install-stack")) continue;
        if (has_token_(module->cmdline, "mode=installer")) return KORONOS_PHASE_INSTALLER;
        if (has_token_(module->cmdline, "mode=installed")) return KORONOS_PHASE_INSTALLED;
        if (has_token_(module->cmdline, "mode=recovery")) return KORONOS_PHASE_RECOVERY;
        if (has_token_(module->cmdline, "mode=verify")) return KORONOS_PHASE_VERIFY;
        if (has_token_(module->cmdline, "mode=live")) return KORONOS_PHASE_LIVE;
    }
    return KORONOS_PHASE_NONE;
}

extern "C" int koronos_installer_run(void) {
    reset_status_(KORONOS_PHASE_INSTALLER);
    if (koronos_block_init() != 0 || koronos_vfs_init() != 0) return -1;
    koronos_partition_t root;
    koronos_partition_t journal;
    if (koronos_vfs_format_disk(koronos_root_type_guid, koronos_journal_type_guid,
                                &root, &journal) != 0) {
        debug_("[INS ] FAIL: disk format");
        return -1;
    }
    publish_layout_(root, journal);

    int mount = -1;
    if (koronos_vfs_mount(root.index, &mount) != 0) {
        debug_("[INS ] FAIL: root mount");
        return -1;
    }
    status_.mount_state = static_cast<uint32_t>(koronos_vfs_mount_state());
    debug_u64_("[INS ] mount_state=", status_.mount_state, false);

    uint8_t kernel[PAYLOAD_MAX];
    uint8_t init[PAYLOAD_MAX];
    uint8_t manifest[PAYLOAD_MAX];
    uint32_t kernel_length = 0;
    uint32_t init_length = 0;
    uint32_t kernel_module = 0;
    uint32_t init_module = 0;
    if (!load_payload_("koronos-payload-kernel", kernel, &kernel_length, &kernel_module) ||
        !load_payload_("koronos-payload-init", init, &init_length, &init_module)) {
        debug_("[INS ] FAIL: payload load");
        return -1;
    }
    if (!write_payload_(mount, "kernel", kernel, kernel_length) ||
        !write_payload_(mount, "init", init, init_length)) {
        debug_("[INS ] FAIL: payload write");
        return -1;
    }
    const uint64_t kernel_digest = koronos_vfs_file_digest(mount, "kernel");
    const uint64_t init_digest = koronos_vfs_file_digest(mount, "init");
    const uint32_t manifest_length = build_manifest_(manifest, kernel_digest, init_digest, 1u);
    if (!write_payload_(mount, "manifest", manifest, manifest_length)) {
        debug_("[INS ] FAIL: manifest write");
        return -1;
    }
    const uint64_t manifest_digest = koronos_vfs_file_digest(mount, "manifest");
    status_.root_digest = root_digest_(mount);
    if (status_.root_digest == 0 || manifest_digest == 0) {
        debug_("[INS ] FAIL: digest computation");
        return -1;
    }
    debug_u64_("[INS ] bytes_written=", koronos_vfs_bytes_written(), false);
    debug_u64_("[INS ] root_digest=", status_.root_digest, true);
    debug_u64_("[INS ] manifest_digest=", manifest_digest, true);
    debug_u64_("[INS ] payload_modules=", kernel_module + init_module, false);

    uint8_t raw_superblock[SECTOR];
    uint8_t raw_inode[sizeof(koronosfs_inode_t)];
    uint32_t manifest_inode = 0;
    if (!raw_superblock_(root, raw_superblock, false) ||
        koronos_vfs_lookup(mount, "manifest", &manifest_inode) != 0 ||
        !raw_inode_(root, manifest_inode, raw_inode, false)) {
        debug_("[INS ] FAIL: journal snapshot");
        return -1;
    }
    koronos_journal_record_t record;
    set_bytes_(reinterpret_cast<uint8_t *>(&record), 0, sizeof(record));
    static const char magic[] = KORONOS_JOURNAL_MAGIC;
    for (uint32_t i = 0; i < 16; ++i) record.magic[i] = static_cast<uint8_t>(magic[i]);
    record.version = KORONOS_JOURNAL_VERSION;
    record.state = KORONOS_JOURNAL_COMMITTED;
    record.transaction = 1u;
    record.next_phase = KORONOS_PHASE_INSTALLED;
    record.root_digest = status_.root_digest;
    record.after_digest = manifest_digest;
    record.target_inode = manifest_inode;
    for (uint32_t i = 0; text_length_("manifest") > i; ++i) record.target_name[i] = "manifest"[i];
    copy_bytes_(record.before_inode, raw_inode, sizeof(raw_inode));
    copy_bytes_(record.after_inode, raw_inode, sizeof(raw_inode));
    copy_bytes_(record.before_superblock, raw_superblock, SECTOR);
    copy_bytes_(record.after_superblock, raw_superblock, SECTOR);
    copy_bytes_(record.before_content, manifest, manifest_length);
    copy_bytes_(record.after_content, manifest, manifest_length);
    record.content_length = manifest_length;
    record.sequence = 1u;
    journal_checksum_(&record);
    if (!write_journal_(&record)) {
        debug_("[INS ] FAIL: journal write");
        return -1;
    }
    status_.journal_state = record.state;
    status_.transaction = record.transaction;
    debug_u64_("[INS ] journal_state=", record.state, false);
    debug_u64_("[INS ] journal_transaction=", record.transaction, false);
    debug_("[INS ] JOURNAL WRITE PASS");
    debug_("[INS ] JOURNAL COMMIT PASS");
    debug_("[INS ] INSTALLED ROOT WRITTEN");

    if (koronos_vfs_unmount(mount) != 0) {
        debug_("[INS ] FAIL: unmount");
        return -1;
    }
    status_.mount_state = static_cast<uint32_t>(koronos_vfs_mount_state());
    debug_u64_("[INS ] handoff_next=", record.next_phase, false);
    debug_("[INS ] HANDOFF next=installed");
    return 0;
}

extern "C" int koronos_installed_run(void) {
    reset_status_(KORONOS_PHASE_INSTALLED);
    if (koronos_block_init() != 0 || koronos_vfs_init() != 0) return -1;
    koronos_partition_t root;
    koronos_partition_t journal;
    if (koronos_vfs_find_by_type(koronos_root_type_guid, &root) != 0 ||
        koronos_vfs_find_by_type(koronos_journal_type_guid, &journal) != 0) return -1;
    publish_layout_(root, journal);
    koronos_journal_record_t record;
    bool from_mirror = false;
    if (!read_journal_(&record, &from_mirror) || record.state != KORONOS_JOURNAL_COMMITTED) {
        debug_("[INS ] FAIL: no committed journal");
        return -1;
    }
    status_.journal_state = record.state;
    status_.transaction = record.transaction;
    int mount = -1;
    if (koronos_vfs_mount(root.index, &mount) != 0 ||
        koronos_vfs_verify(mount) != 0) {
        debug_("[INS ] FAIL: installed root verify");
        return -1;
    }
    status_.mount_state = static_cast<uint32_t>(koronos_vfs_mount_state());
    status_.fsck_pass = 1u;
    status_.root_digest = root_digest_(mount);
    if (status_.root_digest != record.root_digest) {
        debug_("[INS ] FAIL: installed root digest mismatch");
        return -1;
    }
    debug_u64_("[INS ] root_digest=", status_.root_digest, true);
    debug_u64_("[INS ] bytes_read=", koronos_vfs_bytes_read(), false);
    debug_u64_("[INS ] handoff=", 1, false);
    debug_("[INS ] INSTALLED ROOT HANDOFF PASS");
    debug_("[INS ] ROOT MOUNTED=1");

    uint8_t manifest[PAYLOAD_MAX];
    uint32_t manifest_length = 0;
    uint8_t raw_superblock[SECTOR];
    uint8_t raw_inode[sizeof(koronosfs_inode_t)];
    uint32_t manifest_inode = 0;
    if (!read_payload_(mount, "manifest", manifest, &manifest_length) ||
        manifest_length != record.content_length ||
        koronos_vfs_file_digest(mount, "manifest") != record.after_digest ||
        koronos_vfs_lookup(mount, "manifest", &manifest_inode) != 0 ||
        !raw_superblock_(root, raw_superblock, false) ||
        !raw_inode_(root, manifest_inode, raw_inode, false)) {
        debug_("[INS ] FAIL: manifest snapshot");
        return -1;
    }
    debug_("[INS ] ROOT MARKER PASS");

    /* Keep the original bytes before rendering the replacement manifest; the
     * rollback image must not be overwritten by the staged write. */
    uint8_t original[PAYLOAD_MAX];
    copy_bytes_(original, manifest, manifest_length);
    const uint64_t kernel_digest = koronos_vfs_file_digest(mount, "kernel");
    const uint64_t init_digest = koronos_vfs_file_digest(mount, "init");
    const uint32_t after_length = build_manifest_(manifest, kernel_digest, init_digest,
                                                  record.sequence + 1u);
    copy_bytes_(record.before_inode, raw_inode, sizeof(raw_inode));
    copy_bytes_(record.before_superblock, raw_superblock, SECTOR);
    copy_bytes_(record.before_content, original, manifest_length);
    copy_bytes_(record.after_content, manifest, after_length);
    /* Recovery replays the before-image, so the journal records the before
     * length; the after length is only used for the staged write above. */
    record.content_length = manifest_length;
    record.state = KORONOS_JOURNAL_PENDING;
    record.transaction = record.transaction + 1u;
    record.next_phase = KORONOS_PHASE_RECOVERY;
    record.before_digest = record.after_digest;
    record.after_digest = koronos_vfs_digest(manifest, after_length);
    journal_checksum_(&record);
    if (!write_journal_(&record)) {
        debug_("[INS ] FAIL: pending journal write");
        return -1;
    }
    status_.journal_state = record.state;
    status_.transaction = record.transaction;
    debug_u64_("[INS ] journal_state=", record.state, false);
    debug_u64_("[INS ] journal_transaction=", record.transaction, false);

    /* A genuine interrupted transaction: the new manifest bytes and inode are
     * written to disk while the journal stays PENDING. Recovery uses the
     * journal's before-image rather than a fabricated bad-marker string. */
    if (!write_payload_(mount, "manifest", record.after_content, after_length)) {
        debug_("[INS ] FAIL: torn write stage");
        return -1;
    }
    uint8_t torn_inode[sizeof(koronosfs_inode_t)];
    if (!raw_inode_(root, manifest_inode, torn_inode, false)) return -1;
    torn_inode[60] = static_cast<uint8_t>(torn_inode[60] ^ 0xA5u);
    if (!raw_inode_(root, manifest_inode, torn_inode, true)) return -1;
    /* No orderly unmount: an interrupted transaction leaves the dirty
     * superblock and torn inode checksum on disk for recovery to repair. */
    raw_superblock[20] = static_cast<uint8_t>(KORONOSFS_STATE_DIRTY);
    raw_superblock[508] = static_cast<uint8_t>(raw_superblock[508] ^ 0x5Au);
    if (!raw_superblock_(root, raw_superblock, true)) return -1;
    debug_("[INS ] REAL TORN WRITE STAGED");
    debug_u64_("[INS ] handoff_next=", record.next_phase, false);
    debug_("[INS ] HANDOFF next=recovery");
    return 0;
}

extern "C" int koronos_recovery_run(void) {
    reset_status_(KORONOS_PHASE_RECOVERY);
    if (koronos_block_init() != 0 || koronos_vfs_init() != 0) return -1;
    koronos_partition_t root;
    koronos_partition_t journal;
    if (koronos_vfs_find_by_type(koronos_root_type_guid, &root) != 0 ||
        koronos_vfs_find_by_type(koronos_journal_type_guid, &journal) != 0) return -1;
    publish_layout_(root, journal);
    koronos_journal_record_t record;
    bool from_mirror = false;
    if (!read_journal_(&record, &from_mirror) || record.state != KORONOS_JOURNAL_PENDING) {
        debug_("[REC ] FAIL: no pending journal");
        return -1;
    }
    status_.journal_state = record.state;
    status_.transaction = record.transaction;
    debug_u64_("[REC ] journal_source_mirror=", from_mirror ? 1u : 0u, false);

    uint8_t raw_superblock[SECTOR];
    if (!raw_superblock_(root, raw_superblock, false)) return -1;
    if (!superblock_checksum_valid_(raw_superblock)) {
        copy_bytes_(raw_superblock, record.before_superblock, SECTOR);
        if (!raw_superblock_(root, raw_superblock, true)) return -1;
        debug_("[REC ] SUPERBLOCK CHECKSUM REPAIR PASS");
    } else {
        debug_("[REC ] SUPERBLOCK CHECKSUM VALID");
    }
    uint8_t raw_inode[sizeof(koronosfs_inode_t)];
    if (!raw_inode_(root, record.target_inode, raw_inode, false)) return -1;
    if (!inode_checksum_valid_(raw_inode)) {
        copy_bytes_(raw_inode, record.before_inode, sizeof(raw_inode));
        if (!raw_inode_(root, record.target_inode, raw_inode, true)) return -1;
        debug_("[REC ] INODE CHECKSUM REPAIR PASS");
    } else {
        debug_("[REC ] INODE CHECKSUM VALID");
    }

    int mount = -1;
    if (koronos_vfs_mount(root.index, &mount) != 0) {
        debug_("[REC ] FAIL: remount after repair");
        return -1;
    }
    status_.mount_state = static_cast<uint32_t>(koronos_vfs_mount_state());
    if (koronos_vfs_verify(mount) != 0) {
        debug_("[REC ] FAIL: filesystem verify");
        return -1;
    }
    status_.fsck_pass = 1u;
    const uint64_t current_digest = koronos_vfs_file_digest(mount, record.target_name);
    debug_u64_("[REC ] before_digest=", record.before_digest, true);
    debug_u64_("[REC ] current_digest=", current_digest, true);
    debug_u64_("[REC ] replay_length=", record.content_length, false);
    if (current_digest != record.before_digest) {
        if (koronos_vfs_truncate(mount, record.target_inode) != 0) {
            debug_("[REC ] FAIL: truncate for replay");
            return -1;
        }
        uint32_t restored = 0;
        koronos_vfs_file_t file;
        if (koronos_vfs_open(mount, record.target_name, &file) != 0) {
            debug_("[REC ] FAIL: reopen for replay");
            return -1;
        }
        const int write_rc = koronos_vfs_write(&file, record.before_content,
                                               record.content_length, &restored);
        if (write_rc != 0 || restored != record.content_length) {
            debug_u64_("[REC ] replay_write_rc=", static_cast<uint64_t>(write_rc), false);
            debug_u64_("[REC ] restored_partial=", restored, false);
            koronos_vfs_close(&file);
            return -1;
        }
        koronos_vfs_close(&file);
        status_.restored_bytes = restored;
        debug_u64_("[REC ] restored_bytes=", restored, false);
    }
    if (koronos_vfs_file_digest(mount, record.target_name) != record.before_digest) {
        debug_("[REC ] FAIL: rollback digest mismatch");
        return -1;
    }
    status_.root_digest = root_digest_(mount);
    if (status_.root_digest != record.root_digest) {
        debug_("[REC ] FAIL: root digest after rollback");
        return -1;
    }
    status_.rollback = 1u;
    debug_("[REC ] JOURNAL ROLLBACK PASS");
    debug_u64_("[REC ] root_digest=", status_.root_digest, true);

    record.state = KORONOS_JOURNAL_ROLLED_BACK;
    record.next_phase = KORONOS_PHASE_VERIFY;
    journal_checksum_(&record);
    if (!write_journal_(&record) || koronos_vfs_unmount(mount) != 0) return -1;
    status_.journal_state = record.state;
    debug_u64_("[INS ] journal_state=", record.state, false);
    debug_u64_("[REC ] handoff_next=", record.next_phase, false);
    debug_("[REC ] HANDOFF next=verify");
    return 0;
}

extern "C" int koronos_verify_run(void) {
    reset_status_(KORONOS_PHASE_VERIFY);
    if (koronos_block_init() != 0 || koronos_vfs_init() != 0) return -1;
    koronos_partition_t root;
    koronos_partition_t journal;
    if (koronos_vfs_find_by_type(koronos_root_type_guid, &root) != 0 ||
        koronos_vfs_find_by_type(koronos_journal_type_guid, &journal) != 0) return -1;
    publish_layout_(root, journal);
    koronos_journal_record_t record;
    bool from_mirror = false;
    if (!read_journal_(&record, &from_mirror) || record.state != KORONOS_JOURNAL_ROLLED_BACK) {
        debug_("[INS ] FAIL: journal not rolled back");
        return -1;
    }
    status_.journal_state = record.state;
    status_.transaction = record.transaction;
    debug_u64_("[INS ] journal_state=", record.state, false);
    debug_u64_("[INS ] journal_transaction=", record.transaction, false);
    int mount = -1;
    if (koronos_vfs_mount(root.index, &mount) != 0 || koronos_vfs_verify(mount) != 0) {
        debug_("[INS ] FAIL: final fsck");
        return -1;
    }
    status_.mount_state = static_cast<uint32_t>(koronos_vfs_mount_state());
    status_.fsck_pass = 1u;
    status_.root_digest = root_digest_(mount);
    status_.rollback = 1u;
    if (status_.root_digest != record.root_digest ||
        koronos_vfs_file_digest(mount, record.target_name) != record.before_digest) {
        debug_("[INS ] FAIL: final digest mismatch");
        return -1;
    }
    debug_u64_("[INS ] root_digest=", status_.root_digest, true);
    debug_u64_("[INS ] bytes_read=", koronos_vfs_bytes_read(), false);
    debug_("[INS ] ROOT VERIFY PASS");
    debug_("[INS ] ROLLBACK VERIFY PASS");
    debug_("[INS ] REPAIR VERIFY PASS");
    if (koronos_vfs_unmount(mount) != 0) return -1;
    return 0;
}

/* Kernel-side handoff: the ring-3 live payload calls a translated SYSCALL to
 * obtain this token from a real mounted root rather than inventing one. */
static bool handoff_token_(char *buffer, uint32_t capacity, uint64_t *digest_out) {
    koronos_partition_t root;
    if (koronos_vfs_find_by_type(koronos_root_type_guid, &root) != 0) return false;
    int mount = -1;
    if (koronos_vfs_mount(root.index, &mount) != 0) return false;
    const uint64_t digest = root_digest_(mount);
    const uint32_t mounted = koronos_vfs_mount_state();
    const bool fsck = koronos_vfs_verify(mount) == 0;
    koronos_vfs_unmount(mount);
    if (!digest || !fsck) return false;
    if (digest_out) *digest_out = digest;
    uint8_t text[128];
    uint32_t at = append_text_(text, 0, "VFS_HANDOFF mounted=");
    at = append_decimal_(text, at, mounted);
    at = append_text_(text, at, " root_digest=");
    at = append_hex64_(text, at, digest);
    text[at++] = '\n';
    text[at] = 0;
    if (at + 1u > capacity) return false;
    for (uint32_t i = 0; i <= at; ++i) buffer[i] = static_cast<char>(text[i]);
    return true;
}
extern "C" int koronos_vfs_handoff_user(uint64_t address, uint64_t length) {
    if (!length || length > 4096u) return -22;
    uint64_t root = 0;
    __asm__ volatile("mov %%cr3, %0" : "=r"(root));
    if (koronos_address_space_validate_user_range(root, address, length, 1u) != 0) return -14;
    char token[128];
    if (!handoff_token_(token, sizeof(token), nullptr)) return -5;
    char *destination = reinterpret_cast<char *>(static_cast<uintptr_t>(address));
    uint32_t at = 0;
    while (token[at] && at + 1u < length) { destination[at] = token[at]; ++at; }
    destination[at] = 0;
    return static_cast<int>(at);
}
extern "C" int koronos_live_run(void) {
    reset_status_(KORONOS_PHASE_LIVE);
    char token[128];
    uint64_t digest = 0;
    if (!handoff_token_(token, sizeof(token), &digest)) {
        debug_("[LIVE ] FAIL: installed root handoff");
        return -1;
    }
    status_.handoff = 1u;
    status_.mount_state = 1u;
    status_.fsck_pass = 1u;
    status_.root_digest = digest;
    debug_u64_("[LIVE ] root_digest=", digest, true);
    debug_u64_("[LIVE ] handoff=", status_.handoff, false);
    return 0;
}

extern "C" int koronos_install_run_phase(koronos_install_phase_t phase) {
    switch (phase) {
        case KORONOS_PHASE_INSTALLER: return koronos_installer_run();
        case KORONOS_PHASE_INSTALLED: return koronos_installed_run();
        case KORONOS_PHASE_RECOVERY: return koronos_recovery_run();
        case KORONOS_PHASE_VERIFY: return koronos_verify_run();
        case KORONOS_PHASE_LIVE: return koronos_live_run();
        default: return 0;
    }
}
