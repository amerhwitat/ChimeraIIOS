#pragma once
#include <stdint.h>
#include "chimera/vfs.h"
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_PROCESS_FD_ABI 1u
#define KORONOS_PROCESS_FD_PROCESSES 128u
#define KORONOS_PROCESS_FD_MAX 32u
/* Kernel-buffer API only. Callers must validate/copy CPL3 memory separately. */
int koronos_process_fd_init(void);
int koronos_process_fd_open(uint32_t pid, const char *kernel_path, uint32_t flags);
int64_t koronos_process_fd_read(uint32_t pid, int fd, void *kernel_buffer, uint64_t length);
int64_t koronos_process_fd_write(uint32_t pid, int fd, const void *kernel_buffer, uint64_t length);
int64_t koronos_process_fd_seek(uint32_t pid, int fd, int64_t offset, uint32_t whence);
int koronos_process_fd_close(uint32_t pid, int fd);
int koronos_process_fd_close_all(uint32_t pid);
uint32_t koronos_process_fd_count(uint32_t pid);
#ifdef __cplusplus
}
#endif
