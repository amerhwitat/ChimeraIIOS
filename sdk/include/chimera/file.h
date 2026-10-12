#ifndef CHIMERA_FILE_H
#define CHIMERA_FILE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* POSIX-shaped descriptor API. On hosted builds this forwards to the host
 * libc; native Koronos builds must bind these calls to CHM_SYS_* services. */
typedef int32_t chm_fd;
enum chm_open_flags {
    CHM_O_READ_ONLY = 0x0000,
    CHM_O_WRITE_ONLY = 0x0001,
    CHM_O_READ_WRITE = 0x0002,
    CHM_O_CREATE = 0x0040,
    CHM_O_TRUNCATE = 0x0200,
    CHM_O_APPEND = 0x0400
};
chm_fd chm_open(const char *path, int flags, uint32_t mode);
int64_t chm_read(chm_fd fd, void *buffer, size_t count);
int64_t chm_write(chm_fd fd, const void *buffer, size_t count);
int chm_close(chm_fd fd);
int chm_unlink(const char *path);

#ifdef __cplusplus
}
#endif
#endif
