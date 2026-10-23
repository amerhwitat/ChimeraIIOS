#include <stdint.h>
#include <stddef.h>
#include "chimera/target_launch.h"
#include "chimera/multiboot_modules.h"
#include "chimera/process_loader.h"
#include "chimera/process.h"
#include "chimera/user_entry.h"
#include "chimera/address_space.h"
#include "chimera/elf64.h"
#include "chimera/frame_allocator.h"
#include "chimera/initramfs_cpio.h"
#include "chimera/initramfs_ingest.h"
#include "chimera/ramfs.h"
#include "chimera/vfs.h"
#include "chimera/tmpfs.h"

namespace {
constexpr uint64_t USER_STACK_TOP = 0x00007FFFFFFFE000ull; // Loader requires a page-aligned stack ceiling
constexpr uint64_t USER_STACK_SIZE = 64ull * 1024ull;
constexpr uint64_t MAX_INIT_IMAGE = 64ull * 1024ull * 1024ull;
enum Target : uint32_t { TARGET_NONE=0, TARGET_LIVE=1, TARGET_INSTALLER=2, TARGET_RECOVERY=3 };
static volatile uint32_t active_target = TARGET_NONE;
static volatile uint32_t ready_seen = 0;
static uint32_t active_pid = 0;
static uint64_t active_root = 0;
static uint32_t syscall_ack_seen = 0;
static bool attempted = false;
/* Candidate-only fallback is gated by the explicit probe=ring3 module flag. */
static bool active_ring3_probe = false;
/* Keep the complete bounded extraction private until the VFS root mount
   succeeds. The tree remains alive while mounted and is never mutated in place. */
static chimera_ramfs_node *staged_rootfs = nullptr;
static bool staged_rootfs_ready = false;
/* Published only after the VFS root mount succeeds. The extracted tree is
   immutable and remains alive for the lifetime of the mounted root. */
static chimera_ramfs_node *published_rootfs = nullptr;
struct RamfsFrameHeader { uint32_t pages; uint32_t magic; uint64_t reserved; };
constexpr uint32_t RAMFS_FRAME_MAGIC = 0x52414D46u;
static void *ramfs_frame_alloc(uint64_t bytes, void *) {
    if (!bytes || bytes > UINT64_MAX - sizeof(RamfsFrameHeader)) return nullptr;
    const uint64_t total = bytes + sizeof(RamfsFrameHeader);
    const uint64_t pages64 = (total + KORONOS_FRAME_SIZE - 1u) / KORONOS_FRAME_SIZE;
    if (!pages64 || pages64 > 16384u) return nullptr;
    const uint64_t base = koronos_frame_alloc_contiguous(static_cast<uint32_t>(pages64));
    if (!base) return nullptr;
    auto *header = reinterpret_cast<RamfsFrameHeader *>(static_cast<uintptr_t>(base));
    header->pages = static_cast<uint32_t>(pages64);
    header->magic = RAMFS_FRAME_MAGIC;
    header->reserved = 0;
    return reinterpret_cast<void *>(static_cast<uintptr_t>(base + sizeof(RamfsFrameHeader)));
}
static void ramfs_frame_free(void *ptr, void *) {
    if (!ptr) return;
    const uintptr_t address = reinterpret_cast<uintptr_t>(ptr);
    if (address < sizeof(RamfsFrameHeader)) return;
    auto *header = reinterpret_cast<RamfsFrameHeader *>(address - sizeof(RamfsFrameHeader));
    if (header->magic != RAMFS_FRAME_MAGIC || !header->pages) return;
    const uint32_t pages = header->pages;
    const uint64_t base = address - sizeof(RamfsFrameHeader);
    header->magic = 0;
    (void)koronos_frame_free_contiguous(base, pages);
}
static int ramfs_vfs_lookup(void *context, const char *path, chimera_vfs_stat *out) {
    if (!context || !path || !out) return -22;
    const auto *node = chimera_ramfs_lookup(static_cast<const chimera_ramfs_node *>(context), path);
    if (!node) return -2;
    out->size = chimera_ramfs_file_size(node);
    out->type = chimera_ramfs_is_directory(node) ? CHIMERA_VFS_DIRECTORY : CHIMERA_VFS_REGULAR;
    out->mode = out->type == CHIMERA_VFS_DIRECTORY ? 0555u : 0444u;
    return 0;
}
static int ramfs_vfs_read(void *context, const char *path, uint64_t offset,
                          void *buffer, uint64_t length, uint64_t *read_out) {
    if (!context || !path || !read_out || (!buffer && length)) return -22;
    const auto *node = chimera_ramfs_lookup(static_cast<const chimera_ramfs_node *>(context), path);
    if (!node) return -2;
    if (chimera_ramfs_is_directory(node)) return -21;
    return chimera_ramfs_read(node, offset, buffer, length, read_out) == CHIMERA_RAMFS_OK ? 0 : -5;
}
static const chimera_vfs_ops ramfs_vfs_ops = {
    ramfs_vfs_lookup, ramfs_vfs_read, nullptr, nullptr, nullptr,
    nullptr, nullptr, nullptr, nullptr
};
static int stage_rootfs(const void *archive, uint64_t archive_size) {
    if (staged_rootfs_ready || staged_rootfs) return -1;
    const chimera_ramfs_allocator allocator{ramfs_frame_alloc, ramfs_frame_free, nullptr};
    const chimera_ramfs_limits limits{CHIMERA_RAMFS_MAX_ENTRIES,
        CHIMERA_RAMFS_MAX_PATH, CHIMERA_RAMFS_MAX_FILE_BYTES,
        CHIMERA_RAMFS_MAX_TOTAL_BYTES};
    chimera_ramfs_node *candidate = nullptr;
    const int rc = chimera_ramfs_extract_newc(archive, archive_size,
        &allocator, &limits, &candidate);
    if (rc != CHIMERA_RAMFS_OK || !candidate) {
        if (candidate) chimera_ramfs_destroy(candidate, &allocator);
        return rc ? rc : CHIMERA_RAMFS_E_HEADER;
    }
    /* Commit only after the extractor validated the whole archive and built
       every node. On any error its contract leaves no published candidate. */
    staged_rootfs = candidate;
    staged_rootfs_ready = true;
    return CHIMERA_RAMFS_OK;
}
struct TemporaryFrames {
    uint64_t base = 0;
    uint32_t pages = 0;
    ~TemporaryFrames() { if (base && pages) (void)koronos_frame_free_contiguous(base, pages); }
};
static uint32_t read_le32(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) | (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) | (static_cast<uint32_t>(p[3]) << 24);
}

extern "C" void koronos_target_log(const char *message);

static bool token(const char *text, const char *needle) {
    if (!text || !needle) return false;
    const uint64_t nlen = [&]() { uint64_t n=0; while (needle[n]) ++n; return n; }();
    for (uint64_t i=0; text[i]; ++i) {
        if (i && text[i-1] != ' ') continue;
        uint64_t j=0;
        while (j<nlen && text[i+j] == needle[j]) ++j;
        if (j==nlen && (text[i+j]==0 || text[i+j]==' ')) return true;
    }
    return false;
}
static Target parse_target(const char *cmdline) {
    const bool live = token(cmdline,"target=live");
    const bool installer = token(cmdline,"target=installer");
    const bool recovery = token(cmdline,"target=recovery");
    if ((live?1:0)+(installer?1:0)+(recovery?1:0) != 1) return TARGET_NONE;
    return live ? TARGET_LIVE : (installer ? TARGET_INSTALLER : TARGET_RECOVERY);
}
static const char *target_name(Target target) {
    switch (target) {
        case TARGET_LIVE: return "live";
        case TARGET_INSTALLER: return "installer";
        case TARGET_RECOVERY: return "recovery";
        default: return "unknown";
    }
}
static void log_user_init_syscall(Target target, uint32_t pid) {
    char message[96];
    const char *name = target_name(target);
    const char prefix[] = "USER INIT SYSCALL: target=";
    size_t used = 0;
    for (size_t i = 0; i < sizeof(prefix) - 1u; ++i) message[used++] = prefix[i];
    while (*name) message[used++] = *name++;
    const char middle[] = " init_pid=";
    for (size_t i = 0; i < sizeof(middle) - 1u; ++i) message[used++] = middle[i];
    char reversed[10]; size_t digits = 0;
    do { reversed[digits++] = (char)('0' + (pid % 10u)); pid /= 10u; }
    while (pid && digits < sizeof(reversed));
    while (digits) message[used++] = reversed[--digits];
    message[used] = 0;
    koronos_target_log(message);
}
static bool target_marker(const char *bytes, uint64_t length, Target target, uint32_t pid) {
    if (!bytes || !length || pid == 0u) return false;
    const char *production_prefix = nullptr;
    const char *probe_prefix = nullptr;
    switch (target) {
        case TARGET_LIVE: production_prefix = "USERSPACE TARGET READY: live component=aurora-session"; probe_prefix = "USERSPACE READY: live"; break;
        case TARGET_INSTALLER: production_prefix = "USERSPACE TARGET READY: installer component=install-executor"; probe_prefix = "USERSPACE READY: installer"; break;
        case TARGET_RECOVERY: production_prefix = "USERSPACE TARGET READY: recovery component=recovery-runtime"; probe_prefix = "USERSPACE READY: recovery"; break;
        default: return false;
    }
    static const char pid_label[] = " init pid=";
    const uint64_t pid_label_len=sizeof(pid_label)-1u;
    for (uint32_t variant=0; variant<2; ++variant) {
      const char *prefix = (variant==0) ? production_prefix : (active_ring3_probe ? probe_prefix : nullptr);
      if (!prefix) continue;
      uint64_t prefix_len=0;
      while (prefix[prefix_len]) ++prefix_len;
      for (uint64_t i=0; i+prefix_len+pid_label_len<length; ++i) {
        uint64_t j=0;
        while (j<prefix_len && bytes[i+j]==prefix[j]) ++j;
        if (j!=prefix_len) continue;
        uint64_t k=i+prefix_len;
        j=0;
        while (j<pid_label_len && k+j<length && bytes[k+j]==pid_label[j]) ++j;
        if (j!=pid_label_len) continue;
        k+=pid_label_len;
        uint32_t parsed=0, digits=0;
        while (k<length && bytes[k]>='0' && bytes[k]<='9') {
            const uint32_t digit=static_cast<uint32_t>(bytes[k]-'0');
            if (parsed>(UINT32_MAX-digit)/10u) { digits=0; break; }
            parsed=parsed*10u+digit;
            ++digits; ++k;
        }
        if (digits && parsed==pid &&
            (k==length || bytes[k]=='\n' || bytes[k]=='\r' || bytes[k]==' '))
            return true;
      }
    }
    return false;
}
}

extern "C" uint32_t koronos_target_userspace_ready(void) { return ready_seen; }
extern "C" uint32_t koronos_target_active_pid(void) {
    return active_target != TARGET_NONE ? active_pid : 0u;
}

/* Read-only process-owned descriptors bridge the validated RAMFS root to ring 3.
   User addresses are validated against the active process's own CR3 before any
   dereference. Writes to regular files remain unsupported (EROFS) until RAMFS
   has transactional mutation semantics. */
static int copy_target_user_path(uint64_t user_path, char path[CHIMERA_VFS_MAX_PATH + 1u]) {
    if (!active_root || !user_path) return -14;
    uint32_t length = 0;
    for (; length <= CHIMERA_VFS_MAX_PATH; ++length) {
        if (user_path > UINT64_MAX - length ||
            koronos_address_space_validate_user_range(active_root, user_path + length, 1u, 0u) != 0)
            return -14;
        const char c = *reinterpret_cast<const volatile char *>(static_cast<uintptr_t>(user_path + length));
        path[length] = c;
        if (!c) break;
    }
    if (length > CHIMERA_VFS_MAX_PATH || !path[0]) return -22;
    return 0;
}
extern "C" int64_t koronos_target_fs_open(uint64_t user_path, uint64_t flags) {
    if (flags > UINT32_MAX) return -22;
    const uint32_t pid = koronos_target_active_pid();
    if (!pid || !active_root || !user_path) return -14;
    char path[CHIMERA_VFS_MAX_PATH + 1u];
    const int path_rc = copy_target_user_path(user_path, path);
    if (path_rc != 0) return path_rc;
    if (!__atomic_load_n(&published_rootfs, __ATOMIC_ACQUIRE)) return -2;
    return chimera_vfs_open(pid, path, static_cast<uint32_t>(flags), 0644u);
}
extern "C" int64_t koronos_target_fs_read(uint64_t fd, uint64_t user_buffer, uint64_t count) {
    const uint32_t pid = koronos_target_active_pid();
    if (!pid || !active_root) return -9;
    if (!count) return 0;
    if (count > 4096u) return -22;
    if (!user_buffer || koronos_address_space_validate_user_range(active_root, user_buffer, count, 1u) != 0)
        return -14;
    return chimera_vfs_read(pid, static_cast<int64_t>(fd), reinterpret_cast<void *>(static_cast<uintptr_t>(user_buffer)), count);
}
extern "C" int64_t koronos_target_fs_write(uint64_t fd, uint64_t user_buffer, uint64_t count) {
    const uint32_t pid = koronos_target_active_pid();
    if (!pid || !active_root) return -9;
    if (!count) return 0;
    if (count > 4096u) return -22;
    if (!user_buffer || koronos_address_space_validate_user_range(active_root, user_buffer, count, 0u) != 0)
        return -14;
    return chimera_vfs_write(pid, static_cast<int64_t>(fd),
        reinterpret_cast<const void *>(static_cast<uintptr_t>(user_buffer)), count);
}
extern "C" int64_t koronos_target_fs_close(uint64_t fd) {
    const uint32_t pid = koronos_target_active_pid();
    if (!pid) return -9;
    return chimera_vfs_close(pid, static_cast<int64_t>(fd));
}
extern "C" int64_t koronos_target_fs_seek(uint64_t fd, uint64_t offset, uint64_t whence) {
    const uint32_t pid = koronos_target_active_pid();
    if (!pid || whence > 2u) return -22;
    return chimera_vfs_seek(pid, static_cast<int64_t>(fd), static_cast<int64_t>(offset), static_cast<uint32_t>(whence));
}
static uint32_t validate_active_user_context(uint64_t user_rip) {
    if (active_target == TARGET_NONE || !active_pid || !active_root) return 0u;
    if (user_rip < 0x0000000100000000ull || user_rip >= 0x0000800000000000ull) return 0u;
    uint64_t current_cr3 = 0;
    __asm__ volatile("mov %%cr3, %0" : "=r"(current_cr3));
    return ((current_cr3 & 0x000FFFFFFFFFF000ull) == active_root) ? active_pid : 0u;
}
extern "C" uint32_t koronos_target_validate_syscall_context(uint64_t user_rip) {
    return validate_active_user_context(user_rip);
}
extern "C" uint32_t koronos_target_note_user_syscall(uint64_t user_rip, uint64_t user_cs) {
    /* This acknowledgement is only reachable from the DPL3 INT 0x80 gate.
       The CPU-saved CS RPL, not an inferred user RIP, proves CPL3 origin.
       Rejection reasons are deliberately explicit: production traces showed
       missing acknowledgements, and a silent zero obscured the failing layer. */
    if ((user_cs & 3u) != 3u) {
        koronos_target_log("[INT80] rejected: saved CS.RPL is not 3");
        return 0u;
    }
    if (active_target == TARGET_NONE || !active_pid || !active_root) {
        koronos_target_log("[INT80] rejected: no active target PID/CR3");
        return 0u;
    }
    if (user_rip < 0x0000000100000000ull || user_rip >= 0x0000800000000000ull) {
        koronos_target_log("[INT80] rejected: saved user RIP is outside the user range");
        return 0u;
    }
    uint64_t current_cr3 = 0;
    __asm__ volatile("mov %%cr3, %0" : "=r"(current_cr3));
    if ((current_cr3 & 0x000FFFFFFFFFF000ull) != active_root) {
        koronos_target_log("[INT80] rejected: current CR3 does not match active process root");
        return 0u;
    }
    const uint32_t pid = active_pid;
    if (!syscall_ack_seen) {
        syscall_ack_seen = 1u;
        log_user_init_syscall(static_cast<Target>(active_target), pid);
    }
    return pid;
}
extern "C" int koronos_target_note_user_write(const char *bytes, uint64_t length) {
    if (!bytes || !length || active_target==TARGET_NONE || !active_pid) return 0;
    /* Readiness is valid only after this active process has already
       issued a syscall through the DPL3 gate and the kernel verified its
       saved CS.RPL, RIP and CR3. A write that arrives first cannot satisfy
       the readiness half of the acceptance handshake. */
    if (syscall_ack_seen && active_pid &&
        target_marker(bytes,length,static_cast<Target>(active_target),active_pid)) {
        ready_seen=1;
        return 1;
    }
    return 0;
}

extern "C" int koronos_launch_selected_userspace(void) {
    if (attempted) return 0;
    attempted=true;
    const chimera_boot_module *selected=nullptr;
    uint32_t count=0;
    for (uint32_t i=0;i<chimera_multiboot_module_count();++i) {
        const chimera_boot_module *m=chimera_multiboot_module(i);
        if (m && m->kind==CHIMERA_MODULE_USER_INIT_ELF) { selected=m; ++count; }
    }
    if (count==0) {
        /* Kernel-only smoke boots have no target payload and remain valid.
         * A production initramfs/install image without its separate native
         * ELF is a packaging/dispatch failure, never a successful handoff. */
        const bool has_target_payload =
            chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS) != nullptr ||
            chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS) != nullptr ||
            chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE) != nullptr;
        if (!has_target_payload) return 0;
        koronos_target_log("[RUN ] ERROR: production target payload is present but no USER_INIT_ELF module was supplied");
        return -12;
    }
    if (count!=1 || !selected || !selected->base || selected->size<sizeof(koronos_elf64_ehdr) ||
        selected->size>MAX_INIT_IMAGE || selected->base>=KORONOS_FRAME_PHYS_LIMIT ||
        selected->size>KORONOS_FRAME_PHYS_LIMIT-selected->base) {
        koronos_target_log("[RUN ] ERROR: expected exactly one bounded USER_INIT_ELF module");
        return -1;
    }
    const Target target=parse_target(selected->cmdline);
    if (target==TARGET_NONE) {
        koronos_target_log("[RUN ] ERROR: user init module must select exactly one target=live|installer|recovery");
        return -2;
    }

    /* Bind the executable init to the independently classified production
       payload. A target=live ELF must not run with an installer/recovery
       image, and multiple payloads are ambiguous even when the ELF is valid.
       Candidate-only smoke boots remain possible when no production payload
       is present; the full ISO gate separately requires a real target payload
       and verifies target operation. */
    uint32_t payload_count=0;
    Target payload_target=TARGET_NONE;
    for (uint32_t i=0;i<chimera_multiboot_module_count();++i) {
        const chimera_boot_module *m=chimera_multiboot_module(i);
        if (!m) continue;
        switch (m->kind) {
            case CHIMERA_MODULE_LIVE_INITRAMFS:
                ++payload_count;
                payload_target=TARGET_LIVE;
                break;
            case CHIMERA_MODULE_INSTALL_IMAGE:
                ++payload_count;
                payload_target=TARGET_INSTALLER;
                break;
            case CHIMERA_MODULE_RECOVERY_INITRAMFS:
                ++payload_count;
                payload_target=TARGET_RECOVERY;
                break;
            default:
                break;
        }
    }
    if (payload_count>1u) {
        koronos_target_log("[RUN ] ERROR: multiple production target payloads are present; refusing ambiguous dispatch");
        return -13;
    }
    if (payload_count==1u && payload_target!=target) {
        koronos_target_log("[RUN ] ERROR: native init target does not match the selected production payload");
        return -14;
    }
    if (payload_count==1u && (target==TARGET_LIVE || target==TARGET_RECOVERY)) {
        const uint32_t kind = target==TARGET_LIVE ? CHIMERA_MODULE_LIVE_INITRAMFS : CHIMERA_MODULE_RECOVERY_INITRAMFS;
        const chimera_boot_module *archive = chimera_multiboot_find(kind);
        if (!archive || !archive->base || !archive->size || archive->base>=KORONOS_FRAME_PHYS_LIMIT ||
            archive->size>MAX_INIT_IMAGE || archive->size>KORONOS_FRAME_PHYS_LIMIT-archive->base) {
            koronos_target_log("[RUN ] ERROR: selected initramfs bounds are invalid");
            return -15;
        }
        const void *archive_bytes = reinterpret_cast<const void *>(static_cast<uintptr_t>(archive->base));
        const auto *archive_prefix = static_cast<const uint8_t *>(archive_bytes);
        chimera_cpio_summary summary{};
        int cpio_rc = CHIMERA_CPIO_OK;
        if (archive->size >= 2u && archive_prefix[0] == 0x1fu && archive_prefix[1] == 0x8bu) {
            if (archive->size < 18u) {
                koronos_target_log("[RUN ] ERROR: truncated gzip initramfs header/trailer");
                return -16;
            }
            const uint64_t expected_size = read_le32(archive_prefix + archive->size - 4u);
            if (expected_size < 110u || expected_size > MAX_INIT_IMAGE) {
                koronos_target_log("[RUN ] ERROR: gzip initramfs ISIZE is outside the bounded CPIO output range");
                return -16;
            }
            const uint64_t pages64 = (expected_size + KORONOS_FRAME_SIZE - 1u) / KORONOS_FRAME_SIZE;
            if (pages64 == 0u || pages64 > 16384u) {
                koronos_target_log("[RUN ] ERROR: gzip initramfs output page count exceeds the configured limit");
                return -16;
            }
            TemporaryFrames decompressed{};
            decompressed.pages = static_cast<uint32_t>(pages64);
            decompressed.base = koronos_frame_alloc_contiguous(decompressed.pages);
            if (!decompressed.base) {
                decompressed.pages = 0;
                koronos_target_log("[RUN ] ERROR: unable to reserve bounded initramfs decompression workspace");
                return -18;
            }
            uint64_t decoded_size = 0;
            cpio_rc = chimera_initramfs_prepare_newc(
                archive_bytes, archive->size,
                reinterpret_cast<void *>(static_cast<uintptr_t>(decompressed.base)),
                expected_size, &decoded_size, &summary);
            if (cpio_rc != CHIMERA_CPIO_OK || decoded_size != expected_size) {
                /* The separately staged, target-matched native ELF is the
                   executable entry point. A shell /init or absent /init in
                   the archive must not reject an otherwise valid rootfs;
                   CPIO safety and gzip integrity remain mandatory. */
                koronos_target_log("[RUN ] ERROR: gzip decode, CRC32/ISIZE, or CPIO safety validation failed");
                return -19;
            }
            koronos_target_log("[RUN ] Bounded gzip/DEFLATE, CRC32/ISIZE and CPIO validation passed");
            const int rootfs_rc = stage_rootfs(
                reinterpret_cast<const void *>(static_cast<uintptr_t>(decompressed.base)),
                decoded_size);
            if (rootfs_rc != CHIMERA_RAMFS_OK) {
                koronos_target_log("[RUN ] ERROR: transactional RAMFS staging failed; no rootfs was published");
                return -20;
            }
            koronos_target_log("[RUN ] Rootfs archive extracted into bounded unpublished RAMFS staging tree");
        } else {
            cpio_rc = chimera_cpio_validate_newc(archive_bytes, archive->size, &summary);
            if (cpio_rc != CHIMERA_CPIO_OK) {
                /* Entry-point selection is provided by the separately staged
                   native init ELF; validate the archive as rootfs data only. */
                koronos_target_log("[RUN ] ERROR: selected initramfs is malformed or unsafe");
                return -17;
            }
            const int rootfs_rc = stage_rootfs(archive_bytes, archive->size);
            if (rootfs_rc != CHIMERA_RAMFS_OK) {
                koronos_target_log("[RUN ] ERROR: transactional RAMFS staging failed; no rootfs was published");
                return -20;
            }
            koronos_target_log("[RUN ] Rootfs archive extracted into bounded unpublished RAMFS staging tree");
        }
    }
    /* The extracted RAMFS tree is immutable and complete at this point. Publish
       it as one root pointer only after extraction succeeded; installer images
       are disk containers, not CPIO rootfs archives, and remain fail-closed. */
    if (payload_count == 1u && (target == TARGET_LIVE || target == TARGET_RECOVERY)) {
        if (!staged_rootfs_ready || !staged_rootfs) {
            koronos_target_log("[RUN ] ERROR: production rootfs staging is absent; refusing userspace launch");
            return -15;
        }
        if (chimera_vfs_init() != 0 ||
            chimera_vfs_mount("/", &ramfs_vfs_ops, staged_rootfs, CHIMERA_VFS_MOUNT_RDONLY) != 0) {
            koronos_target_log("[RUN ] ERROR: VFS root mount failed; refusing userspace launch");
            return -15;
        }
        const chimera_ramfs_allocator tmpfs_allocator{ramfs_frame_alloc, ramfs_frame_free, nullptr};
        const chimera_tmpfs_limits tmpfs_limits{128u, CHIMERA_VFS_MAX_PATH, 1024u * 1024u, 4u * 1024u * 1024u};
        chimera_tmpfs *tmpfs_candidate = nullptr;
        if (chimera_tmpfs_create(&tmpfs_allocator, &tmpfs_limits, &tmpfs_candidate) != 0 ||
            !tmpfs_candidate ||
            chimera_vfs_mount("/tmp", chimera_tmpfs_vfs_ops(), tmpfs_candidate, 0u) != 0) {
            if (tmpfs_candidate) chimera_tmpfs_destroy(tmpfs_candidate);
            (void)chimera_vfs_unmount("/");
            koronos_target_log("[RUN ] ERROR: bounded writable /tmp filesystem mount failed; refusing userspace launch");
            return -15;
        }
        __atomic_store_n(&published_rootfs, staged_rootfs, __ATOMIC_RELEASE);
        koronos_target_log("[VFS ] Read-only initramfs root and bounded writable /tmp mounted; process file mutation syscalls enabled");
    }
    if (payload_count == 1u && target == TARGET_INSTALLER) {
        koronos_target_log("[RUN ] ERROR: installer storage-backed root namespace is not mounted; refusing false readiness");
        return -15;
    }
    if (!koronos_address_space_ready()) {
        koronos_target_log("[RUN ] ERROR: address-space/ring-3 backend unavailable");
        return -3;
    }
    const chimera_elf_load_ops *ops=koronos_address_space_loader_ops();
    if (!ops) {
        koronos_target_log("[RUN ] ERROR: ELF loader has no real address-space operations");
        return -4;
    }

    chimera_process_image process{};
    const int pid=chimera_process_admit_elf(reinterpret_cast<const void *>(static_cast<uintptr_t>(selected->base)),
        selected->size,KORONOS_EM_X86_64,USER_STACK_TOP,&process);
    if (pid<=0) {
        koronos_target_log("[RUN ] ERROR: selected user init failed protected-process admission");
        return -5;
    }
    chimera_loaded_elf loaded{};
    const int load_rc=chimera_elf_load_user_image(
        reinterpret_cast<const void *>(static_cast<uintptr_t>(selected->base)),selected->size,
        KORONOS_EM_X86_64,USER_STACK_TOP,USER_STACK_SIZE,ops,nullptr,&loaded);
    if (load_rc!=0) {
        (void)chimera_process_set_state(static_cast<uint32_t>(pid),CHIMERA_PROCESS_FAULTED);
        koronos_target_log("[RUN ] ERROR: selected user init ELF load failed");
        return -6;
    }
    const uint64_t root=koronos_address_space_root(loaded.address_space);
    if (!root) {
        ops->destroy_address_space(nullptr,loaded.address_space);
        (void)chimera_process_set_state(static_cast<uint32_t>(pid),CHIMERA_PROCESS_FAULTED);
        koronos_target_log("[RUN ] ERROR: selected user init has no owned CR3 root");
        return -7;
    }
    active_target=target;
    active_ring3_probe=token(selected->cmdline, "probe=ring3");
    active_pid=static_cast<uint32_t>(pid);
    active_root=root;
    syscall_ack_seen=0;
    ready_seen=0;
    (void)chimera_process_set_state(active_pid,CHIMERA_PROCESS_RUNNING);
    // 100 Hz PIT deadline: 1,000 ticks gives user init ten seconds to return
    // and emit readiness. This is enforced by IRQ0 inside the kernel, not by
    // the outer QEMU test timeout.
    if (koronos_user_timeout_arm(1000u) != 0) {
        ops->destroy_address_space(nullptr,loaded.address_space);
        (void)chimera_process_set_state(active_pid,CHIMERA_PROCESS_FAULTED);
        active_target=TARGET_NONE;
        koronos_target_log("[RUN ] ERROR: failed to arm PIT-backed in-kernel user timeout");
        return -10;
    }
    koronos_target_log("[RUN ] Dispatching selected user init through CR3 + ring-3 entry with 10s kernel deadline");
    /* _start is a freestanding C entry, not a CRT process-entry shim.
     * Give it the SysV function-entry stack alignment (RSP % 16 == 8).
     * The full final stack page is already mapped by the ELF loader. */
    const uint64_t user_entry_stack = loaded.user_stack_top - sizeof(uint64_t);
    const int exit_code=koronos_arch_enter_user(root,loaded.entry,user_entry_stack);
    koronos_user_timeout_disarm();
    (void)chimera_vfs_close_process(active_pid);
    ops->destroy_address_space(nullptr,loaded.address_space);
    (void)chimera_process_set_state(active_pid,exit_code==0 ? CHIMERA_PROCESS_EXITED : CHIMERA_PROCESS_FAULTED);
    active_target=TARGET_NONE;
    active_ring3_probe=false;
    active_root=0;
    if (exit_code == -10) {
        koronos_target_log("[RUN ] ERROR: in-kernel PIT deadline expired; user process aborted and address space will be reclaimed");
        return -11;
    }
    if (!ready_seen) {
        koronos_target_log("[RUN ] ERROR: userspace init exited before its target-specific USERSPACE READY handshake");
        return -8;
    }
    if (exit_code!=0) {
        koronos_target_log("[RUN ] ERROR: userspace init exited nonzero after readiness");
        return -9;
    }
    koronos_target_log("[RUN ] Target userspace init emitted its own readiness handshake and exited cleanly");
    return 0;
}
