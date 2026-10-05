#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

static int write_all_fd(int fd, const void *data, size_t len)
{
    const unsigned char *p = (const unsigned char *)data;

    while (len > 0) {
        ssize_t n = write(fd, p, len);

        if (n < 0) {
            if (errno == EINTR)
                continue;

            return -1;
        }

        if (n == 0)
            return -1;

        p += (size_t)n;
        len -= (size_t)n;
    }

    return 0;
}

#include <dirent.h>
#include <time.h>

static const char *progname(const char *s)
{
    const char *p = strrchr(s, '/');
    return p ? p + 1 : s;
}

static int cmd_pwd(void)
{
    char buf[PATH_MAX];

    if (!getcwd(buf, sizeof(buf))) {
        perror("pwd");
        return 1;
    }

    puts(buf);
    return 0;
}

static int cmd_echo(int argc, char **argv)
{
    for (int i = 1; i < argc; ++i) {
        if (i > 1)
            putchar(' ');
        fputs(argv[i], stdout);
    }

    putchar('\n');
    return 0;
}

static int cmd_ls(int argc, char **argv)
{
    const char *path = argc > 1 ? argv[1] : ".";

    DIR *d = opendir(path);
    if (!d) {
        perror(path);
        return 1;
    }

    struct dirent *e;

    while ((e = readdir(d)) != NULL) {
        if (!strcmp(e->d_name, ".") || !strcmp(e->d_name, ".."))
            continue;

        printf("%s\n", e->d_name);
    }

    closedir(d);
    return 0;
}

static int copy_file(const char *src, const char *dst)
{
    int in = open(src, O_RDONLY);
    if (in < 0) {
        perror(src);
        return 1;
    }

    struct stat st;

    if (fstat(in, &st) < 0) {
        perror(src);
        close(in);
        return 1;
    }

    int out = open(
        dst,
        O_WRONLY | O_CREAT | O_TRUNC,
        st.st_mode & 0777
    );

    if (out < 0) {
        perror(dst);
        close(in);
        return 1;
    }

    char buf[65536];
    ssize_t n;

    while ((n = read(in, buf, sizeof(buf))) > 0) {
        ssize_t off = 0;

        while (off < n) {
            ssize_t w = write(out, buf + off, (size_t)(n - off));

            if (w < 0) {
                perror(dst);
                close(in);
                close(out);
                return 1;
            }

            off += w;
        }
    }

    if (n < 0) {
        perror(src);
        close(in);
        close(out);
        return 1;
    }

    close(in);
    close(out);

    return 0;
}

static int cmd_cp(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: cp SOURCE DEST\n");
        return 2;
    }

    if (!strcmp(argv[1], argv[2])) {
        fprintf(stderr, "cp: source and destination are the same file\n");
        return 1;
    }

    return copy_file(argv[1], argv[2]);
}

static int cmd_touch(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: touch FILE...\n");
        return 2;
    }

    int rc = 0;

    for (int i = 1; i < argc; ++i) {
        int fd = open(
            argv[i],
            O_WRONLY | O_CREAT,
            0666
        );

        if (fd < 0) {
            perror(argv[i]);
            rc = 1;
            continue;
        }

        close(fd);

        if (utimensat(
                AT_FDCWD,
                argv[i],
                NULL,
                0) < 0) {
            perror(argv[i]);
            rc = 1;
        }
    }

    return rc;
}

static int cmd_mkdir(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: mkdir DIRECTORY...\n");
        return 2;
    }

    int rc = 0;

    for (int i = 1; i < argc; ++i) {
        if (mkdir(argv[i], 0777) < 0) {
            perror(argv[i]);
            rc = 1;
        }
    }

    return rc;
}

static int cmd_rm(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: rm FILE...\n");
        return 2;
    }

    int rc = 0;

    for (int i = 1; i < argc; ++i) {
        if (unlink(argv[i]) < 0) {
            perror(argv[i]);
            rc = 1;
        }
    }

    return rc;
}

static int cmd_cat(int argc, char **argv)
{
    if (argc < 2) {
        char buf[65536];
        ssize_t n;

        while ((n = read(STDIN_FILENO, buf, sizeof(buf))) > 0)
            if (write_all_fd(STDOUT_FILENO, buf, (size_t)n) < 0) {
                perror("write");
                close(fd);
                return 1;
            }

        return n < 0 ? 1 : 0;
    }

    int rc = 0;

    for (int i = 1; i < argc; ++i) {
        int fd = open(argv[i], O_RDONLY);

        if (fd < 0) {
            perror(argv[i]);
            rc = 1;
            continue;
        }

        char buf[65536];
        ssize_t n;

        while ((n = read(fd, buf, sizeof(buf))) > 0)
            if (write_all_fd(STDOUT_FILENO, buf, (size_t)n) < 0) {
                perror("write");
                close(fd);
                return 1;
            }

        if (n < 0) {
            perror(argv[i]);
            rc = 1;
        }

        close(fd);
    }

    return rc;
}

static int cmd_clear(void)
{
    fputs("\033[2J\033[H", stdout);
    return 0;
}

static int cmd_whoami(void)
{
    const char *u = getenv("USER");

    if (u) {
        puts(u);
        return 0;
    }

    return system("id -un");
}

static int cmd_hostname(void)
{
    char buf[256];

    if (gethostname(buf, sizeof(buf)) < 0) {
        perror("hostname");
        return 1;
    }

    buf[sizeof(buf) - 1] = '\0';
    puts(buf);

    return 0;
}

static int cmd_date(void)
{
    time_t now = time(NULL);
    struct tm tmv;

    if (!localtime_r(&now, &tmv)) {
        perror("date");
        return 1;
    }

    char buf[128];

    if (!strftime(
            buf,
            sizeof(buf),
            "%a %b %d %H:%M:%S %Z %Y",
            &tmv)) {
        return 1;
    }

    puts(buf);
    return 0;
}

static int cmd_true(void)
{
    return 0;
}

static int cmd_false(void)
{
    return 1;
}

static int cmd_chimera_native(void)
{
    puts("Chimera II native command runtime");
    puts("ABI: native");
    puts("Status: operational");
    return 0;
}

int main(int argc, char **argv)
{
    const char *cmd = progname(argv[0]);

    if (!strcmp(cmd, "chimera-cmd"))
        return cmd_chimera_native();

    if (!strcmp(cmd, "pwd"))
        return cmd_pwd();

    if (!strcmp(cmd, "echo"))
        return cmd_echo(argc, argv);

    if (!strcmp(cmd, "ls"))
        return cmd_ls(argc, argv);

    if (!strcmp(cmd, "cp"))
        return cmd_cp(argc, argv);

    if (!strcmp(cmd, "touch"))
        return cmd_touch(argc, argv);

    if (!strcmp(cmd, "mkdir"))
        return cmd_mkdir(argc, argv);

    if (!strcmp(cmd, "rm"))
        return cmd_rm(argc, argv);

    if (!strcmp(cmd, "cat"))
        return cmd_cat(argc, argv);

    if (!strcmp(cmd, "clear"))
        return cmd_clear();

    if (!strcmp(cmd, "whoami"))
        return cmd_whoami();

    if (!strcmp(cmd, "hostname"))
        return cmd_hostname();

    if (!strcmp(cmd, "date"))
        return cmd_date();

    if (!strcmp(cmd, "true"))
        return cmd_true();

    if (!strcmp(cmd, "false"))
        return cmd_false();

    fprintf(
        stderr,
        "chimera-cmd: native implementation unavailable for '%s'\n",
        cmd
    );

    return 127;
}
