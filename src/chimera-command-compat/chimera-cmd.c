#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <unistd.h>
#include <ctype.h>

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
    size_t size = 256;

    for (;;) {
        char *buf = malloc(size);

        if (!buf) {
            fprintf(stderr, "pwd: out of memory\n");
            return 1;
        }

        if (getcwd(buf, size) != NULL) {
            puts(buf);
            free(buf);
            return 0;
        }

        int saved_errno = errno;
        free(buf);

        if (saved_errno != ERANGE) {
            errno = saved_errno;
            perror("pwd");
            return 1;
        }

        if (size > SIZE_MAX / 2) {
            fprintf(stderr, "pwd: path is too long\n");
            return 1;
        }

        size *= 2;
    }
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

static int cmd_mv(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: mv SOURCE DEST\n");
        return 2;
    }
    if (!strcmp(argv[1], argv[2])) {
        fprintf(stderr, "mv: source and destination are the same path\n");
        return 1;
    }
    if (rename(argv[1], argv[2]) == 0)
        return 0;
    if (errno == EXDEV) {
        if (copy_file(argv[1], argv[2]) == 0 && unlink(argv[1]) == 0)
            return 0;
    }
    fprintf(stderr, "mv: %s: %s\n", argv[1], strerror(errno));
    return 1;
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
        fprintf(stderr, "usage: cat FILE...\n");
        return 1;
    }

    for (int i = 1; i < argc; ++i) {
        int input_fd = open(argv[i], O_RDONLY);

        if (input_fd < 0) {
            fprintf(stderr,
                    "cat: %s: %s\n",
                    argv[i],
                    strerror(errno));
            return 1;
        }

        unsigned char buf[8192];

        for (;;) {
            ssize_t n = read(input_fd, buf, sizeof(buf));

            if (n < 0) {
                if (errno == EINTR)
                    continue;

                fprintf(stderr,
                        "cat: %s: %s\n",
                        argv[i],
                        strerror(errno));

                close(input_fd);
                return 1;
            }

            if (n == 0)
                break;

            if (write_all_fd(STDOUT_FILENO,
                             buf,
                             (size_t)n) < 0) {
                fprintf(stderr,
                        "cat: write: %s\n",
                        strerror(errno));

                close(input_fd);
                return 1;
            }
        }

        if (close(input_fd) < 0) {
            fprintf(stderr,
                    "cat: %s: %s\n",
                    argv[i],
                    strerror(errno));
            return 1;
        }
    }

    return 0;
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
    struct utsname info;

    if (uname(&info) < 0) {
        perror("hostname");
        return 1;
    }

    puts(info.nodename);
    return 0;
}

static int cmd_date(void)
{
    time_t now = time(NULL);
    struct tm *tmv = localtime(&now);

    if (!tmv) {
        perror("date");
        return 1;
    }

    char buf[128];

    if (!strftime(
            buf,
            sizeof(buf),
            "%a %b %d %H:%M:%S %Z %Y",
            tmv)) {
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

/* ------------------------------------------------------------------------- */
/* Engineering command providers.                                            */
/* These are real native implementations with explicit argument handling.    */
/* They are partial engineering evidence only: the official ISA/command      */
/* conformance status is not changed by this file.                           */
/* ------------------------------------------------------------------------- */

static int emit_bytes(const void *data, size_t len)
{
    return fwrite(data, 1, len, stdout) == len ? 0 : -1;
}

static int read_all_stream(FILE *stream, char **out_buf, size_t *out_len)
{
    size_t cap = 8192;
    size_t len = 0;
    char *buf = malloc(cap);

    if (!buf)
        return -1;

    for (;;) {
        if (len == cap) {
            char *grown;

            if (cap > SIZE_MAX / 2) {
                free(buf);
                return -1;
            }

            grown = realloc(buf, cap * 2);
            if (!grown) {
                free(buf);
                return -1;
            }

            buf = grown;
            cap *= 2;
        }

        size_t n = fread(buf + len, 1, cap - len, stream);
        len += n;

        if (n == 0) {
            if (ferror(stream)) {
                free(buf);
                return -1;
            }
            break;
        }
    }

    *out_buf = buf;
    *out_len = len;
    return 0;
}

static int read_all_path(const char *path, char **out_buf, size_t *out_len)
{
    FILE *stream = fopen(path, "rb");

    if (!stream) {
        fprintf(stderr, "chimera-cmd: %s: %s\n", path, strerror(errno));
        return -1;
    }

    int rc = read_all_stream(stream, out_buf, out_len);
    fclose(stream);
    return rc;
}

static size_t count_lines(const char *buf, size_t len)
{
    size_t lines = 0;

    for (size_t i = 0; i < len; ++i)
        if (buf[i] == '\n')
            ++lines;

    if (len > 0 && buf[len - 1] != '\n')
        ++lines;

    return lines;
}

static int print_lines(const char *buf, size_t len,
                       size_t first_line, size_t line_count)
{
    if (line_count == 0)
        return 0;

    size_t line = 0;
    size_t start = 0;

    for (size_t i = 0; i < len; ++i) {
        if (buf[i] == '\n') {
            if (line >= first_line && line < first_line + line_count &&
                emit_bytes(buf + start, i + 1 - start) < 0)
                return -1;
            ++line;
            start = i + 1;
        }
    }

    if (start < len &&
        line >= first_line && line < first_line + line_count) {
        if (emit_bytes(buf + start, len - start) < 0 || emit_bytes("\n", 1) < 0)
            return -1;
    }

    return 0;
}

static int parse_ull(const char *text, unsigned long long *out)
{
    char *end = NULL;

    if (!text || !*text)
        return -1;

    errno = 0;
    unsigned long long value = strtoull(text, &end, 10);

    if (errno == ERANGE || !end || *end != '\0')
        return -1;

    *out = value;
    return 0;
}

static int parse_ll(const char *text, long long *out)
{
    char *end = NULL;

    if (!text || !*text)
        return -1;

    errno = 0;
    long long value = strtoll(text, &end, 10);

    if (errno == ERANGE || !end || *end != '\0')
        return -1;

    *out = value;
    return 0;
}

static int cmd_basename(int argc, char **argv)
{
    if (argc > 3) {
        fprintf(stderr, "usage: basename PATH [SUFFIX]\n");
        return 2;
    }

    const char *path = argc > 1 ? argv[1] : "";
    const char *suffix = argc > 2 ? argv[2] : NULL;
    size_t len = strlen(path);

    while (len > 1 && path[len - 1] == '/')
        --len;

    if (len == 1 && path[0] == '/') {
        puts("/");
        return 0;
    }

    size_t start = len;
    while (start > 0 && path[start - 1] != '/')
        --start;

    size_t name_len = len - start;
    if (suffix && *suffix) {
        size_t suffix_len = strlen(suffix);
        if (name_len > suffix_len &&
            !strcmp(path + len - suffix_len, suffix))
            name_len -= suffix_len;
    }

    if (emit_bytes(path + start, name_len) < 0 || emit_bytes("\n", 1) < 0)
        return 1;

    return 0;
}

static int cmd_dirname(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: dirname PATH\n");
        return 2;
    }

    char *path = strdup(argv[1]);
    if (!path) {
        fprintf(stderr, "dirname: out of memory\n");
        return 1;
    }

    size_t len = strlen(path);
    while (len > 1 && path[len - 1] == '/')
        path[--len] = '\0';

    size_t slash = len;
    while (slash > 0 && path[slash - 1] != '/')
        --slash;

    int rc;
    if (slash == 0) {
        rc = puts(".") < 0 ? 1 : 0;
    } else if (slash == 1) {
        rc = puts("/") < 0 ? 1 : 0;
    } else {
        while (slash > 1 && path[slash - 1] == '/')
            --slash;
        path[slash] = '\0';
        rc = puts(path) < 0 ? 1 : 0;
    }

    free(path);
    return rc;
}

static int emit_head_stream(FILE *stream, unsigned long long n,
                            const char *label)
{
    char *buf = NULL;
    size_t len = 0;

    if (label && printf("==> %s <==\n", label) < 0)
        return -1;

    if (read_all_stream(stream, &buf, &len) < 0) {
        free(buf);
        return -1;
    }

    size_t lines = count_lines(buf, len);
    size_t take = lines < n ? lines : (size_t)n;
    int rc = print_lines(buf, len, 0, take);

    free(buf);
    return rc;
}

static int cmd_head(int argc, char **argv)
{
    unsigned long long n = 10;
    int i = 1;

    if (i + 1 < argc && !strcmp(argv[i], "-n")) {
        if (parse_ull(argv[i + 1], &n) < 0) {
            fprintf(stderr, "head: invalid line count: %s\n", argv[i + 1]);
            return 2;
        }
        i += 2;
    }

    if (i == argc) {
        return emit_head_stream(stdin, n, NULL) < 0 || fflush(stdout) < 0 ? 1 : 0;
    }

    int rc = 0;
    int multiple = argc - i > 1;

    for (; i < argc; ++i) {
        FILE *stream;
        const char *label = NULL;

        if (!strcmp(argv[i], "-")) {
            stream = stdin;
        } else {
            stream = fopen(argv[i], "rb");
            if (!stream) {
                fprintf(stderr, "head: %s: %s\n", argv[i], strerror(errno));
                rc = 1;
                continue;
            }
            label = argv[i];
        }

        if (emit_head_stream(stream, n, multiple ? label : NULL) < 0)
            rc = 1;
        if (stream != stdin)
            fclose(stream);
    }

    if (fflush(stdout) < 0)
        rc = 1;

    return rc;
}

static int emit_tail_stream(FILE *stream, unsigned long long n,
                            int from_line, const char *label)
{
    char *buf = NULL;
    size_t len = 0;

    if (label && printf("==> %s <==\n", label) < 0)
        return -1;

    if (read_all_stream(stream, &buf, &len) < 0) {
        free(buf);
        return -1;
    }

    size_t lines = count_lines(buf, len);
    size_t first = 0;
    size_t take = 0;

    if (from_line) {
        if (n >= 1 && n <= lines) {
            first = (size_t)(n - 1);
            take = lines - first;
        }
    } else if (n > 0 && lines > n) {
        first = lines - (size_t)n;
        take = lines - first;
    } else if (n > 0) {
        first = 0;
        take = lines;
    }

    int rc = print_lines(buf, len, first, take);
    free(buf);
    return rc;
}

static int cmd_tail(int argc, char **argv)
{
    unsigned long long n = 10;
    int from_line = 0;
    int i = 1;

    if (i + 1 < argc && !strcmp(argv[i], "-n")) {
        const char *value = argv[i + 1];

        if (*value == '+') {
            from_line = 1;
            value++;
        }

        if (parse_ull(value, &n) < 0 || (from_line && n == 0)) {
            fprintf(stderr, "tail: invalid line count: %s\n", argv[i + 1]);
            return 2;
        }
        i += 2;
    }

    if (i == argc) {
        return emit_tail_stream(stdin, n, from_line, NULL) < 0 || fflush(stdout) < 0 ? 1 : 0;
    }

    int rc = 0;
    int multiple = argc - i > 1;

    for (; i < argc; ++i) {
        FILE *stream;
        const char *label = NULL;

        if (!strcmp(argv[i], "-")) {
            stream = stdin;
        } else {
            stream = fopen(argv[i], "rb");
            if (!stream) {
                fprintf(stderr, "tail: %s: %s\n", argv[i], strerror(errno));
                rc = 1;
                continue;
            }
            label = argv[i];
        }

        if (emit_tail_stream(stream, n, from_line, multiple ? label : NULL) < 0)
            rc = 1;
        if (stream != stdin)
            fclose(stream);
    }

    if (fflush(stdout) < 0)
        rc = 1;

    return rc;
}

static int cmd_wc(int argc, char **argv)
{
    int show_lines = 0;
    int show_words = 0;
    int show_bytes = 0;
    int i = 1;

    while (i < argc && argv[i][0] == '-' && argv[i][1] &&
           strspn(argv[i] + 1, "lwc") == strlen(argv[i] + 1)) {
        for (const char *p = argv[i] + 1; *p; ++p) {
            if (*p == 'l') show_lines = 1;
            if (*p == 'w') show_words = 1;
            if (*p == 'c') show_bytes = 1;
        }
        ++i;
    }

    if (!show_lines && !show_words && !show_bytes) {
        show_lines = show_words = show_bytes = 1;
    }

    unsigned long long total_lines = 0;
    unsigned long long total_words = 0;
    unsigned long long total_bytes = 0;
    int file_count = argc - i;
    int rc = 0;

    do {
        char *buf = NULL;
        size_t len = 0;
        const char *label = NULL;

        if (i < argc) {
            label = argv[i];
            if (!strcmp(label, "-")) {
                label = NULL;
                if (read_all_stream(stdin, &buf, &len) < 0) {
                    free(buf);
                    return 1;
                }
            } else if (read_all_path(label, &buf, &len) < 0) {
                free(buf);
                ++i;
                rc = 1;
                continue;
            }
        } else if (read_all_stream(stdin, &buf, &len) < 0) {
            free(buf);
            return 1;
        }

        unsigned long long lines = 0;
        unsigned long long words = 0;
        int in_word = 0;

        for (size_t k = 0; k < len; ++k) {
            unsigned char c = (unsigned char)buf[k];
            if (c == '\n')
                ++lines;
            if (isspace(c))
                in_word = 0;
            else if (!in_word) {
                ++words;
                in_word = 1;
            }
        }

        if (len > 0 && buf[len - 1] != '\n')
            ++lines;

        total_lines += lines;
        total_words += words;
        total_bytes += (unsigned long long)len;

        int first = 1;
        if (show_lines) {
            printf("%llu", lines);
            first = 0;
        }
        if (show_words) {
            printf("%s%llu", first ? "" : " ", words);
            first = 0;
        }
        if (show_bytes) {
            printf("%s%llu", first ? "" : " ", (unsigned long long)len);
            first = 0;
        }
        if (label)
            printf(" %s", label);
        putchar('\n');

        free(buf);
        ++i;
    } while (i < argc);

    if (file_count > 1) {
        int first = 1;
        if (show_lines) { printf("%llu", total_lines); first = 0; }
        if (show_words) { printf("%s%llu", first ? "" : " ", total_words); first = 0; }
        if (show_bytes) { printf("%s%llu", first ? "" : " ", total_bytes); first = 0; }
        printf(" total\n");
    }

    return fflush(stdout) < 0 ? 1 : rc;
}

static int cmd_seq(int argc, char **argv)
{
    long long first = 1;
    long long increment = 1;
    long long last;

    if (argc < 2 || argc > 4) {
        fprintf(stderr, "usage: seq [FIRST [INCREMENT]] LAST\n");
        return 2;
    }

    if (argc == 2) {
        if (parse_ll(argv[1], &last) < 0) {
            fprintf(stderr, "seq: invalid integer: %s\n", argv[1]);
            return 2;
        }
    } else if (argc == 3) {
        if (parse_ll(argv[1], &first) < 0 || parse_ll(argv[2], &last) < 0) {
            fprintf(stderr, "seq: invalid integer argument\n");
            return 2;
        }
    } else {
        if (parse_ll(argv[1], &first) < 0 ||
            parse_ll(argv[2], &increment) < 0 ||
            parse_ll(argv[3], &last) < 0) {
            fprintf(stderr, "seq: invalid integer argument\n");
            return 2;
        }
    }

    if (increment == 0) {
        fprintf(stderr, "seq: increment must not be zero\n");
        return 2;
    }

    long long value = first;

    for (;;) {
        if ((increment > 0 && value > last) || (increment < 0 && value < last))
            break;

        printf("%lld\n", value);

        if ((increment > 0 && value > LLONG_MAX - increment) ||
            (increment < 0 && value < LLONG_MIN - increment))
            break;

        value += increment;
    }

    return fflush(stdout) < 0 ? 1 : 0;
}

static int cmd_sleep(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: sleep SECONDS\n");
        return 2;
    }

    char *end = NULL;
    errno = 0;
    double seconds = strtod(argv[1], &end);

    if (errno == ERANGE || !end || *end != '\0' ||
        !(seconds >= 0.0 && seconds <= 1000000000.0)) {
        fprintf(stderr, "sleep: invalid duration: %s\n", argv[1]);
        return 2;
    }

    struct timespec request;
    request.tv_sec = (time_t)seconds;
    request.tv_nsec = (long)((seconds - (double)request.tv_sec) * 1000000000.0);

    while (nanosleep(&request, &request) < 0) {
        if (errno == EINTR)
            continue;
        perror("sleep");
        return 1;
    }

    return 0;
}

static int cmd_uname(int argc, char **argv)
{
    int show_kernel = 0;
    int show_node = 0;
    int show_release = 0;
    int show_version = 0;
    int show_machine = 0;

    if (argc == 1 || (argc == 2 && !strcmp(argv[1], "-s"))) {
        show_kernel = 1;
    } else {
        for (int i = 1; i < argc; ++i) {
            if (!strcmp(argv[i], "-a")) {
                show_kernel = show_node = show_release = show_version =
                    show_machine = 1;
            } else if (!strcmp(argv[i], "-s")) {
                show_kernel = 1;
            } else if (!strcmp(argv[i], "-n")) {
                show_node = 1;
            } else if (!strcmp(argv[i], "-r")) {
                show_release = 1;
            } else if (!strcmp(argv[i], "-v")) {
                show_version = 1;
            } else if (!strcmp(argv[i], "-m")) {
                show_machine = 1;
            } else {
                fprintf(stderr, "usage: uname [-s|-n|-r|-v|-m|-a]\n");
                return 2;
            }
        }
    }

    struct utsname info;
    if (uname(&info) < 0) {
        perror("uname");
        return 1;
    }

    int first = 1;
    if (show_kernel) { printf("%s", info.sysname); first = 0; }
    if (show_node) { printf("%s%s", first ? "" : " ", info.nodename); first = 0; }
    if (show_release) { printf("%s%s", first ? "" : " ", info.release); first = 0; }
    if (show_version) { printf("%s%s", first ? "" : " ", info.version); first = 0; }
    if (show_machine) { printf("%s%s", first ? "" : " ", info.machine); first = 0; }
    putchar('\n');
    return fflush(stdout) < 0 ? 1 : 0;
}

static int cmd_readlink(int argc, char **argv)
{
    int canonical = 0;
    int i = 1;

    if (i < argc && !strcmp(argv[i], "-f")) {
        canonical = 1;
        ++i;
    }

    if (argc - i != 1) {
        fprintf(stderr, "usage: readlink [-f] PATH\n");
        return 2;
    }

    if (canonical) {
        char *resolved = realpath(argv[i], NULL);
        if (!resolved) {
            fprintf(stderr, "readlink: %s: %s\n", argv[i], strerror(errno));
            return 1;
        }
        int rc = puts(resolved) < 0 ? 1 : 0;
        free(resolved);
        return rc;
    }

    size_t cap = PATH_MAX;
    char *buf = malloc(cap);
    if (!buf) {
        fprintf(stderr, "readlink: out of memory\n");
        return 1;
    }

    ssize_t n;
    for (;;) {
        n = readlink(argv[i], buf, cap);
        if (n < 0) {
            fprintf(stderr, "readlink: %s: %s\n", argv[i], strerror(errno));
            free(buf);
            return 1;
        }
        if ((size_t)n < cap)
            break;

        char *grown = realloc(buf, cap * 2);
        if (!grown || cap > SIZE_MAX / 2) {
            free(grown ? grown : buf);
            fprintf(stderr, "readlink: target is too long\n");
            return 1;
        }
        buf = grown;
        cap *= 2;
    }

    buf[n] = '\0';
    int rc = puts(buf) < 0 ? 1 : 0;
    free(buf);
    return rc;
}

static int cmd_rmdir(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: rmdir DIRECTORY...\n");
        return 2;
    }

    int rc = 0;
    for (int i = 1; i < argc; ++i) {
        if (rmdir(argv[i]) < 0) {
            fprintf(stderr, "rmdir: %s: %s\n", argv[i], strerror(errno));
            rc = 1;
        }
    }
    return rc;
}

static int cmd_ln(int argc, char **argv)
{
    int symbolic = 0;
    int force = 0;
    int i = 1;

    while (i < argc && argv[i][0] == '-' && argv[i][1]) {
        if (!strcmp(argv[i], "-s")) symbolic = 1;
        else if (!strcmp(argv[i], "-f")) force = 1;
        else {
            fprintf(stderr, "ln: unsupported option: %s\n", argv[i]);
            return 2;
        }
        ++i;
    }

    if (argc - i != 2) {
        fprintf(stderr, "usage: ln [-s] [-f] SOURCE DEST\n");
        return 2;
    }

    const char *source = argv[i];
    const char *dest = argv[i + 1];

    if (force) {
        struct stat st;
        if (lstat(dest, &st) == 0 && unlink(dest) < 0) {
            fprintf(stderr, "ln: %s: %s\n", dest, strerror(errno));
            return 1;
        }
    }

    int rc = symbolic ? symlink(source, dest) : link(source, dest);
    if (rc < 0) {
        fprintf(stderr, "ln: %s -> %s: %s\n", source, dest, strerror(errno));
        return 1;
    }

    return 0;
}

extern char **environ;

static int cmd_printenv(int argc, char **argv)
{
    if (argc == 1) {
        for (char **p = environ; p && *p; ++p)
            if (puts(*p) < 0)
                return 1;
        return fflush(stdout) < 0 ? 1 : 0;
    }

    int rc = 0;
    for (int i = 1; i < argc; ++i) {
        const char *value = getenv(argv[i]);
        if (!value) {
            rc = 1;
            continue;
        }
        if (puts(value) < 0)
            return 1;
    }
    return fflush(stdout) < 0 ? 1 : rc;
}

static int cmd_env(int argc, char **argv)
{
    int i = 1;
    size_t base_count = 0;

    while (environ[base_count])
        ++base_count;

    char **out = calloc(base_count + (size_t)argc + 1, sizeof(*out));
    if (!out) {
        fprintf(stderr, "env: out of memory\n");
        return 1;
    }

    size_t count = 0;
    if (i < argc && !strcmp(argv[i], "-i")) {
        ++i;
    } else {
        for (size_t k = 0; k < base_count; ++k) {
            out[count] = strdup(environ[k]);
            if (!out[count]) {
                fprintf(stderr, "env: out of memory\n");
                return 1;
            }
            ++count;
        }
    }

    while (i < argc) {
        const char *assignment = argv[i];
        const char *eq = strchr(assignment, '=');

        if (!eq || eq == assignment)
            break;

        size_t key_len = (size_t)(eq - assignment);
        int replaced = 0;

        for (size_t k = 0; k < count; ++k) {
            if (!strncmp(out[k], assignment, key_len) && out[k][key_len] == '=') {
                char *value = strdup(assignment);
                if (!value) {
                    fprintf(stderr, "env: out of memory\n");
                    return 1;
                }
                free(out[k]);
                out[k] = value;
                replaced = 1;
                break;
            }
        }

        if (!replaced) {
            out[count] = strdup(assignment);
            if (!out[count]) {
                fprintf(stderr, "env: out of memory\n");
                return 1;
            }
            ++count;
        }

        ++i;
    }

    out[count] = NULL;

    if (i == argc) {
        for (size_t k = 0; k < count; ++k)
            if (puts(out[k]) < 0) {
                free(out);
                return 1;
            }
        int rc = fflush(stdout) < 0 ? 1 : 0;
        for (size_t k = 0; k < count; ++k)
            free(out[k]);
        free(out);
        return rc;
    }

    /* POSIX environ is a mutable global; execvp uses it for the child. */
    environ = out;
    execvp(argv[i], &argv[i]);
    fprintf(stderr, "env: %s: %s\n", argv[i], strerror(errno));
    return errno == ENOENT ? 127 : 126;
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

    if (!strcmp(cmd, "mv"))
        return cmd_mv(argc, argv);

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

    if (!strcmp(cmd, "basename")) return cmd_basename(argc, argv);
    if (!strcmp(cmd, "dirname")) return cmd_dirname(argc, argv);
    if (!strcmp(cmd, "head")) return cmd_head(argc, argv);
    if (!strcmp(cmd, "tail")) return cmd_tail(argc, argv);
    if (!strcmp(cmd, "wc")) return cmd_wc(argc, argv);
    if (!strcmp(cmd, "seq")) return cmd_seq(argc, argv);
    if (!strcmp(cmd, "sleep")) return cmd_sleep(argc, argv);
    if (!strcmp(cmd, "uname")) return cmd_uname(argc, argv);
    if (!strcmp(cmd, "readlink")) return cmd_readlink(argc, argv);
    if (!strcmp(cmd, "rmdir")) return cmd_rmdir(argc, argv);
    if (!strcmp(cmd, "ln")) return cmd_ln(argc, argv);
    if (!strcmp(cmd, "printenv")) return cmd_printenv(argc, argv);
    if (!strcmp(cmd, "env")) return cmd_env(argc, argv);

    /* Route unknown command names through the shared runtime dispatcher.
       Preserve argv exactly and never parse command text through a shell. */
    if (getenv("CHIMERA_DISABLE_COMPAT") == NULL) {
        const char *mode = getenv("CHIMERA_COMMAND_MODE");
        if (mode == NULL || (strcmp(mode, "native") != 0 &&
                             strcmp(mode, "compat") != 0 &&
                             strcmp(mode, "auto") != 0))
            mode = "auto";

        char **run_argv = calloc((size_t)argc + 4, sizeof(*run_argv));
        if (run_argv == NULL) {
            fprintf(stderr, "chimera-cmd: out of memory while dispatching '%s'\n", cmd);
            return 1;
        }
        char self_path[PATH_MAX];
        ssize_t self_len = readlink("/proc/self/exe", self_path, sizeof(self_path) - 1);
        if (self_len > 0 && (size_t)self_len < sizeof(self_path)) {
            self_path[self_len] = '\0';
            (void)setenv("CHIMERA_SHIM_BINARY", self_path, 1);
        }
        run_argv[0] = (char *)"chimera-run";
        run_argv[1] = (char *)"--mode";
        run_argv[2] = (char *)mode;
        run_argv[3] = (char *)cmd;
        for (int i = 1; i < argc; ++i)
            run_argv[i + 3] = argv[i];
        run_argv[argc + 3] = NULL;
        execvp(run_argv[0], run_argv);
        int saved_errno = errno;
        free(run_argv);
        if (saved_errno != ENOENT) {
            errno = saved_errno;
            perror("chimera-cmd: chimera-run");
            return 126;
        }
    }

    fprintf(
        stderr,
        "chimera-cmd: native implementation unavailable for '%s'\n",
        cmd
    );
    return 127;
}
