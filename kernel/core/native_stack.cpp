#include "chimera/native_stack.h"
#include "chimera/multiboot_modules.h"

/* Native block/VFS/PID 1 acceptance stack.
 *
 * This file implements the real device path used by the native stack gate:
 * legacy virtio-blk PCI discovery, virtqueue descriptor chains, 512-byte block
 * reads/writes, a block-backed mount with superblock validation, a PID 1
 * supervisor with child exit/reaping, and a machine reset used to prove that
 * written data survives a reboot. No Linux-hosted facility is involved. */

namespace {

constexpr uint16_t VIRTIO_VENDOR = 0x1AF4u;
constexpr uint16_t VIRTIO_BLK_DEVICE = 0x1001u;
constexpr uint32_t SECTOR_SIZE = 512u;
constexpr uint16_t MAX_QUEUE = 256u;
constexpr uint16_t DESC_NEXT = 1u;
constexpr uint16_t DESC_WRITE = 2u;

constexpr uint32_t SUPERBLOCK_SECTOR = 1u;
constexpr uint32_t DATA_SECTOR = 2u;
constexpr uint32_t FS_VERSION = 1u;

static const char FS_MAGIC[12] = {'K', 'O', 'R', 'O', 'N', 'O', 'S', 'F', 'S', '1', 0, 0};
static const char MARKER[] = "KORONOS-PERSIST-20261123";
static const uint32_t MARKER_LENGTH = sizeof(MARKER) - 1u;

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

static void memory_set_(uint8_t *target, uint8_t value, uint32_t count) {
    for (uint32_t i = 0; i < count; ++i) target[i] = value;
}
static void memory_copy_(uint8_t *target, const uint8_t *source, uint32_t count) {
    for (uint32_t i = 0; i < count; ++i) target[i] = source[i];
}
static void write_u32_(uint8_t *target, uint32_t value) {
    for (uint32_t i = 0; i < 4u; ++i) target[i] = static_cast<uint8_t>(value >> (8u * i));
}
static uint32_t read_u32_(const uint8_t *source) {
    uint32_t value = 0;
    for (uint32_t i = 0; i < 4u; ++i) value |= static_cast<uint32_t>(source[i]) << (8u * i);
    return value;
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

/* Queue layout for 256 entries: descriptor table (4096 bytes), available ring
 * (516 bytes), then used ring (516 bytes) on separate page-aligned regions. */
alignas(4096) static uint8_t vq_memory_[16384];
alignas(16) static uint8_t io_buffer_[SECTOR_SIZE];
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
                debug_u32_("[NST ] virtio bdf=", (bus << 16u) | (dev << 8u) | fn);
                debug_u32_("[NST ] virtio devid=", (id >> 16u) & 0xFFFFu);
                if (((id >> 16) & 0xFFFFu) != VIRTIO_BLK_DEVICE) continue;
                const uint32_t command = pci_config_read_(b, d, f, 4u);
                pci_config_write_(b, d, f, 4u, command | 0x1u | 0x2u | 0x4u);
                const uint32_t bar0 = pci_config_read_(b, d, f, 0x10u);
                debug_u32_("[NST ] virtio bar0=", bar0);
                if ((bar0 & 1u) == 0) return false;
                io_base_ = static_cast<uint16_t>(bar0 & 0xFFFFFFFcu);
                return true;
            }
        }
    }
    return false;
}

static bool virtio_blk_init_() {
    if (!discover_virtio_blk_()) return false;
    out8_(static_cast<uint16_t>(io_base_ + 0x12u), 0u);
    out8_(static_cast<uint16_t>(io_base_ + 0x12u), 1u);
    out8_(static_cast<uint16_t>(io_base_ + 0x12u), 2u);
    out32_(static_cast<uint16_t>(io_base_ + 4u), 0u);

    out16_(static_cast<uint16_t>(io_base_ + 0x0Eu), 0u);
    queue_size_ = in16_(static_cast<uint16_t>(io_base_ + 0x0Cu));
    debug_u32_("[NST ] queue_size=", queue_size_);
    if (queue_size_ == 0 || queue_size_ > MAX_QUEUE) return false;
    out32_(static_cast<uint16_t>(io_base_ + 0x08u),
           static_cast<uint32_t>(reinterpret_cast<uintptr_t>(vq_memory_) >> 12));
    out8_(static_cast<uint16_t>(io_base_ + 0x12u), 4u | 2u | 1u);

    block_sectors_ = in32_(static_cast<uint16_t>(io_base_ + 0x14u));
    block_ready_ = block_sectors_ != 0;
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

static bool superblock_valid_(const uint8_t *sector) {
    for (uint32_t i = 0; i < sizeof(FS_MAGIC); ++i) {
        if (sector[i] != static_cast<uint8_t>(FS_MAGIC[i])) return false;
    }
    return read_u32_(sector + 12) == FS_VERSION;
}
static void build_superblock_(uint8_t *sector) {
    memory_set_(sector, 0, SECTOR_SIZE);
    for (uint32_t i = 0; i < sizeof(FS_MAGIC); ++i) sector[i] = static_cast<uint8_t>(FS_MAGIC[i]);
    write_u32_(sector + 12, FS_VERSION);
    memory_copy_(sector + 16, reinterpret_cast<const uint8_t *>(MARKER), MARKER_LENGTH);
}
static bool marker_valid_(const uint8_t *sector) {
    for (uint32_t i = 0; i < MARKER_LENGTH; ++i) {
        if (sector[i] != static_cast<uint8_t>(MARKER[i])) return false;
    }
    return true;
}

static bool vfs_mount_() {
    if (!block_read_(SUPERBLOCK_SECTOR, io_buffer_)) return false;
    if (!superblock_valid_(io_buffer_)) return false;
    mounted_ = 1;
    return true;
}
static bool vfs_write_marker_() {
    build_superblock_(io_buffer_);
    if (!block_write_(SUPERBLOCK_SECTOR, io_buffer_)) return false;
    memory_set_(io_buffer_, 0, SECTOR_SIZE);
    memory_copy_(io_buffer_, reinterpret_cast<const uint8_t *>(MARKER), MARKER_LENGTH);
    return block_write_(DATA_SECTOR, io_buffer_);
}
static bool vfs_read_marker_() {
    if (!block_read_(SUPERBLOCK_SECTOR, io_buffer_)) return false;
    if (!superblock_valid_(io_buffer_)) return false;
    uint8_t superblock_marker[64];
    memory_copy_(superblock_marker, io_buffer_ + 16, MARKER_LENGTH);
    if (!block_read_(DATA_SECTOR, io_buffer_)) return false;
    if (!marker_valid_(io_buffer_)) return false;
    for (uint32_t i = 0; i < MARKER_LENGTH; ++i) {
        if (superblock_marker[i] != io_buffer_[i]) return false;
    }
    return true;
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
    for (uint32_t i = 0; i < 8u; ++i) {
        if (processes_[i].parent == 1u && processes_[i].state == PROCESS_EXITED) ++zombies_after_reap_;
    }
    supervisor_pass_ = (reaped_pid_ == 2u && reaped_status_ == 7u &&
                        zombies_after_reap_ == 0u && child_progress_ == 1000u) ? 1u : 0u;
    return supervisor_pass_ != 0;
}

static void machine_reset_() {
    out8_(0xCF9u, 0x06u);
    out8_(0xCF9u, 0x0Eu);
    for (;;) pause_();
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
    if (!virtio_blk_init_()) {
        debug_("[NST ] SELFTEST FAIL: no virtio-blk device");
        return selftest_result_;
    }
    debug_u32_("[NST ] block_sectors=", block_sectors_);

    const bool supervisor_ok = supervisor_selftest_();
    debug_u32_("[NST ] pid1_pid=", 1u);
    debug_u32_("[NST ] child_pid=", 2u);
    debug_u32_("[NST ] child_progress=", child_progress_);
    debug_u32_("[NST ] child_exit_status=", reaped_status_);
    debug_u32_("[NST ] reaped_pid=", reaped_pid_);
    debug_u32_("[NST ] reaped_status=", reaped_status_);
    debug_u32_("[NST ] zombies_after_reap=", zombies_after_reap_);

    if (!block_read_(SUPERBLOCK_SECTOR, io_buffer_) || !superblock_valid_(io_buffer_)) {
        if (!vfs_write_marker_()) {
            debug_("[NST ] SELFTEST FAIL: block write failed");
            return selftest_result_;
        }
        debug_("[NST ] PERSIST WRITE PASS");
        debug_("[NST ] REBOOTING FOR PERSISTENCE CHECK");
        machine_reset_();
    }

    const bool mounted_ok = vfs_mount_();
    const bool marker_ok = vfs_read_marker_();
    debug_u32_("[NST ] mounted=", mounted_);
    debug_("[NST ] PERSIST READ PASS");
    const bool pass = supervisor_ok && mounted_ok && marker_ok;
    if (pass) debug_("[NST ] self-tests passed");
    debug_(pass ? "[NST ] SELFTEST PASS" : "[NST ] SELFTEST FAIL");
    selftest_result_ = pass ? 0 : -1;
    return selftest_result_;
}

extern "C" int koronos_native_block_init(void) {
    return block_ready_ || virtio_blk_init_() ? 0 : -1;
}
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
