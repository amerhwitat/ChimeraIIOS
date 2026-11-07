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
    puts("Chimera II POSIX command multicall");
    puts("ABI: Linux userspace ELF");
    puts("Koronos native syscall compatibility: not verified");
    return 0;
}


static int cmd_rmdir(int argc, char **argv)
{
    int rc = 0;
    if (argc < 2) { fprintf(stderr, "rmdir: missing operand\n"); return 1; }
    for (int i = 1; i < argc; ++i) {
        if (rmdir(argv[i]) != 0) { perror(argv[i]); rc = 1; }
    }
    return rc;
}

static int cmd_ln(int argc, char **argv)
{
    int symbolic = 0, force = 0, i = 1;
    while (i < argc && argv[i][0] == '-') {
        if (!strcmp(argv[i], "--")) { ++i; break; }
        for (const char *p = argv[i] + 1; *p; ++p) {
            if (*p == 's') symbolic = 1;
            else if (*p == 'f') force = 1;
            else { fprintf(stderr, "ln: unsupported option -%c\n", *p); return 1; }
        }
        ++i;
    }
    if (argc - i != 2) { fprintf(stderr, "usage: ln [-sf] TARGET LINK_NAME\n"); return 1; }
    if (force && unlink(argv[i + 1]) != 0 && errno != ENOENT) { perror(argv[i + 1]); return 1; }
    int rc = symbolic ? symlink(argv[i], argv[i + 1]) : link(argv[i], argv[i + 1]);
    if (rc != 0) { perror(argv[i + 1]); return 1; }
    return 0;
}

static int cmd_readlink(int argc, char **argv)
{
    if (argc != 2) { fprintf(stderr, "usage: readlink LINK\n"); return 1; }
    char buf[PATH_MAX + 1];
    ssize_t n = readlink(argv[1], buf, PATH_MAX);
    if (n < 0) { perror(argv[1]); return 1; }
    buf[n] = '\0';
    puts(buf);
    return 0;
}

static char *trim_path_copy(const char *input)
{
    char *p = strdup(input);
    if (!p) return NULL;
    size_t n = strlen(p);
    while (n > 1 && p[n - 1] == '/') p[--n] = '\0';
    return p;
}

static int cmd_basename(int argc, char **argv)
{
    if (argc < 2 || argc > 3) { fprintf(stderr, "usage: basename PATH [SUFFIX]\n"); return 1; }
    char *p = trim_path_copy(argv[1]);
    if (!p) return 1;
    char *base = strrchr(p, '/');
    base = base ? base + 1 : p;
    if (argc == 3) {
        size_t n = strlen(base), sn = strlen(argv[2]);
        if (sn && sn <= n && !strcmp(base + n - sn, argv[2])) base[n - sn] = '\0';
    }
    puts(*base ? base : "/");
    free(p);
    return 0;
}

static int cmd_dirname(int argc, char **argv)
{
    if (argc != 2) { fprintf(stderr, "usage: dirname PATH\n"); return 1; }
    char *p = trim_path_copy(argv[1]);
    if (!p) return 1;
    char *slash = strrchr(p, '/');
    if (!slash) puts(".");
    else if (slash == p) puts("/");
    else { *slash = '\0'; puts(p); }
    free(p);
    return 0;
}

static int cmd_uname(int argc, char **argv)
{
    struct utsname u;
    if (uname(&u) != 0) { perror("uname"); return 1; }
    if (argc == 1) { puts(u.sysname); return 0; }
    int any = 0;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "-a")) { printf("%s %s %s %s %s\n", u.sysname,u.nodename,u.release,u.version,u.machine); return 0; }
        for (const char *p = argv[i] + (argv[i][0] == '-' ? 1 : 0); *p; ++p) {
            const char *v = NULL;
            switch (*p) {
                case 's': v=u.sysname; break; case 'n': v=u.nodename; break;
                case 'r': v=u.release; break; case 'v': v=u.version; break;
                case 'm': v=u.machine; break; case 'o': v="GNU/Linux"; break;
                default: fprintf(stderr,"uname: invalid option -- '%c'\n",*p); return 1;
            }
            if (any) putchar(' ');
            fputs(v, stdout); any = 1;
        }
    }
    if (any) putchar('\n');
    return 0;
}

static int cmd_wc(int argc, char **argv)
{
    int lines=0, words=0, bytes=0, i=1, files=0, rc=0;
    while (i < argc && argv[i][0]=='-' && argv[i][1]) {
        for (const char *p=argv[i]+1; *p; ++p) {
            if (*p=='l') lines=1; else if (*p=='w') words=1; else if (*p=='c' || *p=='m') bytes=1;
            else { fprintf(stderr,"wc: unsupported option -%c\n",*p); return 1; }
        }
        ++i;
    }
    if (!lines && !words && !bytes) lines=words=bytes=1;
    do {
        FILE *f = (i < argc) ? fopen(argv[i], "rb") : stdin;
        if (!f) { perror(argv[i]); rc=1; ++i; continue; }
        unsigned long long l=0,w=0,b=0; int c, inword=0;
        while ((c=fgetc(f)) != EOF) { ++b; if (c=='\n') ++l; if (c==' '||c=='\t'||c=='\n'||c=='\r'||c=='\f'||c=='\v') inword=0; else if(!inword){++w;inword=1;} }
        if (ferror(f)) { if (f!=stdin) perror(argv[i]); rc=1; }
        if (f!=stdin) fclose(f);
        int col=0;
        if(lines){printf("%llu",l);col=1;} if(words){printf("%s%llu",col?" ":"",w);col=1;}
        if(bytes)printf("%s%llu",col?" ":"",b);
        if(i<argc)printf(" %s",argv[i]);
        putchar('\n'); ++files; ++i;
    } while(i<argc);
    (void)files;
    return rc;
}

static int stream_lines(int argc, char **argv, int tail_mode)
{
    long count=10; int i=1;
    if (i<argc && !strcmp(argv[i],"-n")) {
        if (++i>=argc) { fprintf(stderr,"line utility: -n requires a count\n"); return 1; }
        char *end=NULL; count=strtol(argv[i++],&end,10);
        if (!end || *end || count<0 || count>1000000) { fprintf(stderr,"line utility: invalid line count\n"); return 1; }
    }
    if (i>=argc) {
        char *line=NULL; size_t cap=0; ssize_t n; long shown=0;
        if (!tail_mode) { while(shown<count && (n=getline(&line,&cap,stdin))>=0){fwrite(line,1,(size_t)n,stdout);++shown;} }
        else {
            char **ring=calloc((size_t)(count?count:1),sizeof(*ring)); size_t *lens=calloc((size_t)(count?count:1),sizeof(*lens));
            if(!ring||!lens){free(ring);free(lens);free(line);return 1;}
            long total=0; while((n=getline(&line,&cap,stdin))>=0){size_t k=(size_t)(total%(count?count:1));free(ring[k]);ring[k]=strndup(line,(size_t)n);lens[k]=(size_t)n;++total;}
            long start=total>count?total-count:0;for(long x=start;x<total;++x){size_t k=(size_t)(x%(count?count:1));if(ring[k])fwrite(ring[k],1,lens[k],stdout);}
            for(long x=0;x<(count?count:1);++x)free(ring[x]);free(ring);free(lens);
        }
        free(line); return ferror(stdin)?1:0;
    }
    int rc=0;
    for(;i<argc;++i){FILE*f=fopen(argv[i],"r");if(!f){perror(argv[i]);rc=1;continue;}
        char *line=NULL;size_t cap=0;ssize_t n;long shown=0;
        if(!tail_mode){while(shown<count&&(n=getline(&line,&cap,f))>=0){fwrite(line,1,(size_t)n,stdout);++shown;}}
        else {char **ring=calloc((size_t)(count?count:1),sizeof(*ring));size_t*lens=calloc((size_t)(count?count:1),sizeof(*lens));long total=0;
            if(!ring||!lens){free(ring);free(lens);free(line);fclose(f);return 1;}
            while((n=getline(&line,&cap,f))>=0){size_t k=(size_t)(total%(count?count:1));free(ring[k]);ring[k]=strndup(line,(size_t)n);lens[k]=(size_t)n;++total;}
            long start=total>count?total-count:0;for(long x=start;x<total;++x){size_t k=(size_t)(x%(count?count:1));if(ring[k])fwrite(ring[k],1,lens[k],stdout);}
            for(long x=0;x<(count?count:1);++x)free(ring[x]);free(ring);free(lens);
        }
        free(line);fclose(f);
    }
    return rc;
}
static int cmd_head(int argc,char**argv){return stream_lines(argc,argv,0);}
static int cmd_tail(int argc,char**argv){return stream_lines(argc,argv,1);}
static int cmd_sleep(int argc,char**argv)
{
    if(argc!=2){fprintf(stderr,"usage: sleep SECONDS\n");return 1;}
    char *end=NULL;double sec=strtod(argv[1],&end);
    if(!end||*end||sec<0){fprintf(stderr,"sleep: invalid time interval\n");return 1;}
    struct timespec req={(time_t)sec,(long)((sec-(time_t)sec)*1000000000.0)};
    while(nanosleep(&req,&req)!=0){if(errno!=EINTR){perror("sleep");return 1;}}
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
    if (!strcmp(cmd, "rmdir"))
        return cmd_rmdir(argc, argv);
    if (!strcmp(cmd, "ln"))
        return cmd_ln(argc, argv);
    if (!strcmp(cmd, "readlink"))
        return cmd_readlink(argc, argv);
    if (!strcmp(cmd, "basename"))
        return cmd_basename(argc, argv);
    if (!strcmp(cmd, "dirname"))
        return cmd_dirname(argc, argv);
    if (!strcmp(cmd, "uname"))
        return cmd_uname(argc, argv);
    if (!strcmp(cmd, "wc"))
        return cmd_wc(argc, argv);
    if (!strcmp(cmd, "head"))
        return cmd_head(argc, argv);
    if (!strcmp(cmd, "tail"))
        return cmd_tail(argc, argv);
    if (!strcmp(cmd, "sleep"))
        return cmd_sleep(argc, argv);

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
