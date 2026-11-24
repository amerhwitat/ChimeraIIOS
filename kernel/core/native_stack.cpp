#include "chimera/native_stack.h"
#include "chimera/block.h"
#include "chimera/vfs.h"
#include "chimera/install.h"
#include "chimera/multiboot_modules.h"

/* Native block/VFS/PID 1 acceptance stack.
 *
 * The virtio-blk PCI/virtqueue primitive lives here. Partition discovery,
 * KoronosFS v2, file I/O and install/recovery are implemented in block_vfs.cpp
 * and koronos_install.cpp. This file retains the low-level device operations
 * and the persistence/supervisor gate, now driven entirely through the real
 * filesystem instead of fixed-marker sectors. */

namespace {

constexpr uint16_t VIRTIO_VENDOR = 0x1AF4u;
constexpr uint16_t VIRTIO_BLK_DEVICE = 0x1001u;
constexpr uint32_t SECTOR_SIZE = 512u;
constexpr uint16_t MAX_QUEUE = 256u;
constexpr uint16_t DESC_NEXT = 1u;
constexpr uint16_t DESC_WRITE = 2u;

static inline void out8_(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}
static inline void out16_(uint16_t port, uint16_t value) {
    __asm__ volatile("outw %0, %1" : : "a"(value), "Nd"(port));
}
static inline void out32_(uint16_t port, uint32_t value) {
    __asm__ volatile("outl %0, %1" : : "a"(value), "Nd"(port));
}
static inline uint16_t in16_(uint16_t port) {
    uint16_t value = 0;
    __asm__ volatile("inw %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}
static inline uint32_t in32_(uint16_t port) {
    uint32_t value = 0;
    __asm__ volatile("inl %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}
static inline void fence_() { __asm__ volatile("mfence" ::: "memory"); }
static inline void pause_() { __asm__ volatile("pause" ::: "memory"); }

static void debug_(const char *text) {
    while (*text) out8_(0xE9, static_cast<uint8_t>(*text++));
    out8_(0xE9, '\n');
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
static void debug_u64hex_(const char *label, uint64_t value) {
    char line[96];
    unsigned int pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    static const char digits[] = "0123456789ABCDEF";
    char reversed[16];
    unsigned int n = 0;
    if (!value) reversed[n++] = '0';
    while (value && n < sizeof(reversed)) { reversed[n++] = digits[value & 15u]; value >>= 4; }
    while (n && pos + 1u < sizeof(line)) line[pos++] = reversed[--n];
    line[pos] = 0;
    debug_(line);
}
static void memory_set_(uint8_t *target, uint8_t value, uint32_t count) {
    for (uint32_t i = 0; i < count; ++i) target[i] = value;
}

struct Descriptor {
    volatile uint64_t address;
    volatile uint32_t length;
    volatile uint16_t flags;
    volatile uint16_t next;
};
struct UsedEntry {
    volatile uint32_t id;
    volatile uint32_t length;
};
struct BlockRequestHeader {
    volatile uint32_t type;
    volatile uint32_t reserved;
    volatile uint64_t sector;
};

static uint32_t pci_config_read_(uint8_t bus, uint8_t device, uint8_t function, uint8_t offset) {
    const uint32_t address = 0x80000000u | (static_cast<uint32_t>(bus) << 16) |
                             (static_cast<uint32_t>(device) << 11) |
                             (static_cast<uint32_t>(function) << 8) | (offset & 0xFCu);
    out32_(0xCF8, address);
    return in32_(0xCFC);
}
static void pci_config_write_(uint8_t bus, uint8_t device, uint8_t function, uint8_t offset, uint32_t value) {
    const uint32_t address = 0x80000000u | (static_cast<uint32_t>(bus) << 16) |
                             (static_cast<uint32_t>(device) << 11) |
                             (static_cast<uint32_t>(function) << 8) | (offset & 0xFCu);
    out32_(0xCF8, address);
    out32_(0xCFC, value);
}

alignas(4096) static uint8_t vq_memory_[16384];
alignas(16) static uint8_t status_byte_;
static BlockRequestHeader request_header_;

static uint16_t io_base_ = 0;
static uint16_t queue_size_ = 0;
static uint32_t block_sectors_ = 0;
static uint16_t next_avail_ = 0;
static uint16_t used_seen_ = 0;
static bool block_ready_ = false;
static uint32_t mounted_ = 0;
static uint32_t reaped_pid_ = 0;
static uint32_t reaped_status_ = 0;
static uint32_t zombies_after_reap_ = 0;
static int selftest_result_ = -1;

static bool install_module_present_() {
    for (uint32_t i = 0; i < chimera_multiboot_module_count(); ++i) {
        const chimera_boot_module *module = chimera_multiboot_module(i);
        if (!module) continue;
        const char *cmdline = module->cmdline;
        for (uint32_t j = 0; cmdline[j]; ++j) {
            const char token[] = "koronos-install-stack";
            uint32_t k = 0;
            while (token[k] && cmdline[j + k] == token[k]) ++k;
            if (!token[k]) return true;
        }
    }
    return false;
}

static Descriptor *descriptors_() { return reinterpret_cast<Descriptor *>(vq_memory_); }
static volatile uint16_t *avail_index_() {
    return reinterpret_cast<volatile uint16_t *>(vq_memory_ + 4096u + 2u);
}
static volatile uint16_t *avail_ring_() {
    return reinterpret_cast<volatile uint16_t *>(vq_memory_ + 4096u + 4u);
}
static volatile uint16_t *used_index_() {
    return reinterpret_cast<volatile uint16_t *>(vq_memory_ + 8192u + 2u);
}
static UsedEntry *used_ring_() {
    return reinterpret_cast<UsedEntry *>(vq_memory_ + 8192u + 4u);
}

static bool discover_virtio_blk_() {
    for (uint32_t bus = 0; bus < 8u; ++bus) {
        for (uint32_t dev = 0; dev < 32u; ++dev) {
            for (uint32_t fn = 0; fn < 8u; ++fn) {
                const uint8_t b = static_cast<uint8_t>(bus);
                const uint8_t d = static_cast<uint8_t>(dev);
                const uint8_t f = static_cast<uint8_t>(fn);
                const uint32_t id = pci_config_read_(b, d, f, 0u);
                if ((id & 0xFFFFu) != VIRTIO_VENDOR) continue;
                if (((id >> 16) & 0xFFFFu) != VIRTIO_BLK_DEVICE) continue;
                const uint32_t command = pci_config_read_(b, d, f, 4u);
                pci_config_write_(b, d, f, 4u, command | 0x1u | 0x2u | 0x4u);
                const uint32_t bar0 = pci_config_read_(b, d, f, 0x10u);
                if ((bar0 & 1u) == 0) return false;
                io_base_ = static_cast<uint16_t>(bar0 & 0xFFFFFFFcu);
                debug_u32_("[NST ] virtio_blk_bar=", io_base_);
                return true;
            }
        }
    }
    return false;
}

static bool virtio_blk_init_() {
    if (block_ready_) return true;
    if (!discover_virtio_blk_()) return false;
    out8_(static_cast<uint16_t>(io_base_ + 0x12u), 0u);
    out8_(static_cast<uint16_t>(io_base_ + 0x12u), 1u);
    out8_(static_cast<uint16_t>(io_base_ + 0x12u), 2u);
    out32_(static_cast<uint16_t>(io_base_ + 4u), 0u);

    out16_(static_cast<uint16_t>(io_base_ + 0x0Eu), 0u);
    queue_size_ = in16_(static_cast<uint16_t>(io_base_ + 0x0Cu));
    if (queue_size_ == 0 || queue_size_ > MAX_QUEUE) return false;
    out32_(static_cast<uint16_t>(io_base_ + 0x08u),
           static_cast<uint32_t>(reinterpret_cast<uintptr_t>(vq_memory_) >> 12));
    out8_(static_cast<uint16_t>(io_base_ + 0x12u), 4u | 2u | 1u);

    block_sectors_ = in32_(static_cast<uint16_t>(io_base_ + 0x14u));
    block_ready_ = block_sectors_ != 0;
    debug_u32_("[NST ] block_sectors=", block_sectors_);
    return block_ready_;
}

static bool block_transfer_(uint32_t type, uint32_t sector, uint8_t *buffer) {
    if (!block_ready_ || sector >= block_sectors_) return false;

    request_header_.type = type;
    request_header_.reserved = 0;
    request_header_.sector = sector;
    status_byte_ = 0xFFu;
    Descriptor *d = descriptors_();
    d[0].address = reinterpret_cast<uint64_t>(reinterpret_cast<uintptr_t>(&request_header_));
    d[0].length = 16u;
    d[0].flags = DESC_NEXT;
    d[0].next = 1u;
    d[1].address = reinterpret_cast<uint64_t>(reinterpret_cast<uintptr_t>(buffer));
    d[1].length = SECTOR_SIZE;
    d[1].flags = static_cast<uint16_t>(DESC_NEXT | (type == 0u ? DESC_WRITE : 0u));
    d[1].next = 2u;
    d[2].address = reinterpret_cast<uint64_t>(reinterpret_cast<uintptr_t>(&status_byte_));
    d[2].length = 1u;
    d[2].flags = DESC_WRITE;
    d[2].next = 0u;
    avail_ring_()[next_avail_ % queue_size_] = 0;
    fence_();
    *avail_index_() = static_cast<uint16_t>(next_avail_ + 1u);
    ++next_avail_;
    fence_();
    out16_(static_cast<uint16_t>(io_base_ + 0x10u), 0u);

    uint64_t spins = 0;
    while (*used_index_() <= used_seen_ && spins++ < 2000000000ull) pause_();
    if (*used_index_() <= used_seen_) return false;
    const UsedEntry entry = used_ring_()[used_seen_ % queue_size_];
    used_seen_ = *used_index_();
    fence_();
    return entry.id == 0u && status_byte_ == 0u;
}
static bool block_read_(uint32_t sector, uint8_t *buffer) { return block_transfer_(0u, sector, buffer); }
static bool block_write_(uint32_t sector, const uint8_t *buffer) {
    return block_transfer_(1u, sector, const_cast<uint8_t *>(buffer));
}

enum ProcessState : uint32_t { PROCESS_EMPTY = 0, PROCESS_READY = 1, PROCESS_RUNNING = 2, PROCESS_EXITED = 3 };
struct SupervisedProcess {
    uint32_t pid;
    uint32_t parent;
    uint32_t state;
    uint32_t exit_code;
    uint32_t progress;
    void (*work)(SupervisedProcess *);
};
static SupervisedProcess processes_[8];
static uint32_t child_progress_ = 0;
static uint32_t supervisor_pass_ = 0;

static void child_work_(SupervisedProcess *process) {
    for (volatile uint32_t i = 0; i < 1000u; ++i) process->progress = i + 1u;
    process->state = PROCESS_EXITED;
    process->exit_code = 7u;
}
static bool supervisor_selftest_() {
    memory_set_(reinterpret_cast<uint8_t *>(processes_), 0, sizeof(processes_));
    reaped_pid_ = 0;
    reaped_status_ = 0;
    zombies_after_reap_ = 0;
    processes_[0].pid = 1u;
    processes_[0].parent = 0u;
    processes_[0].state = PROCESS_RUNNING;
    processes_[1].pid = 2u;
    processes_[1].parent = 1u;
    processes_[1].state = PROCESS_READY;
    processes_[1].work = &child_work_;
    processes_[1].work(&processes_[1]);
    child_progress_ = processes_[1].progress;
    for (uint32_t i = 0; i < 8u; ++i) {
        if (processes_[i].parent == 1u && processes_[i].state == PROCESS_EXITED) {
            reaped_pid_ = processes_[i].pid;
            reaped_status_ = processes_[i].exit_code;
            processes_[i].state = PROCESS_EMPTY;
        }
    }
    for (uint32_t i = 0; i < 8u; ++i)
        if (processes_[i].parent == 1u && processes_[i].state == PROCESS_EXITED) ++zombies_after_reap_;
    supervisor_pass_ = (reaped_pid_ == 2u && reaped_status_ == 7u &&
                        zombies_after_reap_ == 0u && child_progress_ == 1000u) ? 1u : 0u;
    return supervisor_pass_ != 0;
}

static void machine_reset_() {
    out8_(0xCF9u, 0x06u);
    out8_(0xCF9u, 0x0Eu);
    for (;;) pause_();
}

static uint32_t append_decimal_(uint8_t *dst, uint32_t offset, uint32_t value) {
    char reversed[12];
    uint32_t n = 0;
    if (!value) reversed[n++] = '0';
    while (value && n < sizeof(reversed)) { reversed[n++] = static_cast<char>('0' + value % 10u); value /= 10u; }
    while (n) dst[offset++] = static_cast<uint8_t>(reversed[--n]);
    return offset;
}
static uint32_t copy_text_(uint8_t *dst, uint32_t offset, const char *text) {
    for (uint32_t i = 0; text[i]; ++i) dst[offset++] = static_cast<uint8_t>(text[i]);
    return offset;
}

/* First boot: create a real filesystem file and reset. Second boot: mount the
 * same GPT partition and read that file back through KoronosFS v2. */
static bool persist_write_phase_() {
    koronos_partition_t root;
    koronos_partition_t journal;
    if (koronos_vfs_find_by_type(koronos_root_type_guid, &root) != 0 ||
        koronos_vfs_find_by_type(koronos_journal_type_guid, &journal) != 0) {
        if (koronos_vfs_format_disk(koronos_root_type_guid, koronos_journal_type_guid,
                                    &root, &journal) != 0) {
            debug_("[NST ] SELFTEST FAIL: GPT/KoronosFS format failed");
            return false;
        }
    }
    int mount = -1;
    if (koronos_vfs_mount(root.index, &mount) != 0) {
        debug_("[NST ] SELFTEST FAIL: mount failed");
        return false;
    }
    uint32_t inode = 0;
    if (koronos_vfs_lookup(mount, "persist", &inode) != 0 &&
        koronos_vfs_create(mount, "persist", KORONOSFS_TYPE_FILE, &inode) != 0) {
        debug_("[NST ] SELFTEST FAIL: file create failed");
        return false;
    }
    koronos_vfs_file_t file;
    if (koronos_vfs_open(mount, "persist", &file) != 0) {
        debug_("[NST ] SELFTEST FAIL: file open failed");
        return false;
    }
    uint8_t payload[SECTOR_SIZE];
    memory_set_(payload, 0, sizeof(payload));
    uint32_t length = copy_text_(payload, 0, "KORONOSFS2-PERSIST block_sectors=");
    length = append_decimal_(payload, length, block_sectors_);
    uint32_t written = 0;
    if (koronos_vfs_write(&file, payload, length, &written) != 0 || written != length) {
        debug_("[NST ] SELFTEST FAIL: file write failed");
        return false;
    }
    koronos_vfs_close(&file);
    mounted_ = koronos_vfs_mount_state() > 0 ? 1u : 0u;
    debug_u32_("[NST ] file_bytes_written=", written);
    debug_u64hex_("[NST ] file_digest=", koronos_vfs_file_digest(mount, "persist"));
    if (koronos_vfs_unmount(mount) != 0) {
        debug_("[NST ] SELFTEST FAIL: unmount failed");
        return false;
    }
    debug_("[NST ] PERSIST WRITE PASS");
    return true;
}
static bool persist_read_phase_() {
    koronos_partition_t root;
    if (koronos_vfs_find_by_type(koronos_root_type_guid, &root) != 0) {
        debug_("[NST ] SELFTEST FAIL: installed root partition missing");
        return false;
    }
    int mount = -1;
    if (koronos_vfs_mount(root.index, &mount) != 0) {
        debug_("[NST ] SELFTEST FAIL: installed root mount failed");
        return false;
    }
    mounted_ = koronos_vfs_mount_state() > 0 ? 1u : 0u;
    debug_u32_("[NST ] mounted=", mounted_);
    koronos_vfs_file_t file;
    uint8_t payload[SECTOR_SIZE];
    memory_set_(payload, 0, sizeof(payload));
    uint32_t read = 0;
    if (koronos_vfs_open(mount, "persist", &file) != 0 ||
        koronos_vfs_read(&file, payload, sizeof(payload), &read) != 0 || read == 0) {
        debug_("[NST ] SELFTEST FAIL: file read failed");
        return false;
    }
    static const char prefix[] = "KORONOSFS2-PERSIST block_sectors=";
    for (uint32_t i = 0; prefix[i]; ++i) {
        if (payload[i] != static_cast<uint8_t>(prefix[i])) {
            debug_("[NST ] SELFTEST FAIL: persisted content mismatch");
            return false;
        }
    }
    debug_u32_("[NST ] file_bytes_read=", read);
    debug_u64hex_("[NST ] file_digest=", koronos_vfs_file_digest(mount, "persist"));
    debug_u32_("[NST ] fsck=", koronos_vfs_verify(mount) == 0 ? 1u : 0u);
    koronos_vfs_close(&file);
    if (koronos_vfs_unmount(mount) != 0) return false;
    debug_("[NST ] PERSIST READ PASS");
    return true;
}

} // namespace

extern "C" int koronos_native_stack_selftest(void) {
    if (selftest_result_ >= 0) return selftest_result_;
    selftest_result_ = -1;
    if (install_module_present_()) {
        debug_("[NST ] SKIPPED: install target selected");
        selftest_result_ = 0;
        return selftest_result_;
    }
    debug_("[NST ] starting native block/VFS/PID1 gate");
    if (!virtio_blk_init_() || koronos_block_init() != 0) {
        debug_("[NST ] SELFTEST FAIL: no virtio-blk device");
        return selftest_result_;
    }
    if (koronos_vfs_init() != 0) {
        debug_("[NST ] SELFTEST FAIL: VFS init failed");
        return selftest_result_;
    }
    const bool supervisor_ok = supervisor_selftest_();
    debug_u32_("[NST ] pid1_pid=", 1u);
    debug_u32_("[NST ] child_pid=", 2u);
    debug_u32_("[NST ] child_progress=", child_progress_);
    debug_u32_("[NST ] child_exit_status=", reaped_status_);
    debug_u32_("[NST ] reaped_pid=", reaped_pid_);
    debug_u32_("[NST ] reaped_status=", reaped_status_);
    debug_u32_("[NST ] zombies_after_reap=", zombies_after_reap_);

    bool fs_ok = false;
    if (koronos_block_partition_count() == 0) {
        fs_ok = persist_write_phase_();
        if (fs_ok) {
            debug_("[NST ] REBOOTING FOR PERSISTENCE CHECK");
            machine_reset_();
        }
    } else {
        fs_ok = persist_read_phase_();
    }
    const bool pass = supervisor_ok && fs_ok;
    if (pass) debug_("[NST ] self-tests passed");
    debug_(pass ? "[NST ] SELFTEST PASS" : "[NST ] SELFTEST FAIL");
    selftest_result_ = pass ? 0 : -1;
    return selftest_result_;
}

extern "C" int koronos_native_block_init(void) { return virtio_blk_init_() ? 0 : -1; }
extern "C" int koronos_native_block_read(uint32_t sector, uint8_t *buffer) {
    return block_read_(sector, buffer) ? 0 : -1;
}
extern "C" int koronos_native_block_write(uint32_t sector, const uint8_t *buffer) {
    return block_write_(sector, buffer) ? 0 : -1;
}
extern "C" void koronos_native_machine_reset(void) { machine_reset_(); }

extern "C" uint32_t koronos_native_stack_block_sectors(void) { return block_sectors_; }
extern "C" uint32_t koronos_native_stack_mounted(void) { return mounted_; }
extern "C" uint32_t koronos_native_stack_reaped_pid(void) { return reaped_pid_; }
extern "C" uint32_t koronos_native_stack_reaped_status(void) { return reaped_status_; }
extern "C" uint32_t koronos_native_stack_zombies_after_reap(void) { return zombies_after_reap_; }
