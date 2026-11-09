#define _DEFAULT_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <utmpx.h>
#include <sys/stat.h>
#include <sys/types.h>

static void usage(void) {
    fprintf(stderr, "usage: write user [tty]\n");
}

static int write_all(int fd, const char *data, size_t length) {
    while (length) {
        ssize_t count = write(fd, data, length);
        if (count < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        if (count == 0) { errno = EIO; return -1; }
        data += (size_t)count;
        length -= (size_t)count;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2 || argc > 3 || argv[1][0] == '-') {
        usage();
        return 2;
    }

    const char *requested_user = argv[1];
    const char *requested_tty = argc == 3 ? argv[2] : NULL;
    char tty[sizeof(((struct utmpx *)0)->ut_line) + 1] = {0};
    int found = 0;

    setutxent();
    struct utmpx *entry;
    while ((entry = getutxent()) != NULL) {
        if (entry->ut_type != USER_PROCESS) continue;
        if (strncmp(entry->ut_user, requested_user, sizeof(entry->ut_user)) != 0) continue;
        if (requested_tty && strncmp(entry->ut_line, requested_tty, sizeof(entry->ut_line)) != 0) continue;
        memcpy(tty, entry->ut_line, sizeof(entry->ut_line));
        tty[sizeof(entry->ut_line)] = '\0';
        found = 1;
        break;
    }
    endutxent();

    if (!found) {
        fprintf(stderr, "write: %s is not logged in%s\n", requested_user,
                requested_tty ? " on the requested terminal" : "");
        return 1;
    }

    char device[sizeof("/dev/") + sizeof(tty)];
    if (snprintf(device, sizeof(device), "/dev/%s", tty) >= (int)sizeof(device)) {
        fprintf(stderr, "write: terminal path is too long\n");
        return 1;
    }
    if (access(device, W_OK) != 0) {
        fprintf(stderr, "write: %s: %s\n", device, strerror(errno));
        return 1;
    }
    int terminal = open(device, O_WRONLY | O_CLOEXEC | O_NONBLOCK);
    if (terminal < 0) {
        fprintf(stderr, "write: %s: %s\n", device, strerror(errno));
        return 1;
    }

    char user[128] = "unknown";
    if (getlogin_r(user, sizeof(user)) != 0) {
        const char *env_user = getenv("USER");
        if (env_user && *env_user) snprintf(user, sizeof(user), "%s", env_user);
        else {
            struct passwd *pw = getpwuid(getuid());
            if (pw) snprintf(user, sizeof(user), "%s", pw->pw_name);
        }
    }
    char host[256] = "localhost";
    (void)gethostname(host, sizeof(host) - 1);
    time_t now = time(NULL);
    struct tm local;
    char timestamp[64] = "unknown time";
    if (localtime_r(&now, &local)) (void)strftime(timestamp, sizeof(timestamp), "%a %b %e %H:%M:%S", &local);

    char header[512];
    int header_len = snprintf(header, sizeof(header),
        "\nMessage from %s@%s on %s at %s ...\n", user, host, tty, timestamp);
    if (header_len < 0 || (size_t)header_len >= sizeof(header) ||
        write_all(terminal, header, (size_t)header_len) != 0) {
        fprintf(stderr, "write: cannot write to %s: %s\n", device, strerror(errno));
        close(terminal);
        return 1;
    }

    char buffer[4096];
    ssize_t count;
    while ((count = read(STDIN_FILENO, buffer, sizeof(buffer))) > 0) {
        if (write_all(terminal, buffer, (size_t)count) != 0) {
            fprintf(stderr, "write: terminal write failed: %s\n", strerror(errno));
            close(terminal);
            return 1;
        }
    }
    if (count < 0 && errno != EINTR) {
        fprintf(stderr, "write: stdin read failed: %s\n", strerror(errno));
        close(terminal);
        return 1;
    }
    (void)write_all(terminal, "\nEOF\n", 5);
    close(terminal);
    return 0;
}
