#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc, char **argv) {
    const char *runtime = getenv("CHIMERA_MOBILE_RUNTIME");
    if (!runtime || !*runtime) runtime = "/system/bin/koronos-runtime";
    fprintf(stdout, "Chimera Mobile Edition\n");
    fprintf(stdout, "Koronos runtime attachment: %s\n", runtime);
    fflush(stdout);
    if (argc > 1) execv(argv[1], &argv[1]);
    if (access(runtime, X_OK) == 0) execl(runtime, runtime, (char *)0);
    fprintf(stderr, "Mobile runtime executable not installed: %s\n", runtime);
    return 127;
}
