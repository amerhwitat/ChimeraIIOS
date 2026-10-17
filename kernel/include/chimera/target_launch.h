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

#ifdef __cplusplus
}
#endif
