#include "chimera/driver.h"
#include "chimera/device.h"
#include <stddef.h>

static chimera_driver_descriptor g_drivers[256];
static uint32_t g_count = 0;
static int g_last_probe_count = 0;

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

extern "C" int chimera_driver_start_all() {
    int started = 0;
    for (uint32_t i = 0; i < g_count; ++i) {
        chimera_driver_descriptor *d = &g_drivers[i];
        /* Probe requires the actual device; never call it with nullptr. */
        if (d->state == 2) {
            d->state = 3;
            ++started;
        }
    }
    return started;
}

extern "C" int chimera_driver_probe_all() {
    chimera_device_inventory inv{};
    const int n = chimera_hardware_enumerate_devices(&inv);
    if (n < 0) return n;

    g_last_probe_count = 0;
    for (uint32_t i = 0; i < inv.count; ++i) {
        const chimera_device *x = &inv.devices[i];
        for (uint32_t j = 0; j < g_count; ++j) {
            chimera_driver_descriptor *d = &g_drivers[j];
            if (!match(d, x)) continue;

            /* An ID match is only a candidate. A missing probe callback is
             * not evidence of a usable driver; a rejecting probe must not
             * mask later matching candidates. */
            if (!d->probe) continue;
            if (d->probe(x) != 0) {
                d->state = 5; /* rejected/failed candidate */
                continue;
            }

            d->state = 2; /* probe passed; eligible for start */
            ++g_last_probe_count;
            break;
        }
        /* Unknown devices remain inventory records for diagnostics and the
         * userspace driver assistant. Never fabricate a compatibility driver
         * or claim that a Linux/Windows catalog entry is an executable driver. */
    }
    return g_last_probe_count;
}
