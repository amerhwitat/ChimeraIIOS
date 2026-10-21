#include "chimera/driver.h"
#include "chimera/device.h"
#include <stdio.h>
#include <string.h>

static int probe_calls;
extern "C" int chimera_hardware_enumerate_devices(chimera_device_inventory *out) {
    if (!out) return -1;
    memset(out, 0, sizeof(*out));
    out->count = 1;
    out->devices[0].bus = CHM_BUS_PCI;
    out->devices[0].vendor_id = 0x1AF4;
    out->devices[0].device_id = 0x1001;
    out->devices[0].class_code = 1;
    out->devices[0].device_class = CHM_DEV_STORAGE;
    return 1;
}
extern "C" const chimera_device_inventory *chimera_hardware_inventory(void) { return nullptr; }
extern "C" int chimera_hardware_device_class(uint8_t, uint8_t) { return CHM_DEV_STORAGE; }

static int real_probe(const void *device) {
    if (!device) return -1;
    const chimera_device *d = static_cast<const chimera_device *>(device);
    ++probe_calls;
    return (d->vendor_id == 0x1AF4 && d->device_id == 0x1001) ? 0 : -1;
}
static int fail(const char *message) { fprintf(stderr, "FAIL: %s\n", message); return 1; }

int main() {
    /* A catalog entry with no probe callback must never be promoted to RUNNING. */
    chimera_driver_descriptor catalog_only{
        KORONOS_DRIVER_ABI, CHM_BUS_VIRTIO, CHM_DRV_STORAGE, 0,
        0x1AF4, 0x1001, 0, "virtio-blk-catalog-only", "none", "1",
        0, 0, 0, 0, "test", nullptr
    };
    if (chimera_driver_register(&catalog_only) != 0) return fail("register catalog-only descriptor");
    if (chimera_driver_probe_all() >= 0) return fail("missing executable backend was not reported");
    if (chimera_driver_start_all() >= 0) return fail("start_all accepted a descriptor without probe");
    const chimera_driver_registry *registry = chimera_driver_registry_snapshot();
    if (!registry || registry->count != 1 || registry->entries[0].state != 5)
        return fail("catalog-only descriptor was not marked FAILED");

    /* A device-specific successful probe is the only route to RUNNING. */
    chimera_driver_descriptor executable{
        KORONOS_DRIVER_ABI, CHM_BUS_VIRTIO, CHM_DRV_STORAGE, 0,
        0x1AF4, 0x1001, 0, "virtio-blk-probe-test", "test", "1",
        0, 0, 0, 0, "test", real_probe
    };
    if (chimera_driver_register(&executable) != 0) return fail("register executable probe");
    if (chimera_driver_probe_all() != 1) return fail("real probe was not accepted");
    if (probe_calls != 1) return fail("probe was not called exactly once with the device");
    if (chimera_driver_start_all() < 0) return fail("probed driver failed start");
    registry = chimera_driver_registry_snapshot();
    if (registry->entries[1].state != 3) return fail("successfully probed driver not RUNNING");
    puts("PASS: catalog-only drivers fail closed; only successful device probes can become RUNNING");
    return 0;
}
