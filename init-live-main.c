#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mount.h>
#include <sys/wait.h>
#include <signal.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define KORONOS_LIVE 1
#define KORONOS_VERSION "1.0"

void print_banner(void) {
    printf("\n");
    printf("================================================================================\n");
    printf("                 KORONOS LIVE SYSTEM - INIT (PID=1)\n");
    printf("================================================================================\n");
    printf("[KORONOS_INIT] Kernel→Userspace Handoff Starting\n");
    printf("[KORONOS_INIT] Target: LIVE SYSTEM\n");
    printf("[KORONOS_INIT] Version: %s\n", KORONOS_VERSION);
    printf("[KORONOS_INIT] Architecture: x86_64\n");
    printf("[KORONOS_INIT] PID: %d (Parent: %d)\n", getpid(), getppid());
    printf("[KORONOS_INIT] Status: CPL3 RING-3 USER SPACE\n");
    printf("================================================================================\n\n");
}

void mount_filesystems(void) {
    printf("[KORONOS_INIT] Mounting virtual filesystems...\n");
    
    // Mount procfs
    if (mount("proc", "/proc", "proc", 0, NULL) < 0) {
        printf("[KORONOS_INIT_ERROR] Failed to mount /proc\n");
    } else {
        printf("[KORONOS_INIT] ✓ /proc mounted\n");
    }
    
    // Mount sysfs
    if (mount("sysfs", "/sys", "sysfs", 0, NULL) < 0) {
        printf("[KORONOS_INIT_ERROR] Failed to mount /sys\n");
    } else {
        printf("[KORONOS_INIT] ✓ /sys mounted\n");
    }
    
    // Mount devtmpfs
    if (mount("devtmpfs", "/dev", "devtmpfs", 0, "size=10m,nr_inodes=248418,mode=0755") < 0) {
        printf("[KORONOS_INIT_ERROR] Failed to mount /dev\n");
    } else {
        printf("[KORONOS_INIT] ✓ /dev mounted\n");
    }
    
    // Create pts
    mkdir("/dev/pts", 0755);
    if (mount("devpts", "/dev/pts", "devpts", 0, "gid=5,mode=0620") < 0) {
        printf("[KORONOS_INIT_WARNING] Failed to mount /dev/pts\n");
    } else {
        printf("[KORONOS_INIT] ✓ /dev/pts mounted\n");
    }
}

void setup_environment(void) {
    printf("[KORONOS_INIT] Setting up environment...\n");
    
    // Set critical environment variables
    setenv("PATH", "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin", 1);
    setenv("HOME", "/root", 1);
    setenv("TERM", "linux", 1);
    setenv("KORONOS_TARGET", "live", 1);
    setenv("KORONOS_HANDOFF", "kernel_to_userspace", 1);
    
    printf("[KORONOS_INIT] ✓ Environment configured\n");
}

void start_services(void) {
    printf("[KORONOS_INIT] Starting core services...\n");
    
    pid_t pid;
    
    // Start syslogd
    pid = fork();
    if (pid == 0) {
        execlp("syslogd", "syslogd", NULL);
        exit(1);
    }
    printf("[KORONOS_INIT] ✓ Syslog started (PID: %d)\n", pid);
    
    // Start udevd  
    pid = fork();
    if (pid == 0) {
        execlp("udevd", "udevd", "--daemon", NULL);
        exit(1);
    }
    printf("[KORONOS_INIT] ✓ Udev started (PID: %d)\n", pid);
}

int launch_desktop(void) {
    printf("[KORONOS_INIT] Launching desktop environment...\n");
    printf("[KORONOS_INIT] Attempting to start Aurora Glass desktop...\n");
    
    pid_t pid = fork();
    if (pid == 0) {
        // Try to launch X server and desktop
        if (execl("/usr/bin/startx", "startx", NULL) < 0) {
            // Fallback to shell
            printf("[KORONOS_INIT] Desktop failed, launching shell...\n");
            if (execl("/bin/bash", "bash", "-l", NULL) < 0) {
                perror("Failed to launch shell");
                exit(1);
            }
        }
        exit(0);
    } else if (pid > 0) {
        printf("[KORONOS_INIT] Desktop launcher started (PID: %d)\n", pid);
        return pid;
    } else {
        perror("fork failed");
        return -1;
    }
}

void signal_handler(int sig) {
    printf("[KORONOS_INIT] Received signal %d\n", sig);
    if (sig == SIGTERM || sig == SIGINT) {
        printf("[KORONOS_INIT] Initiating system shutdown...\n");
        sync();
        exit(0);
    }
}

int main(int argc, char *argv[]) {
    printf("[KORONOS_INIT_CPL3_ACKNOWLEDGEMENT] PID=%d\n", getpid());
    
    // Verify we're PID 1
    if (getpid() != 1) {
        fprintf(stderr, "ERROR: This init must run as PID 1\n");
        return 1;
    }
    
    // Set up signal handlers
    signal(SIGTERM, signal_handler);
    signal(SIGINT, signal_handler);
    signal(SIGCHLD, SIG_IGN);
    
    // Begin handoff sequence
    print_banner();
    mount_filesystems();
    setup_environment();
    start_services();
    
    printf("[KORONOS_INIT] Handoff sequence complete\n");
    printf("[KORONOS_INIT] CPL3 RING-3 USERSPACE ACTIVE\n");
    printf("[KORONOS_INIT] Launching Live environment...\n\n");
    
    // Launch desktop
    int desktop_pid = launch_desktop();
    
    // Main event loop
    printf("[KORONOS_INIT] Entering main event loop (PID: %d)...\n", getpid());
    while (1) {
        pid_t child = wait(NULL);
        if (child > 0) {
            printf("[KORONOS_INIT] Child process %d exited\n", child);
        }
    }
    
    return 0;
}
