#include "chimera/driver.h"
#include "chimera/device.h"
#include <stddef.h>

static chimera_driver_descriptor g_drivers[256];
static uint32_t g_count = 0;
static int g_last_probe_count = 0;
static int g_last_probe_failures = 0;

static int match(const chimera_driver_descriptor *d, const chimera_device *x) {
    if (!d || !x) return 0;
    if (d->vendor_id != 0xFFFFu && d->vendor_id != x->vendor_id) return 0;
    if (d->device_id != 0xFFFFu && d->device_id != x->device_id) return 0;
    if (d->match_class && d->match_class != x->class_code) return 0;
    if (d->match_subclass && d->match_subclass != x->subclass) return 0;
    if (d->match_prog_if && d->match_prog_if != x->prog_if) return 0;
    return 1;
}

extern "C" int chimera_driver_register(const chimera_driver_descriptor *d) {
    if (!d || d->abi_version != KORONOS_DRIVER_ABI || !d->name || g_count >= 256)
        return -1;
    g_drivers[g_count++] = *d;
    return 0;
}

extern "C" const chimera_driver_registry *chimera_driver_registry_snapshot() {
    static chimera_driver_registry r{0, 256, g_drivers};
    r.count = g_count;
    return &r;
}

/* A descriptor/catalog match is not a functioning driver. Only a device that
 * passed its real device-specific probe may transition to RUNNING. The probe
 * callback receives the discovered device exactly once, during probe_all. */
extern "C" int chimera_driver_start_all() {
    int started = 0;
    int rejected = 0;
    for (uint32_t i = 0; i < g_count; ++i) {
        chimera_driver_descriptor *d = &g_drivers[i];
        if (d->state != 2 && d->state != 1) continue;
        if (!d->probe || d->state != 2) {
            d->state = 5; /* FAILED/unsupported: no executable driver backend */
            ++rejected;
            continue;
        }
        d->state = 3;
        ++started;
    }
    return rejected ? -2 : started;
}

extern "C" int chimera_driver_probe_all() {
    chimera_device_inventory inv{};
    const int n = chimera_hardware_enumerate_devices(&inv);
    if (n < 0) return n;
    g_last_probe_count = 0;
    g_last_probe_failures = 0;

    for (uint32_t i = 0; i < inv.count; ++i) {
        const chimera_device *x = &inv.devices[i];
        bool matched_candidate = false;
        bool operational = false;
        for (uint32_t j = 0; j < g_count; ++j) {
            chimera_driver_descriptor *d = &g_drivers[j];
            if (!match(d, x)) continue;
            matched_candidate = true;
            if (!d->probe) {
                d->state = 5;
                continue;
            }
            if (d->probe(x) != 0) {
                d->state = 5;
                continue;
            }
            d->state = 2; /* probed; start_all may now mark it running */
            ++g_last_probe_count;
            operational = true;
            break;
        }
        if (!operational) {
            ++g_last_probe_failures;
            if (!matched_candidate) {
                /* Catalog-only compatibility descriptors are explicitly
                 * unavailable until they have an executable probe backend. */
                static chimera_driver_descriptor compat[256];
                static uint32_t cc = 0;
                if (cc < 256) {
                    chimera_driver_descriptor *d = &compat[cc++];
                    *d = {KORONOS_DRIVER_ABI, CHM_BUS_PCI,
                        (x->device_class == CHM_DEV_NETWORK) ? CHM_DRV_NET :
                        (x->device_class == CHM_DEV_STORAGE) ? CHM_DRV_STORAGE :
                        (x->device_class == CHM_DEV_DISPLAY) ? CHM_DRV_DISPLAY :
                        (x->device_class == CHM_DEV_GPU) ? CHM_DRV_GPU :
                        (x->device_class == CHM_DEV_MOTHERBOARD) ? CHM_DRV_PLATFORM : CHM_DRV_USB,
                        0, x->vendor_id, x->device_id, 0, "compatibility-adapter",
                        "catalog-only; no executable backend", "1",
                        static_cast<uint8_t>(x->class_code), static_cast<uint8_t>(x->subclass),
                        static_cast<uint8_t>(x->prog_if), 5, "compatibility-layer", nullptr};
                    (void)chimera_driver_register(d);
                }
            }
        }
    }
    /* Any discovered device without a successful executable probe means the
     * driver layer is degraded; callers must not advertise full readiness. */
    return g_last_probe_failures ? -2 : g_last_probe_count;
}
