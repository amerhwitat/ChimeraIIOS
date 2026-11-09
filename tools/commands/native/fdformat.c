#define _DEFAULT_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/fd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

static void usage(void) {
    fprintf(stderr, "usage: fdformat [/dev/fdN]\n");
}

int main(int argc, char **argv) {
    const char *device = "/dev/fd0";
    if (argc == 2 && (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0)) {
        usage();
        return 0;
    }
    if (argc == 2) device = argv[1];
    else if (argc != 1) { usage(); return 2; }

    int fd = open(device, O_RDWR | O_CLOEXEC | O_NONBLOCK);
    if (fd < 0) {
        fprintf(stderr, "fdformat: %s: %s\n", device, strerror(errno));
        return 1;
    }

    struct floppy_struct geometry;
    if (ioctl(fd, FDGETPRM, &geometry) != 0) {
        fprintf(stderr, "fdformat: cannot read floppy geometry for %s: %s\n", device, strerror(errno));
        close(fd);
        return 1;
    }
    if (geometry.track == 0 || geometry.head == 0) {
        fprintf(stderr, "fdformat: invalid floppy geometry for %s\n", device);
        close(fd);
        return 1;
    }

    if (ioctl(fd, FDFMTBEG, 0) != 0) {
        fprintf(stderr, "fdformat: format start failed for %s: %s\n", device, strerror(errno));
        close(fd);
        return 1;
    }

    struct stat st;
    unsigned int drive = 0;
    if (fstat(fd, &st) == 0 && S_ISBLK(st.st_mode)) drive = (unsigned int)(minor(st.st_rdev) & 3);
    for (unsigned int track = 0; track < geometry.track; ++track) {
        for (unsigned int head = 0; head < geometry.head; ++head) {
            struct format_descr descriptor = { drive, head, track };
            if (ioctl(fd, FDFMTTRK, &descriptor) != 0) {
                int saved = errno;
                (void)ioctl(fd, FDFMTEND, 0);
                fprintf(stderr, "fdformat: track %u head %u failed: %s\n", track, head, strerror(saved));
                close(fd);
                return 1;
            }
        }
    }

    if (ioctl(fd, FDFMTEND, 0) != 0) {
        fprintf(stderr, "fdformat: format finalization failed: %s\n", strerror(errno));
        close(fd);
        return 1;
    }
    close(fd);
    printf("fdformat: formatted %s (%u tracks, %u heads)\n", device, geometry.track, geometry.head);
    return 0;
}
