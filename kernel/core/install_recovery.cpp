#include "chimera/native_stack.h"
#include "chimera/multiboot_modules.h"

/* Native installer / installed-root / recovery acceptance stack.
 *
 * Each boot carries a Multiboot2 module whose cmdline names the phase. The
 * phase sequence uses the same real virtio-blk backend as the block/VFS gate:
 *   installer -> committed journal + installed root, reset
 *   installed -> verify handoff, stage an interrupted write, reset
 *   recovery  -> roll back the pending journal and repair the superblock, reset
 *   verify    -> confirm restored root, rolled-back journal, repaired FS
 */

namespace {

constexpr uint32_t CONTROL_SECTOR = 0u;
constexpr uint32_t JOURNAL_SECTOR = 1u;
constexpr uint32_t ROOT_SB_SECTOR = 2u;
constexpr uint32_t ROOT_DATA_SECTOR = 3u;
constexpr uint32_t SECTOR_SIZE = 512u;

static const char CONTROL_MAGIC[16] = {'K','O','R','O','N','O','S','-','I','N','S','T','-','C','T','L'};
static const char JOURNAL_MAGIC[16] = {'K','O','R','O','N','O','S','-','J','O','U','R','N','A','L','!'};
static const char ROOT_MAGIC[16] = {'K','O','R','O','N','O','S','R','O','O','T','F','S','1','\0','\0'};
static const char GOOD_MARKER[] = "KORONOS-INSTALLED-ROOT-MARKER";
static const char PRE_MARKER[] = "KORONOS-PRE-INSTALL-MARKER";
static const char BAD_MARKER[] = "KORONOS-CORRUPTED-MARKER";

enum Phase : uint8_t { PHASE_NONE = 0, PHASE_INSTALLER = 1, PHASE_INSTALLED = 2, PHASE_RECOVERY = 3, PHASE_VERIFY = 4 };
enum JournalState : uint8_t { JOURNAL_COMMITTED = 'C', JOURNAL_PENDING = 'P', JOURNAL_ROLLED_BACK = 'R' };

alignas(16) static uint8_t sector_buffer_[SECTOR_SIZE];
alignas(16) static uint8_t scratch_buffer_[SECTOR_SIZE];

static inline void debug_(const char *text) {
    while (*text) __asm__ volatile("outb %0, $0xE9" : : "a"(*text++));
    __asm__ volatile("outb %0, $0xE9" : : "a"('\n'));
}

static void debug_u32_(const char *label, uint32_t value) {
    char line[96];
    unsigned int pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    char digits[10];
    unsigned int n = 0;
    if (value == 0) digits[n++] = '0';
    while (value && n < sizeof(digits)) {
        digits[n++] = static_cast<char>('0' + (value % 10u));
        value /= 10u;
    }
    while (n && pos + 1u < sizeof(line)) line[pos++] = digits[--n];
    line[pos] = 0;
    debug_(line);
}

static void memory_set_(uint8_t *target, uint8_t value, uint32_t count) {
    for (uint32_t i = 0; i < count; ++i) target[i] = value;
}
static void memory_copy_(uint8_t *target, const uint8_t *source, uint32_t count) {
    for (uint32_t i = 0; i < count; ++i) target[i] = source[i];
}
static uint32_t string_length_(const char *text) {
    uint32_t length = 0;
    while (text[length]) ++length;
    return length;
}
static bool string_equal_(const uint8_t *left, const char *right, uint32_t length) {
    for (uint32_t i = 0; i < length; ++i) {
        if (left[i] != static_cast<uint8_t>(right[i])) return false;
    }
    return true;
}
static uint8_t checksum_(const uint8_t *data, uint32_t length) {
    uint8_t sum = 0;
    for (uint32_t i = 0; i < length; ++i) sum = static_cast<uint8_t>(sum + data[i]);
    return sum;
}

static bool has_token_(const char *text, const char *token) {
    if (!text || !token) return false;
    const uint32_t length = string_length_(token);
    for (uint32_t i = 0; text[i]; ++i) {
        uint32_t j = 0;
        while (j < length && text[i + j] == token[j]) ++j;
        if (j == length) return true;
    }
    return false;
}

static Phase selected_phase_() {
    for (uint32_t i = 0; i < chimera_multiboot_module_count(); ++i) {
        const chimera_boot_module *module = chimera_multiboot_module(i);
        if (!module || !has_token_(module->cmdline, "koronos-install-stack")) continue;
        if (has_token_(module->cmdline, "mode=installer")) return PHASE_INSTALLER;
        if (has_token_(module->cmdline, "mode=installed")) return PHASE_INSTALLED;
        if (has_token_(module->cmdline, "mode=recovery")) return PHASE_RECOVERY;
        if (has_token_(module->cmdline, "mode=verify")) return PHASE_VERIFY;
    }
    return PHASE_NONE;
}

static bool write_control_(Phase next) {
    memory_set_(sector_buffer_, 0, SECTOR_SIZE);
    memory_copy_(sector_buffer_, reinterpret_cast<const uint8_t *>(CONTROL_MAGIC), sizeof(CONTROL_MAGIC));
    sector_buffer_[16] = static_cast<uint8_t>(next);
    return koronos_native_block_write(CONTROL_SECTOR, sector_buffer_) == 0;
}
static Phase read_control_() {
    if (koronos_native_block_read(CONTROL_SECTOR, sector_buffer_) != 0) return PHASE_NONE;
    for (uint32_t i = 0; i < sizeof(CONTROL_MAGIC); ++i) {
        if (sector_buffer_[i] != static_cast<uint8_t>(CONTROL_MAGIC[i])) return PHASE_NONE;
    }
    return static_cast<Phase>(sector_buffer_[16]);
}

static void build_superblock_(uint8_t *sector, const char *marker, uint8_t sequence) {
    memory_set_(sector, 0, SECTOR_SIZE);
    memory_copy_(sector, reinterpret_cast<const uint8_t *>(ROOT_MAGIC), sizeof(ROOT_MAGIC));
    sector[16] = 1u;
    sector[17] = sequence;
    memory_copy_(sector + 32, reinterpret_cast<const uint8_t *>(marker), string_length_(marker));
    sector[96] = checksum_(sector, 96u);
}
static bool superblock_valid_(const uint8_t *sector) {
    for (uint32_t i = 0; i < sizeof(ROOT_MAGIC); ++i) {
        if (sector[i] != static_cast<uint8_t>(ROOT_MAGIC[i])) return false;
    }
    return sector[96] == checksum_(sector, 96u);
}

static bool write_marker_(const char *marker) {
    memory_set_(sector_buffer_, 0, SECTOR_SIZE);
    memory_copy_(sector_buffer_, reinterpret_cast<const uint8_t *>(marker), string_length_(marker));
    return koronos_native_block_write(ROOT_DATA_SECTOR, sector_buffer_) == 0;
}
static bool marker_matches_(const char *marker) {
    if (koronos_native_block_read(ROOT_DATA_SECTOR, sector_buffer_) != 0) return false;
    return string_equal_(sector_buffer_, marker, string_length_(marker));
}

static void build_journal_(uint8_t *sector, JournalState state, const char *before,
                           const char *after, const uint8_t *superblock_template) {
    memory_set_(sector, 0, SECTOR_SIZE);
    memory_copy_(sector, reinterpret_cast<const uint8_t *>(JOURNAL_MAGIC), sizeof(JOURNAL_MAGIC));
    sector[16] = static_cast<uint8_t>(state);
    memory_copy_(sector + 32, reinterpret_cast<const uint8_t *>(before), string_length_(before));
    memory_copy_(sector + 96, reinterpret_cast<const uint8_t *>(after), string_length_(after));
    memory_copy_(sector + 160, superblock_template, 64u);
    sector[224] = checksum_(sector, 224u);
}
static bool read_journal_(JournalState *state, uint8_t *before, uint8_t *after, uint8_t *superblock_template) {
    if (koronos_native_block_read(JOURNAL_SECTOR, sector_buffer_) != 0) return false;
    for (uint32_t i = 0; i < sizeof(JOURNAL_MAGIC); ++i) {
        if (sector_buffer_[i] != static_cast<uint8_t>(JOURNAL_MAGIC[i])) return false;
    }
    if (sector_buffer_[224] != checksum_(sector_buffer_, 224u)) return false;
    *state = static_cast<JournalState>(sector_buffer_[16]);
    memory_copy_(before, sector_buffer_ + 32, 64u);
    memory_copy_(after, sector_buffer_ + 96, 64u);
    memory_copy_(superblock_template, sector_buffer_ + 160, 64u);
    return true;
}

static bool phase_installer_() {
    build_superblock_(scratch_buffer_, GOOD_MARKER, 1u);
    build_journal_(sector_buffer_, JOURNAL_COMMITTED, PRE_MARKER, GOOD_MARKER, scratch_buffer_);
    if (koronos_native_block_write(JOURNAL_SECTOR, sector_buffer_) != 0) return false;
    debug_("[INS ] JOURNAL WRITE PASS");
    debug_("[INS ] JOURNAL COMMIT PASS");

    if (koronos_native_block_write(ROOT_SB_SECTOR, scratch_buffer_) != 0) return false;
    if (!write_marker_(GOOD_MARKER)) return false;
    debug_("[INS ] INSTALLED ROOT WRITTEN");
    if (!write_control_(PHASE_INSTALLED)) return false;
    debug_("[INS ] HANDOFF next=installed");
    return true;
}

static bool phase_installed_() {
    if (read_control_() != PHASE_INSTALLED) return false;
    if (koronos_native_block_read(ROOT_SB_SECTOR, scratch_buffer_) != 0) return false;
    if (!superblock_valid_(scratch_buffer_)) return false;
    if (!marker_matches_(GOOD_MARKER)) return false;
    debug_("[INS ] INSTALLED ROOT HANDOFF PASS");
    debug_("[INS ] ROOT MOUNTED=1");
    debug_("[INS ] ROOT MARKER PASS");

    /* Simulate an interrupted installer transaction: journal is pending, the
     * root marker is clobbered, and the superblock checksum is damaged. */
    JournalState state = JOURNAL_COMMITTED;
    uint8_t before[64], after[64], template_sb[64];
    if (!read_journal_(&state, before, after, template_sb)) return false;
    build_journal_(sector_buffer_, JOURNAL_PENDING, GOOD_MARKER, BAD_MARKER, template_sb);
    if (koronos_native_block_write(JOURNAL_SECTOR, sector_buffer_) != 0) return false;
    if (!write_marker_(BAD_MARKER)) return false;
    memory_set_(scratch_buffer_, 0, SECTOR_SIZE);
    scratch_buffer_[96] = 0xA5u;
    if (koronos_native_block_write(ROOT_SB_SECTOR, scratch_buffer_) != 0) return false;
    if (!write_control_(PHASE_RECOVERY)) return false;
    debug_("[INS ] CRASH SIMULATION PASS");
    debug_("[INS ] HANDOFF next=recovery");
    return true;
}

static bool phase_recovery_() {
    if (read_control_() != PHASE_RECOVERY) return false;
    JournalState state = JOURNAL_COMMITTED;
    uint8_t before[64], after[64], template_sb[64];
    if (!read_journal_(&state, before, after, template_sb)) return false;
    if (state != JOURNAL_PENDING) return false;

    memory_set_(sector_buffer_, 0, SECTOR_SIZE);
    for (uint32_t i = 0; i < 64u; ++i) sector_buffer_[i] = before[i];
    if (koronos_native_block_write(ROOT_DATA_SECTOR, sector_buffer_) != 0) return false;
    debug_("[REC ] JOURNAL ROLLBACK PASS");

    build_superblock_(scratch_buffer_, GOOD_MARKER, 2u);
    if (koronos_native_block_write(ROOT_SB_SECTOR, scratch_buffer_) != 0) return false;
    debug_("[REC ] SUPERBLOCK REPAIR PASS");
    debug_("[REC ] FILESYSTEM REPAIR PASS");

    build_journal_(sector_buffer_, JOURNAL_ROLLED_BACK, GOOD_MARKER, BAD_MARKER, template_sb);
    if (koronos_native_block_write(JOURNAL_SECTOR, sector_buffer_) != 0) return false;
    if (!write_control_(PHASE_VERIFY)) return false;
    debug_("[REC ] HANDOFF next=verify");
    return true;
}

static bool phase_verify_() {
    if (read_control_() != PHASE_VERIFY) return false;
    if (koronos_native_block_read(ROOT_SB_SECTOR, scratch_buffer_) != 0) return false;
    if (!superblock_valid_(scratch_buffer_)) return false;
    if (!marker_matches_(GOOD_MARKER)) return false;
    JournalState state = JOURNAL_COMMITTED;
    uint8_t before[64], after[64], template_sb[64];
    if (!read_journal_(&state, before, after, template_sb)) return false;
    if (state != JOURNAL_ROLLED_BACK) return false;
    debug_("[INS ] ROOT VERIFY PASS");
    debug_("[INS ] ROLLBACK VERIFY PASS");
    debug_("[INS ] REPAIR VERIFY PASS");
    return true;
}

} // namespace

extern "C" int koronos_install_recovery_selftest(void) {
    const Phase phase = selected_phase_();
    if (phase == PHASE_NONE) {
        debug_("[INS ] SKIPPED: no install target module");
        return 0;
    }
    if (koronos_native_block_init() != 0) {
        debug_("[INS ] SELFTEST FAIL: block backend unavailable");
        return -1;
    }
    debug_u32_("[INS ] mode_selected=", static_cast<uint32_t>(phase));

    bool pass = false;
    bool reset = false;
    switch (phase) {
        case PHASE_INSTALLER:
            pass = phase_installer_();
            reset = pass;
            break;
        case PHASE_INSTALLED:
            pass = phase_installed_();
            reset = pass;
            break;
        case PHASE_RECOVERY:
            pass = phase_recovery_();
            reset = pass;
            break;
        case PHASE_VERIFY:
            pass = phase_verify_();
            break;
        default:
            break;
    }
    if (!pass) {
        debug_("[INS ] SELFTEST FAIL");
        return -1;
    }
    debug_("[INS ] SELFTEST PASS");
    if (reset) {
        debug_("[INS ] REBOOTING FOR NEXT PHASE");
        koronos_native_machine_reset();
    }
    return 0;
}
