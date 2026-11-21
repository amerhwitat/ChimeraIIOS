#include "chimera/kore.h"
#include <stdint.h>

static void console_service(void*) {}
static void timer_service(void*) {}
static void module_service(void*) {}
static void storage_service(void*) {}
static void live_initramfs_service(void*) {}
static void aurora_service(void*) {}
static void installer_image_service(void*) {}
static void installer_storage_service(void*) {}
static void installer_ui_service(void*) {}
static void security_service(void*) {}

extern "C" void koronos_kore_init(uint32_t cpus, bool installer_mode) {
    kore_init(cpus);
    kore_register_target("koronos.target", 0);
    kore_register_target("hardware.target", 10);
    kore_register_target("runtime.target", 20);
    kore_register_target("live.target", 30);
    kore_register_target("installer.target", 30);
    kore_register_target("complete.target", 40);

    kore_register_service("console.service", console_service, nullptr, 10);
    kore_register_service("timer.service", timer_service, nullptr, 10);
    kore_register_service("module-manager.service", module_service, nullptr, 20);
    kore_register_service("storage.service", storage_service, nullptr, 20);
    kore_register_service("security.service", security_service, nullptr, 20);
    kore_register_service("live-initramfs.service", live_initramfs_service, nullptr, 30);
    kore_register_service("aurora.service", aurora_service, nullptr, 40);
    kore_register_service("installer-image.service", installer_image_service, nullptr, 30);
    kore_register_service("installer-storage.service", installer_storage_service, nullptr, 35);
    kore_register_service("installer-ui.service", installer_ui_service, nullptr, 40);

    kore_add_wants("hardware.target", "console.service");
    kore_add_wants("hardware.target", "timer.service");
    kore_add_wants("hardware.target", "storage.service");
    kore_add_wants("runtime.target", "module-manager.service");
    kore_add_wants("runtime.target", "security.service");
    kore_add_wants("runtime.target", "console.service");
    kore_add_requires("live-initramfs.service", "module-manager.service");
    kore_add_after("live-initramfs.service", "module-manager.service");
    kore_add_requires("aurora.service", "live-initramfs.service");
    kore_add_after("aurora.service", "live-initramfs.service");
    kore_add_requires("installer-image.service", "module-manager.service");
    kore_add_after("installer-image.service", "module-manager.service");
    kore_add_requires("installer-storage.service", "storage.service");
    kore_add_after("installer-storage.service", "storage.service");
    kore_add_requires("installer-ui.service", "installer-image.service");
    kore_add_requires("installer-ui.service", "installer-storage.service");
    kore_add_after("installer-ui.service", "installer-image.service");
    kore_add_after("installer-ui.service", "installer-storage.service");

    kore_add_wants("koronos.target", "hardware.target");
    kore_add_wants("koronos.target", "runtime.target");
    if (installer_mode) {
        kore_add_wants("koronos.target", "installer.target");
        kore_add_wants("installer.target", "installer-image.service");
        kore_add_wants("installer.target", "installer-storage.service");
        kore_add_wants("installer.target", "installer-ui.service");
    } else {
        kore_add_wants("koronos.target", "live.target");
        kore_add_wants("live.target", "live-initramfs.service");
        kore_add_wants("live.target", "aurora.service");
    }
    kore_start_target("koronos.target");
    kore_start_target(installer_mode ? "installer.target" : "live.target");
    kore_dispatch(0);
}
