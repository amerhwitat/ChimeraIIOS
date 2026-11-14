#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mount.h>

int main(int argc, char *argv[]) {
    printf("[KORONOS_INIT_CPL3_ACKNOWLEDGEMENT] PID=%d\n", getpid());
    
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
    printf("[KORONOS_INIT_INSTALLER] Status: CPL3 RING-3 USERSPACE\n");
    printf("================================================================================\n\n");
    
    // Mount critical filesystems
    mount("proc", "/proc", "proc", 0, NULL);
    mount("sysfs", "/sys", "sysfs", 0, NULL);
    mount("devtmpfs", "/dev", "devtmpfs", 0, "size=10m,mode=0755");
    
    printf("[KORONOS_INIT_INSTALLER] Launching installer wizard...\n");
    printf("[KORONOS_INIT_INSTALLER] Handoff complete - installation payload ready\n");
    
    // Launch installer UI
    execl("/usr/bin/installer-ui", "installer-ui", NULL);
    
    // Fallback shell
    execl("/bin/bash", "bash", "-l", NULL);
    
    return 0;
}
