#include <stdio.h>
#include <unistd.h>
#include <sys/mount.h>

int main() {
    printf("[KORONOS_INIT_CPL3_ACKNOWLEDGEMENT] PID=%d\n", getpid());
    
    if (getpid() != 1) return 1;
    
    printf("\n[KORONOS_INIT_INSTALLER] Kernel→Userspace Handoff\n");
    printf("[KORONOS_INIT_INSTALLER] Target: INSTALLER SYSTEM\n");
    printf("[KORONOS_INIT_INSTALLER] PID: %d\n\n", getpid());
    
    mount("proc", "/proc", "proc", 0, NULL);
    mount("sysfs", "/sys", "sysfs", 0, NULL);
    mount("devtmpfs", "/dev", "devtmpfs", 0, NULL);
    
    printf("[KORONOS_INIT_INSTALLER] Handoff complete\n");
    printf("[KORONOS_INIT_INSTALLER] Installation ready...\n\n");
    
    execl("/bin/bash", "bash", "-l", NULL);
    return 0;
}
