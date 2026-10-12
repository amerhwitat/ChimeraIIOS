#include "chimera/file.h"
#include <string.h>

int main(void) {
    static const char message[] = "Chimera file-oriented API\n";
    chm_fd fd = chm_open("chimera-file-example.tmp",
                         CHM_O_WRITE_ONLY | CHM_O_CREATE | CHM_O_TRUNCATE, 0600);
    if (fd < 0) return 1;
    int64_t written = chm_write(fd, message, sizeof(message) - 1);
    int close_rc = chm_close(fd);
    int unlink_rc = chm_unlink("chimera-file-example.tmp");
    return written == (int64_t)(sizeof(message) - 1) && close_rc == 0 && unlink_rc == 0 ? 0 : 2;
}
