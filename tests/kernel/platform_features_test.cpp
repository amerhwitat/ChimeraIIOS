#include "chimera/platform_features.h"
#include <assert.h>

int main() {
    assert(chimera_platform_init(0) == 0);
    assert(chimera_platform_probe() == 0);
    assert(chimera_platform_state() == CHM_PLATFORM_READY);
    assert(chimera_platform_has(CHM_FEAT_VMEM));
    assert(chimera_platform_has(CHM_FEAT_VFS));
    assert(chimera_platform_has(CHM_FEAT_NET_SOCKETS));
    assert(chimera_platform_has(CHM_FEAT_SECURITY));
    assert(chimera_platform_has(CHM_FEAT_AURORA_COMP));

    assert(chimera_memory_register_region(0x100000, 0x400000, 1, 3) == 0);
    assert(chimera_memory_region_count() == 1);

    chimera_io_request io{};
    io.buffer = 0x200000;
    io.length = 4096;
    assert(chimera_io_submit(&io) == 0);
    assert(io.id != 0);
    assert(chimera_io_pending() == 1);
    assert(chimera_io_complete(io.id, 0) == 0);
    assert(chimera_io_pending() == 0);

    chimera_security_subject subject{};
    subject.subject_id = 7;
    subject.capabilities = 0x5;
    assert(chimera_security_set_subject(&subject) == 0);
    assert(chimera_security_check(&subject, 0x1) == 0);
    assert(chimera_security_check(&subject, 0x2) != 0);

    chimera_net_endpoint ep{};
    ep.family = 2;
    ep.port = 8080;
    ep.protocol = 6;
    assert(chimera_net_register_endpoint(&ep) == 0);
    assert(chimera_net_endpoint_count() == 1);
    assert(chimera_net_remove_endpoint(2, 8080) == 0);

    chimera_display_target display{};
    display.id = 1;
    display.width = 1920;
    display.height = 1080;
    display.refresh_millihz = 60000;
    assert(chimera_display_register(&display) == 0);
    assert(chimera_display_count() == 1);

    chimera_power_state power{};
    power.ac_online = 1;
    power.battery_percent = 100;
    assert(chimera_power_update(&power) == 0);
    chimera_power_state observed{};
    assert(chimera_power_snapshot(&observed) == 0);
    assert(observed.ac_online == 1);

    chimera_platform_snapshot snapshot{};
    assert(chimera_platform_get_snapshot(&snapshot) == 0);
    assert(snapshot.memory_regions == 1);
    assert(snapshot.displays == 1);
    assert(snapshot.security_subjects == 1);
    return 0;
}
