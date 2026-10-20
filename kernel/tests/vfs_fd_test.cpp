#include "chimera/vfs_fd.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
int main() {
    chimera_vfs fs{}; chimera_vfs_node nodes[4]{}; uint8_t storage[256]{};
    assert(chimera_vfs_init(&fs, nodes, 4, storage, sizeof(storage), 64) == 0);
    chimera_vfs_fd fds[8]{}; assert(chimera_vfs_fd_init(fds, 8) == 0);
    int fd = chimera_vfs_open(fds, 8, &fs, 7, 1000, 100, "/docs/file.txt",
                              CHIMERA_FD_READ | CHIMERA_FD_WRITE | CHIMERA_FD_CREATE);
    assert(fd >= 0);
    const char s[] = "abc";
    assert(chimera_vfs_fd_write(fds, 8, 7, fd, s, 3) == 3);
    assert(chimera_vfs_fd_seek(fds, 8, 7, fd, 0) == 0);
    char out[8]{};
    assert(chimera_vfs_fd_read(fds, 8, 7, fd, out, sizeof(out)) == 3);
    assert(!strcmp(out, "abc"));
    assert(chimera_vfs_fd_read(fds, 8, 8, fd, out, 1) == CHIMERA_VFS_EINVAL);
    assert(chimera_vfs_close(fds, 8, 7, fd) == 0);
    assert(chimera_vfs_fd_read(fds, 8, 7, fd, out, 1) == CHIMERA_VFS_EINVAL);
    int fd2 = chimera_vfs_open(fds, 8, &fs, 9, 1000, 100, "/docs/file.txt", CHIMERA_FD_READ);
    assert(fd2 >= 0);
    assert(chimera_vfs_fd_write(fds, 8, 9, fd2, s, 1) == CHIMERA_VFS_EACCES);
    assert(chimera_vfs_close_process(fds, 8, 9) == 0);
    assert(chimera_vfs_fd_read(fds, 8, 9, fd2, out, 1) == CHIMERA_VFS_EINVAL);
    return 0;
}