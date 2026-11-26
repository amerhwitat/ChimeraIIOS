/* Historical Linux reference sample, not a Koronos-native init. Markers below
 * are sample source output only; they do not establish a native handoff or
 * production acceptance. */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mount.h>

int main(int argc, char *argv[]) {
    printf("[LINUX_REFERENCE_INIT_ACKNOWLEDGEMENT] PID=%d\n", getpid());
    
    if (getpid() != 1) {
        fprintf(stderr, "ERROR: Init must run as PID 1\n");
        return 1;
    }
    
    printf("\n");
    printf("================================================================================\n");
    printf("                 KORONOS INSTALLER - INIT (PID=1)\n");
    printf("================================================================================\n");
    printf("[KORONOS_INIT_INSTALLER] Kernel→Userspace Handoff\n");
    printf("[KORONOS_INIT_INSTALLER] Target: INSTALLER SYSTEM\n");
    printf("[KORONOS_INIT_INSTALLER] PID: %d\n", getpid());
    printf("[LINUX_REFERENCE_INIT_INSTALLER] Status: Linux reference marker only\n");
    printf("================================================================================\n\n");
    
    // Mount critical filesystems
    mount("proc", "/proc", "proc", 0, NULL);
    mount("sysfs", "/sys", "sysfs", 0, NULL);
    mount("devtmpfs", "/dev", "devtmpfs", 0, "size=10m,mode=0755");
    
    printf("[KORONOS_INIT_INSTALLER] Launching installer wizard...\n");
    printf("[LINUX_REFERENCE_INIT_INSTALLER] reference sequence complete; native handoff not established\n");
    
    // Launch installer UI
    execl("/usr/bin/installer-ui", "installer-ui", NULL);
    
    // Fallback shell
    execl("/bin/bash", "bash", "-l", NULL);
    
    return 0;
}
