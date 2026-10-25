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
void *koronos_target_active_address_space(void);
/* Copy syscall data through checked, pinned mappings in the active process
   address space. A nonzero length must fit the supported user range and all
   pages must have the requested permission before any byte is touched. */
int koronos_target_copy_from_user(void *destination, uint64_t source, uint64_t length);
int koronos_target_copy_to_user(uint64_t destination, const void *source, uint64_t length);
/* Acknowledges a syscall only when its saved user RIP and active CR3 match
   the currently launched process. Returns that process PID, otherwise zero. */
uint32_t koronos_target_note_user_syscall(uint64_t user_rip, uint64_t user_cs);
/* Context validation for SYSCALL, which does not save the caller CS. */
uint32_t koronos_target_validate_syscall_context(uint64_t user_rip);

#ifdef __cplusplus
}
#endif
