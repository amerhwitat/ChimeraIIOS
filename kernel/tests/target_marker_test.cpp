#include <cassert>
#include <cstdint>
#include "chimera/target_launch.h"

int main() {
    static constexpr char live_prefix[] =
        "USERSPACE READY: target=live init_pid=";
    static constexpr char recovery_prefix[] =
        "USERSPACE READY: recovery init pid=";

    const char valid[] = "USERSPACE READY: target=live init_pid=123\n";
    assert(chimera_target_marker_pid_matches(
        valid, sizeof(valid) - 1u, live_prefix, sizeof(live_prefix) - 1u, 123u));
    assert(!chimera_target_marker_pid_matches(
        valid, sizeof(valid) - 1u, live_prefix, sizeof(live_prefix) - 1u, 124u));

    /* 2^32 + 123 used to wrap to PID 123 and falsely satisfy correlation. */
    const char wrapped[] = "USERSPACE READY: target=live init_pid=4294967419\n";
    assert(!chimera_target_marker_pid_matches(
        wrapped, sizeof(wrapped) - 1u, live_prefix, sizeof(live_prefix) - 1u, 123u));

    const char max_pid[] = "USERSPACE READY: target=live init_pid=4294967295\n";
    assert(chimera_target_marker_pid_matches(
        max_pid, sizeof(max_pid) - 1u, live_prefix, sizeof(live_prefix) - 1u, 0xffffffffu));

    const char overflow[] = "USERSPACE READY: target=live init_pid=4294967296\n";
    assert(!chimera_target_marker_pid_matches(
        overflow, sizeof(overflow) - 1u, live_prefix, sizeof(live_prefix) - 1u, 0xffffffffu));

    const char zero_pid[] = "USERSPACE READY: target=live init_pid=0\n";
    assert(!chimera_target_marker_pid_matches(
        zero_pid, sizeof(zero_pid) - 1u, live_prefix, sizeof(live_prefix) - 1u, 0u));

    const char bad_boundary[] = "USERSPACE READY: target=live init_pid=123x\n";
    assert(!chimera_target_marker_pid_matches(
        bad_boundary, sizeof(bad_boundary) - 1u, live_prefix, sizeof(live_prefix) - 1u, 123u));

    const char legacy[] = "USERSPACE READY: recovery init pid=42\r\n";
    assert(chimera_target_marker_pid_matches(
        legacy, sizeof(legacy) - 1u, recovery_prefix, sizeof(recovery_prefix) - 1u, 42u));
    return 0;
}
