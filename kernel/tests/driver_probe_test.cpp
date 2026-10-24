#include "chimera/driver.h"
#include "chimera/device.h"
#include <cassert>

static unsigned failed_calls = 0;
static unsigned successful_calls = 0;

static int failing_probe(const void *device) {
    assert(device != nullptr);
    ++failed_calls;
    return -1;
}

static int successful_probe(const void *device) {
    assert(device != nullptr);
    ++successful_calls;
    return 0;
}

/* The test exercises the injectable inventory API, not privileged PCI I/O. */
extern "C" int chimera_hardware_enumerate_devices(chimera_device_inventory *) {
    return -1;
}

int main() {
    const chimera_driver_descriptor failed{
        KORONOS_DRIVER_ABI, CHM_BUS_PCI, CHM_DRV_STORAGE, 0,
        0x1AF4, 0x1001, 0, "failing-storage-probe", "test", "1",
        0, 0, 0, 0, "test", failing_probe
    };
    const chimera_driver_descriptor successful{
        KORONOS_DRIVER_ABI, CHM_BUS_PCI, CHM_DRV_STORAGE, 0,
        0x1AF4, 0x1001, 0, "working-storage-probe", "test", "1",
        0, 0, 0, 0, "test", successful_probe
    };
    const chimera_driver_descriptor catalog_only{
        KORONOS_DRIVER_ABI, CHM_BUS_PCI, CHM_DRV_STORAGE, 0,
        0x1234, 0x5678, 0, "catalog-only-storage", "catalog", "1",
        0, 0, 0, 0, "test", nullptr
    };
    assert(chimera_driver_register(&failed) == 0);
    assert(chimera_driver_register(&successful) == 0);
    assert(chimera_driver_register(&catalog_only) == 0);

    chimera_device_inventory inventory{};
    inventory.count = 2;
    inventory.devices[0].vendor_id = 0x1AF4;
    inventory.devices[0].device_id = 0x1001;
    inventory.devices[0].device_class = CHM_DEV_STORAGE;
    inventory.devices[0].class_code = 1;
    inventory.devices[1].vendor_id = 0x1234;
    inventory.devices[1].device_id = 0x5678;
    inventory.devices[1].device_class = CHM_DEV_STORAGE;
    inventory.devices[1].class_code = 1;

    /* A failed candidate is not success; probing continues to a working match.
       A catalogue-only entry must not be counted as an executable driver. */
    assert(chimera_driver_probe_inventory(&inventory) == 1);
    assert(failed_calls == 1);
    assert(successful_calls == 1);

    const chimera_driver_registry *registry = chimera_driver_registry_snapshot();
    assert(registry != nullptr);
    assert(registry->count >= 3);
    assert(registry->entries[0].state == 5);
    assert(registry->entries[1].state == 2);
    assert(registry->entries[2].state == 5);

    /* start_all must not re-call probe with nullptr or start unprobed entries. */
    assert(chimera_driver_start_all() == 1);
    assert(successful_calls == 1);
    assert(registry->entries[1].state == 3);
    assert(registry->entries[0].state == 5);
    assert(registry->entries[2].state == 5);
    return 0;
}
