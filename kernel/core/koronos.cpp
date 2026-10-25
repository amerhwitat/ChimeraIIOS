#include "../include/chimera/koronos_abi.h"
#include "chimera/scheduler.h"
#include "chimera/driver.h"
#include "chimera/learning.h"
#include "chimera/multiboot_modules.h"
#include "chimera/frame_allocator.h"
#include "chimera/address_space.h"
#include "chimera/user_entry.h"
#include "chimera/target_launch.h"
#include "chimera/hardware.h"
#include "chimera/device.h"
#include "chimera/firmware.h"
#include "chimera/service.h"
#include "chimera/platform_features.h"
#include "chimera/process.h"

extern "C" void koronos_outb(uint16_t port, uint8_t value);

namespace {
volatile uint32_t koronos_state = 0;
static uint32_t g_system_block_size = KORONOS_SYSTEM_BLOCK_SIZE;
static bool system_block_size_valid(uint32_t size) {
    return size >= KORONOS_SYSTEM_BLOCK_MIN && size <= KORONOS_SYSTEM_BLOCK_MAX && (size & (size - 1u)) == 0u;
}

static uint8_t serial_in8(uint16_t port) {
    uint8_t v;
    __asm__ volatile("inb %1,%0" : "=a"(v) : "Nd"(port));
    return v;
}

static void serial_init() {
    koronos_outb(0x3F9, 0);
    koronos_outb(0x3FB, 0x80);
    koronos_outb(0x3F8, 3);
    koronos_outb(0x3F9, 0);
    koronos_outb(0x3FB, 3);
    koronos_outb(0x3FA, 0xC7);
    koronos_outb(0x3FC, 3);
}

/*
 * COM1 is a diagnostic sink, never a boot/runtime dependency.  Some VMs and
 * physical machines expose the UART but do not drain THR.  The old 100000
 * iteration wait therefore made every kernel log line capable of stalling the
 * cooperative scheduler for a long time.  Bound the poll and drop the byte if
 * the UART is not ready; VGA remains the authoritative early-console path.
 */
static void debugcon_write8(uint8_t v) {
    // Use inline port I/O so early diagnostics do not depend on an outb
    // wrapper, UART readiness, or a platform console being initialized.
    __asm__ volatile("outb %0, $0xE9" : : "a"(v));
}

static void debugcon_write(const char *s) {
    if (!s) return;
    while (*s) debugcon_write8((uint8_t)*s++);
    debugcon_write8('\n');
}

static void serial_write8(uint8_t v) {
    // QEMU/Bochs debugcon (I/O port 0xE9) gives CI a deterministic early-boot
    // trace even when the virtual UART is not configured as a serial sink.
    debugcon_write8(v);
    for (uint32_t i = 0; i < 1024u; ++i) {
        if (serial_in8(0x3FD) & 0x20) {
            koronos_outb(0x3F8, v);
            return;
        }
    }
}

static void serial_write(const char *s) {
    if (!s) return;
    while (*s) serial_write8((uint8_t)*s++);
    serial_write8('\r');
    serial_write8('\n');
}

static void parse_system_block_option(uint64_t info) {
    if (!info) return;
    const auto *base = reinterpret_cast<const uint8_t *>(static_cast<uintptr_t>(info));
    const uint32_t total = *reinterpret_cast<const uint32_t *>(base);
    if (total < 16u || total > 16u * 1024u * 1024u) return;
    for (uint32_t off = 8u; off <= total - 8u;) {
        const auto *tag = reinterpret_cast<const uint32_t *>(base + off);
        const uint32_t type = tag[0], size = tag[1];
        if (size < 8u || size > total - off) return;
        if (type == 0u) return;
        if (type == 1u && size > 8u) {
            const char *cmd = reinterpret_cast<const char *>(base + off + 8u);
            const uint32_t bytes = size - 8u;
            const char key[] = "koronos.system_block=";
            for (uint32_t i = 0; i < bytes && cmd[i];) {
                while (i < bytes && (cmd[i] == ' ' || cmd[i] == '\t')) ++i;
                const uint32_t start = i;
                while (i < bytes && cmd[i] && cmd[i] != ' ' && cmd[i] != '\t') ++i;
                if (i - start < sizeof(key) - 1u) continue;
                bool match = true;
                for (uint32_t k = 0; k < sizeof(key) - 1u; ++k) if (cmd[start + k] != key[k]) { match = false; break; }
                if (!match) continue;
                uint32_t value = 0;
                bool valid = i > start + sizeof(key) - 1u;
                for (uint32_t k = start + sizeof(key) - 1u; k < i; ++k) {
                    if (cmd[k] < '0' || cmd[k] > '9') { valid = false; break; }
                    const uint32_t digit = static_cast<uint32_t>(cmd[k] - '0');
                    if (value > (KORONOS_SYSTEM_BLOCK_MAX - digit) / 10u) { valid = false; break; }
                    value = value * 10u + digit;
                }
                if (valid && system_block_size_valid(value)) g_system_block_size = value;
                else debugcon_write("[BLK] Invalid koronos.system_block value; retaining configured default");
            }
            return;
        }
        const uint64_t next = (static_cast<uint64_t>(off) + size + 7u) & ~7ull;
        if (next <= off || next > total) return;
        off = static_cast<uint32_t>(next);
    }
}

static void vga_clear() {
    volatile uint16_t *v = (volatile uint16_t *)0xB8000;
    for (uint32_t i = 0; i < 80u * 25u; ++i) v[i] = 0x0720;
}

static void vga_scroll(volatile uint16_t *v) {
    for (uint32_t r = 1; r < 25; ++r)
        for (uint32_t c = 0; c < 80; ++c)
            v[(r - 1) * 80 + c] = v[r * 80 + c];
    for (uint32_t c = 0; c < 80; ++c) v[24 * 80 + c] = 0x0720;
}

static void vga_write(const char *s) {
    volatile uint16_t *v = (volatile uint16_t *)0xB8000;
    static uint32_t row = 0, col = 0;
    if (row == 0 && col == 0) vga_clear();
    if (!s) return;
    while (*s) {
        char c = *s++;
        if (c == '\r') {
            col = 0;
            continue;
        }
        if (c == '\n') {
            col = 0;
            if (++row >= 25) {
                vga_scroll(v);
                row = 24;
            }
            continue;
        }
        if (col >= 80) {
            col = 0;
            if (++row >= 25) {
                vga_scroll(v);
                row = 24;
            }
        }
        v[row * 80 + col++] = (uint16_t)(0x0F00u | (uint8_t)c);
    }
}

static void console_write(const char *s) {
    /* Never let a diagnostic UART hold up the visible kernel console. */
    vga_write(s);
    vga_write("\r\n");
    serial_write(s);
}

static void console_raw(const char *s) {
    if (!s) return;
    vga_write(s);
    while (*s) serial_write8((uint8_t)*s++);
}

static void console_endline() {
    vga_write("\r\n");
    serial_write8('\r');
    serial_write8('\n');
}

static void console_u32_raw(uint32_t v) {
    char s[11];
    uint32_t i = 10;
    s[i] = 0;
    if (v == 0) {
        console_raw("0");
        return;
    }
    while (v && i) {
        s[--i] = (char)('0' + v % 10u);
        v /= 10u;
    }
    console_raw(&s[i]);
}

static void console_progress(uint32_t percent, const char *label) {
    if (percent > 100u) percent = 100u;
    const uint32_t filled = (percent * 20u) / 100u;
    console_raw("[PROG] [");
    for (uint32_t i = 0; i < 20u; ++i) console_raw(i < filled ? "#" : "-");
    console_raw("] ");
    console_u32_raw(percent);
    console_raw("% ");
    console_raw(label ? label : "Boot phase");
    console_endline();
}

static void console_u32(uint32_t v) {
    char s[11];
    uint32_t i = 10;
    s[i] = 0;
    if (v == 0) {
        console_write("0");
        return;
    }
    while (v && i) {
        s[--i] = (char)('0' + v % 10u);
        v /= 10u;
    }
    console_write(&s[i]);
}

static void console_hex32(uint32_t v) {
    static const char h[] = "0123456789ABCDEF";
    char s[9];
    for (int i = 7; i >= 0; --i) {
        s[i] = h[v & 15u];
        v >>= 4;
    }
    s[8] = 0;
    console_write(s);
}

static const char *module_kind_name(uint32_t k) {
    switch (k) {
        case CHIMERA_MODULE_LIVE_INITRAMFS: return "LIVE INITRAMFS";
        case CHIMERA_MODULE_LIVE_MANIFEST: return "LIVE MANIFEST";
        case CHIMERA_MODULE_RECOVERY_INITRAMFS: return "RECOVERY INITRAMFS";
        case CHIMERA_MODULE_RECOVERY_MANIFEST: return "RECOVERY MANIFEST";
        case CHIMERA_MODULE_INSTALL_IMAGE: return "INSTALL IMAGE";
        case CHIMERA_MODULE_INSTALL_MANIFEST: return "INSTALL MANIFEST";
        case CHIMERA_MODULE_INSTALL_CONTRACT: return "INSTALL CONTRACT";
        case CHIMERA_MODULE_INSTALL_PHASES: return "INSTALL PHASES";
        case CHIMERA_MODULE_INSTALL_PROFILES: return "INSTALL PROFILES";
        default: return "OTHER";
    }
}

static void console_modules() {
    uint32_t n = chimera_multiboot_module_count();
    console_write("[MB2 ] Module registry: ");
    console_u32(n);
    console_write(" module(s)");
    for (uint32_t i = 0; i < n; ++i) {
        const chimera_boot_module *m = chimera_multiboot_module(i);
        if (!m) continue;
        console_write("[MB2 ] type=");
        console_write(module_kind_name(m->kind));
        console_write("[MB2 ] cmdline=");
        console_write(m->cmdline);
        console_write("[MB2 ] base=");
        console_hex32((uint32_t)m->base);
        console_write("[MB2 ] size=");
        console_hex32((uint32_t)m->size);
    }
}

static volatile uint32_t console_task_runs = 0;
static volatile uint32_t module_task_runs = 0;
static volatile uint32_t live_task_runs = 0;
static volatile uint32_t installer_phase = 0;

static void task_console(void *) {
    if (console_task_runs++ == 0) console_write("[TASK] Console service online");
    // Registration is a one-shot bootstrap action, not a continuously runnable task.
    chimera_sched_block();
}

static void task_modules(void *) {
    if (module_task_runs++ == 0) {
        console_write("[TASK] Module manager online");
        console_modules();
    }
    // Module discovery completes during bootstrap; do not spin in READY forever.
    chimera_sched_block();
}

static void task_live(void *) {
    if (live_task_runs++ == 0) {
        if (chimera_multiboot_find(CHIMERA_MODULE_USER_INIT_ELF)) {
            const int launch_rc = koronos_launch_selected_userspace();
            if (launch_rc != 0)
                console_write("[RUN ] Selected userspace target failed its launch/readiness acceptance gate");
            chimera_sched_block();
            return;
        }
        const chimera_boot_module *m = chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS);
        if (m) {
            console_write("[LIVE] Live initramfs module recognized");
            const int launch_rc = koronos_launch_selected_userspace();
            if (launch_rc != 0)
                console_write("[RUN ] Live target init failed before readiness; failing closed");
            chimera_sched_block();
        } else if (!chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE)) {
            console_write("[LIVE] No live initramfs module; live service idle");
            chimera_sched_block();
        } else {
            // Installer media is handled by task_installer. There is no live
            // payload to launch in this target, so the live service blocks.
            console_write("[LIVE] Installer target detected; live service idle");
            chimera_sched_block();
        }
    }
}

static void task_recovery(void *) {
    const chimera_boot_module *image = chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS);
    if (image) {
        console_write("[REC ] Recovery initramfs module recognized");
        const int launch_rc = koronos_launch_selected_userspace();
        if (launch_rc != 0)
            console_write("[RUN ] Recovery target init failed before readiness; failing closed");
    } else {
        console_write("[REC ] Recovery target not selected: no recovery initramfs module");
    }
    chimera_sched_block();
}

static void task_installer(void *) {
    const chimera_boot_module *image = chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE);
    const chimera_boot_module *manifest = chimera_multiboot_find(CHIMERA_MODULE_INSTALL_MANIFEST);
    const chimera_boot_module *contract = chimera_multiboot_find(CHIMERA_MODULE_INSTALL_CONTRACT);
    const chimera_boot_module *phases = chimera_multiboot_find(CHIMERA_MODULE_INSTALL_PHASES);
    const chimera_boot_module *profiles = chimera_multiboot_find(CHIMERA_MODULE_INSTALL_PROFILES);

    if (!image && !manifest && !contract && !phases && !profiles) {
        if (installer_phase++ == 0)
            console_write("[INST] Installer target not selected: no installer modules");
        chimera_sched_block();
        return;
    }

    if (image) {
        const int launch_rc = koronos_launch_selected_userspace();
        if (launch_rc != 0) {
            console_write("[RUN ] Installer target init failed before readiness; failing closed");
            chimera_sched_block();
            return;
        }
    }

    switch (installer_phase++) {
        case 0:
            console_write("[INST] Installer target detected");
            if (image) console_write("[INST] Installation image accepted");
            else console_write("[INST] ERROR: installation image module missing");
            if (manifest) console_write("[INST] Installation manifest accepted");
            else console_write("[INST] WARNING: installation manifest module missing");
            if (contract) console_write("[INST] Installer contract accepted");
            else console_write("[INST] WARNING: installer contract module missing");
            break;
        case 1:
            console_write("[INST] Installer runtime initialization");
            console_write("[INST] Initializing installer services in parallel");
            break;
        case 2:
            console_write("[INST] Hardware discovery service started");
            console_write("[INST] Storage discovery service started");
            break;
        case 3:
            if (phases) console_write("[INST] Installation phases loaded");
            if (profiles) console_write("[INST] Installer profiles loaded");
            console_write("[INST] Installer UI scaffolding initialized; graphical userspace is not running");
            break;
        case 4:
            console_write("[INST] Installer metadata/service scaffolding complete; install execution is not verified");
            console_write("[USER] Installer handoff withheld: production payload has no supported native init ELF/runtime");
            chimera_sched_block();
            break;
        default:
            chimera_sched_block();
            break;
    }
}

static const char *task_state_name(uint32_t state) {
    switch (state) {
        case CHIMERA_TASK_READY: return "READY";
        case CHIMERA_TASK_RUNNING: return "RUNNING";
        case CHIMERA_TASK_BLOCKED: return "BLOCKED";
        case CHIMERA_TASK_EXITED: return "EXITED";
        default: return "UNKNOWN";
    }
}

static void task_monitor(void *) {
    static uint32_t ticks = 0;
    // The scheduler is a tight cooperative loop; sampling every 10 dispatches
    // floods VGA/serial output and makes a healthy kernel look hung. Keep the
    // monitor live, but emit a full snapshot only once per 1000 monitor runs.
    // This is currently a diagnostic snapshot, not a timer-driven service.
    // Emit it once; repeated polling here floods VGA/serial and obscures the
    // actual handoff state. A timer/event source can wake a periodic monitor later.
    if (++ticks > 1u) { chimera_sched_block(); return; }
    chimera_task_info info[32]{};
    uint32_t n = chimera_sched_snapshot(info, 32);
    console_write("[MON ] ===== REAL-TIME KORONOS TASKS =====");
    console_write("[MON ] CPUs: ");
    console_u32(chimera_sched_cpu_count());
    console_write("[MON ] Runnable: ");
    console_u32(chimera_sched_runnable_count());
    for (uint32_t i = 0; i < n; ++i) {
        // Keep each process record on one VGA/serial line. The previous
        // label/value-per-line format made the monitor look corrupted once
        // the 25-row VGA console started scrolling.
        console_raw("[PROC] id=");
        console_u32_raw(info[i].id);
        console_raw(" cpu=");
        console_u32_raw(info[i].cpu);
        console_raw(" state=");
        console_raw(task_state_name(info[i].state));
        console_raw(" priority=");
        console_u32_raw(info[i].priority);
        console_raw(" runs=");
        console_u32_raw((uint32_t)info[i].runs);
        console_endline();
    }
}

static void task_kore(void *) {
    static bool started = false;
    if (!started) {
        started = true;
        chimera_kore_bootstrap();
        console_write("[KORE] Service orchestration online");
        console_write("[KORE] Storage/device/security services BLOCKED pending implementation health checks");
        console_write("[KORE] Registry initialized; service registration is not service readiness");
    }
    // Bootstrap orchestration is complete; a service worker must block until
    // an event source wakes it rather than consume every scheduler dispatch.
    chimera_sched_block();
}

static void koronos_submit_bootstrap_tasks() {
    int a = chimera_sched_submit(task_console, 0, 100);
    int b = chimera_sched_submit(task_modules, 0, 90);
    int c = chimera_sched_submit(task_live, 0, 80);
    int d = chimera_sched_submit(task_installer, 0, 80);
    int e = chimera_sched_submit(task_kore, 0, 95);
    int r = chimera_sched_submit(task_recovery, 0, 80);
    int m = chimera_sched_submit(task_monitor, 0, 60);
    console_write("[SCH ] Bootstrap tasks submitted");
    console_write("[SCH ] console/module/live/installer/recovery/Kore services registered");
    if (a < 0 || b < 0 || c < 0 || d < 0 || e < 0 || r < 0 || m < 0)
        console_write("[SCH ] WARNING: bootstrap task registration incomplete");
}
}

extern "C" void chimera_register_virtio_drivers(void);
extern "C" void chimera_register_display_drivers(void);
extern "C" void chimera_register_pci_generic_drivers(void);

extern "C" int64_t koronos_console_write_user(uint64_t address, uint64_t length) {
    if (length == 0) return 0;
    if (length > 4096u) return -22;
    /* Never dereference a ring-3 pointer from the console/syscall path. The
       shared helper validates and pins the active process's own address space,
       then copies into kernel-owned memory before diagnostics inspect bytes. */
    uint8_t kernel_buffer[4096];
    if (koronos_target_copy_from_user(kernel_buffer, address, length) != 0) return -14;
    (void)koronos_target_note_user_write(reinterpret_cast<const char *>(kernel_buffer), length);
    for (uint64_t i = 0; i < length; ++i) debugcon_write8(kernel_buffer[i]);
    return static_cast<int64_t>(length);
}

extern "C" void koronos_target_log(const char *message) {
    if (!message) return;
    debugcon_write(message);
    console_write(message);
}

extern "C" void koronos_boot(const koronos_boot_context *ctx) {
    debugcon_write("[KRN ] koronos_boot entered");
    serial_init();
    console_write("CHIMERA II OS / KORONOS");
    console_write("[BOOT] Boot handoff: ");
    if (!ctx || ctx->magic != KORONOS_BOOTINFO_MAGIC || ctx->version != KORONOS_ABI_VERSION) {
        koronos_state = 0xBAD00001u;
        console_write("INVALID BOOT CONTEXT");
        return;
    }

    console_write("OK");
    parse_system_block_option(ctx->boot_info);
    console_raw("[BLK ] System block size (bytes): ");
    console_u32_raw(g_system_block_size);
    console_endline();
    console_write("[BLK ] Override with GRUB option koronos.system_block=<512..65536 power of two>");
    console_progress(5, "Koronos boot context accepted");
    console_write("[HW  ] Initializing hardware...");
    uint32_t modules = chimera_multiboot_scan(ctx->boot_info);
    console_write("[MB2 ] Scanned Multiboot2 modules");
    const int frame_init = koronos_frame_allocator_init(ctx->boot_info, ctx->kernel_base, ctx->kernel_end);
    if (frame_init == 0) {
        console_write("[MM  ] Physical frame allocator initialized; free 4 KiB frames: ");
        console_u32(static_cast<uint32_t>(koronos_frame_free_count()));
    } else {
        console_write("[MM  ] ERROR: physical frame allocator initialization failed");
        console_write("[MM  ] User-image launch must remain disabled until memory ownership is valid");
    }
    console_progress(15, "Multiboot2 modules scanned");
    console_write("[MB2 ] Count: ");
    console_u32(modules);
    koronos_arch_init(ctx);
    const int address_space_init = (frame_init == 0) ? koronos_address_space_init() : -1;
    const int address_space_test = (address_space_init == 0) ? koronos_address_space_self_test() : -1;
    const int user_entry_init = (address_space_test == 0) ? koronos_user_entry_init() : -1;
    if (address_space_test == 0 && user_entry_init == 0) {
        console_write("[MM  ] Process page-table self-test passed: kernel identity mappings preserved; user U/RW/NX permissions verified; frames reclaimed");
        console_write("[ARCH] GDT/TSS RSP0 and native SYSCALL entry initialized; user-image launch remains gated on target payload acceptance");
        console_write("[MM  ] User virtual addresses must begin at or above 4 GiB to avoid the bootstrap identity map");
    } else {
        console_write("[MM  ] ERROR: process address-space or ring-3 entry setup failed; user-image launch remains disabled");
    }
    console_progress(25, "Architecture discovery and address-space safety checks complete");

    const struct koronos_cpu_features *f = koronos_get_cpu_features();
    console_write("[CPU ] ");
    console_write(f->vendor);
    console_write("[CPU ] Logical CPUs: ");
    console_hex32(f->logical_cpus);
    console_write("[VM  ] Hypervisor detected: ");
    console_hex32(f->hypervisor);

    console_write("[SCH ] Initializing scheduler...");
    // CPUID reports possible/logical processors, not processors that Koronos
    // has actually brought online. Until AP startup and per-CPU scheduler
    // state are implemented, CPU0 is the only schedulable CPU. Passing the
    // detected count here can assign runnable work to offline CPUs and stall
    // the bootstrap/userspace handoff.
    constexpr uint32_t online_scheduler_cpus = 1;
    console_write("[SCH ] Online scheduler CPUs: 1 (AP startup not implemented)");
    chimera_sched_init(online_scheduler_cpus);
    chimera_learning_init(online_scheduler_cpus);
    console_progress(35, "Scheduler and learning runtime initialized");

    console_write("[IO  ] Initializing virtual I/O drivers...");
    chimera_register_virtio_drivers();
    chimera_register_display_drivers();
    chimera_register_pci_generic_drivers();
    console_progress(45, "Display and PCI driver registries populated");

    chimera_hardware_profile hw{};
    if (chimera_hardware_probe(&hw) == 0) {
        console_write("[HW  ] Architecture profile ready");
        console_write("[HW  ] Native N-bit mode: ");
        console_u32(hw.native_nbit_mode);
        console_write("[HW  ] Best N-bit mode: ");
        console_u32(hw.best_nbit_mode);
    }

    chimera_firmware_profile fw{};
    if (chimera_firmware_probe(ctx, &fw) == 0) {
        console_write("[FW  ] Firmware: ");
        console_write(fw.type == CHIMERA_FW_UEFI ? "UEFI" :
                      fw.type == CHIMERA_FW_BIOS ? "BIOS" : "UNKNOWN");
        console_write("[FW  ] ACPI present: ");
        console_write(fw.acpi_rsdp ? "yes" : "no");
        console_write("[FW  ] SMBIOS present: ");
        console_write(fw.smbios_entry ? "yes" : "no");
        console_write("[FW  ] UEFI system table: ");
        console_write(fw.efi_system_table ? "present" : "absent");
    }

    chimera_device_inventory inv{};
    int devices = chimera_hardware_enumerate_devices(&inv);
    console_write("[PCI ] Enumerated devices: ");
    console_progress(55, "Hardware inventory enumerated");
    console_u32(devices < 0 ? 0 : (uint32_t)devices);

    int bound = chimera_driver_probe_all();
    console_write("[DRV ] Native/compatible bindings: ");
    console_u32(bound);
    int running = chimera_driver_start_all();
    console_write("[DRV ] Active driver set: ");
    console_progress(65, "Driver probing and start requests completed");
    console_u32(running);

    chimera_platform_init(0);
    chimera_platform_probe();
    chimera_platform_snapshot platform_snapshot{};
    chimera_platform_get_snapshot(&platform_snapshot);

    chimera_learning_record(1, f->logical_cpus);
    koronos_elf64_init();
    chimera_process_init();
    console_write("[PROC] Protected-process admission layer ready (load-plan mode)");
    console_progress(75, "Process admission and module registries initialized");
    koronos_module_init();
    koronos_state = 0x4B4F524Fu;
    console_write("[PLT ] Native platform feature registry ready");
    debugcon_write("[KRN ] KORONOS READY");
    console_write("[KRN ] KORONOS READY");
    console_write("[IO  ] Console: VGA text + COM1");
    koronos_submit_bootstrap_tasks();
    console_progress(90, "Bootstrap services registered");
    console_write("[RUN ] Starting cooperative scheduler runtime...");
    console_write("[RUN ] Scheduler now has runnable bootstrap tasks");
    console_write("[RUN ] Entering Koronos scheduler loop");
    console_progress(100, "Kernel initialization complete; scheduler loop entered (not desktop readiness)");
}

extern "C" uint32_t koronos_system_block_size_get(void) { return g_system_block_size; }
