#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Called by the live/bootstrap scheduler task. Returns 0 only when no target
   ELF was selected or when the selected init exited after its own readiness
   handshake; negative values describe an explicit launch/acceptance failure. */
int koronos_launch_selected_userspace(void);
int koronos_target_note_user_write(const char *bytes, uint64_t length);
uint32_t koronos_target_userspace_ready(void);
/* Returns the kernel-owned PID only while a selected target process is active. */
uint32_t koronos_target_active_pid(void);
/* Acknowledges a syscall only when its saved user RIP and active CR3 match
   the currently launched process. Returns that process PID, otherwise zero. */
uint32_t koronos_target_note_user_syscall(uint64_t user_rip, uint64_t user_cs);
/* Context validation for SYSCALL, which does not save the caller CS. */
uint32_t koronos_target_validate_syscall_context(uint64_t user_rip);

#ifdef __cplusplus
}
#endif

/* Parse the PID printed by the active init without accepting uint32 wraparound.
   The kernel-owned PID is nonzero; a longer decimal string must not alias it. */
static inline int chimera_target_marker_pid_matches(
    const char *bytes, uint64_t length,
    const char *prefix, uint64_t prefix_len, uint32_t pid) {
    if (!bytes || !prefix || !prefix_len || !pid ||
        prefix_len > length || length - prefix_len < 2u)
        return 0;

    const uint64_t candidate_starts = length - prefix_len;
    for (uint64_t i = 0; i < candidate_starts; ++i) {
        uint64_t j = 0;
        while (j < prefix_len && bytes[i + j] == prefix[j]) ++j;
        if (j != prefix_len) continue;

        uint64_t k = i + prefix_len;
        uint32_t parsed = 0;
        uint64_t digits = 0;
        int overflow = 0;
        while (k < length && bytes[k] >= '0' && bytes[k] <= '9') {
            const uint32_t digit = (uint32_t)(bytes[k] - '0');
            if (!overflow) {
                if (parsed > (0xffffffffu - digit) / 10u) {
                    overflow = 1;
                } else {
                    parsed = parsed * 10u + digit;
                }
            }
            ++k;
            ++digits;
        }

        if (!overflow && digits && parsed == pid &&
            (k == length || bytes[k] == '\n' ||
             bytes[k] == '\r' || bytes[k] == ' '))
            return 1;
    }
    return 0;
}
