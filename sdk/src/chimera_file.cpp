#include "chimera/file.h"

#include <cerrno>
#include <fcntl.h>
#include <unistd.h>

extern "C" chm_fd chm_open(const char *path, int flags, uint32_t mode) {
    if (!path) { errno = EINVAL; return -1; }
    int host_flags = 0;
    switch (flags & 3) {
        case CHM_O_READ_ONLY: host_flags |= O_RDONLY; break;
        case CHM_O_WRITE_ONLY: host_flags |= O_WRONLY; break;
        case CHM_O_READ_WRITE: host_flags |= O_RDWR; break;
        default: errno = EINVAL; return -1;
    }
    if (flags & CHM_O_CREATE) host_flags |= O_CREAT;
    if (flags & CHM_O_TRUNCATE) host_flags |= O_TRUNC;
    if (flags & CHM_O_APPEND) host_flags |= O_APPEND;
    return ::open(path, host_flags, static_cast<mode_t>(mode));
}
extern "C" int64_t chm_read(chm_fd fd, void *buffer, size_t count) {
    if (!buffer && count) { errno = EINVAL; return -1; }
    return static_cast<int64_t>(::read(fd, buffer, count));
}
extern "C" int64_t chm_write(chm_fd fd, const void *buffer, size_t count) {
    if (!buffer && count) { errno = EINVAL; return -1; }
    return static_cast<int64_t>(::write(fd, buffer, count));
}
extern "C" int chm_close(chm_fd fd) { return ::close(fd); }
extern "C" int chm_unlink(const char *path) {
    if (!path) { errno = EINVAL; return -1; }
    return ::unlink(path);
}
