#include "chimera/driver.h"
#include "chimera/device.h"
#include <cassert>
#include <cstring>

static chimera_device_inventory inventory{};
static int reject_calls = 0;
static int accept_calls = 0;
static int null_device_calls = 0;

extern "C" int chimera_hardware_enumerate_devices(chimera_device_inventory *out) {
    if (!out) return -1;
    *out = inventory;
    return static_cast<int>(out->count);
}
static int reject_probe(const void *device) {
    if (!device) ++null_device_calls;
    ++reject_calls;
    return -1;
}
static int accept_probe(const void *device) {
    if (!device) { ++null_device_calls; return -1; }
    ++accept_calls;
    return 0;
}
static int unprobed_callback(const void *device) {
    if (!device) ++null_device_calls;
    return 0;
}
int main() {
    inventory.count = 2;
    inventory.devices[0].vendor_id = 0x1234;
    inventory.devices[0].device_id = 0x5678;
    inventory.devices[0].class_code = 1;
    inventory.devices[1].vendor_id = 0x1111;
    inventory.devices[1].device_id = 0x2222;
    inventory.devices[1].class_code = 2;

    chimera_driver_descriptor reject{
        KORONOS_DRIVER_ABI, CHM_BUS_PCI, CHM_DRV_STORAGE, 0,
        0x1234, 0x5678, 0, "reject-first", "", "test",
        0, 0, 0, 1, "test", reject_probe
    };
    chimera_driver_descriptor accept{
        KORONOS_DRIVER_ABI, CHM_BUS_PCI, CHM_DRV_STORAGE, 0,
        0x1234, 0x5678, 0, "accept-second", "", "test",
        0, 0, 0, 1, "test", accept_probe
    };
    chimera_driver_descriptor no_probe{
        KORONOS_DRIVER_ABI, CHM_BUS_PCI, CHM_DRV_NET, 0,
        0xFFFF, 0xFFFF, 0, "no-probe", "", "test",
        0, 0, 0, 1, "test", nullptr
    };
    chimera_driver_descriptor unprobed{
        KORONOS_DRIVER_ABI, CHM_BUS_PCI, CHM_DRV_NET, 0,
        0x1111, 0x2222, 0, "callback-not-a-probe", "", "test",
        0, 0, 0, 1, "test", unprobed_callback
    };
    assert(chimera_driver_register(&reject) == 0);
    assert(chimera_driver_register(&accept) == 0);
    assert(chimera_driver_register(&no_probe) == 0);
    assert(chimera_driver_register(&unprobed) == 0);

    assert(chimera_driver_probe_all() == 1);
    assert(reject_calls == 1 && accept_calls == 1);
    const chimera_driver_registry *registry = chimera_driver_registry_snapshot();
    assert(registry && registry->count == 4);
    assert(registry->entries[0].state == 5);
    assert(registry->entries[1].state == 2);
    assert(registry->entries[2].state == 1);
    assert(registry->entries[3].state == 2);
    assert(chimera_driver_start_all() == 2);
    assert(registry->entries[1].state == 3);
    assert(registry->entries[3].state == 3);
    assert(null_device_calls == 0);
    return 0;
}
