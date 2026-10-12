#include "chimera/file.h"

#include <cerrno>
#include <climits>
#ifdef _WIN32
#  include <io.h>
#  include <fcntl.h>
#  include <sys/stat.h>
#  define CHM_HOST_OPEN _open
#  define CHM_HOST_READ _read
#  define CHM_HOST_WRITE _write
#  define CHM_HOST_CLOSE _close
#  define CHM_HOST_UNLINK _unlink
#else
#  include <fcntl.h>
#  include <unistd.h>
#  define CHM_HOST_OPEN open
#  define CHM_HOST_READ read
#  define CHM_HOST_WRITE write
#  define CHM_HOST_CLOSE close
#  define CHM_HOST_UNLINK unlink
#endif

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
#ifdef _WIN32
    return CHM_HOST_OPEN(path, host_flags | _O_BINARY, static_cast<int>(mode));
#else
    return CHM_HOST_OPEN(path, host_flags, static_cast<mode_t>(mode));
#endif
}
extern "C" int64_t chm_read(chm_fd fd, void *buffer, size_t count) {
    if (!buffer && count) { errno = EINVAL; return -1; }
#ifdef _WIN32
    if (count > static_cast<size_t>(INT_MAX)) { errno = EINVAL; return -1; }
#endif
    return static_cast<int64_t>(CHM_HOST_READ(fd, buffer, count));
}
extern "C" int64_t chm_write(chm_fd fd, const void *buffer, size_t count) {
    if (!buffer && count) { errno = EINVAL; return -1; }
#ifdef _WIN32
    if (count > static_cast<size_t>(INT_MAX)) { errno = EINVAL; return -1; }
#endif
    return static_cast<int64_t>(CHM_HOST_WRITE(fd, buffer, count));
}
extern "C" int chm_close(chm_fd fd) { return CHM_HOST_CLOSE(fd); }
extern "C" int chm_unlink(const char *path) {
    if (!path) { errno = EINVAL; return -1; }
    return CHM_HOST_UNLINK(path);
}
