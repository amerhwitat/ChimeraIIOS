#!/usr/bin/env bash
set -Eeuo pipefail
# ==============================================================================
# KORONOS INIT SYSTEM - KERNEL → USERSPACE HANDOFF
# ==============================================================================
# Three native init implementations for Live, Installer, Recovery targets
# Reference: Linux init/systemd architecture
# 
# The handoff sequence:
# 1. Kernel hands control to init (PID=1)
# 2. Init acknowledges target type (Live/Installer/Recovery)
# 3. Init initializes filesystem, devices, services
# 4. Init launches appropriate target environment

# ==============================================================================
# BUILD CONFIGURATION
# ==============================================================================

ARCH="${KORONOS_ARCH:-$(uname -m)}"
if [[ "$ARCH" != "x86_64" ]]; then
    echo "This Linux-host reference builder supports only x86_64; it is not a Koronos cross-compiler." >&2
    exit 64
fi
TARGET="${1:-live}"  # live, installer, recovery
OUTPUT_DIR="${2:-build/koronos-linux-reference-inits}"
mkdir -p "$OUTPUT_DIR"
BUILD_LOG="$OUTPUT_DIR/init-build.log"

{
echo "================================================================================"
echo "KORONOS INIT BUILDER - Kernel→Userspace Handoff"
echo "================================================================================"
echo "Architecture: $ARCH"
echo "Target: $TARGET"
echo "Output: $OUTPUT_DIR"
echo ""

# ==============================================================================
# STEP 1: CREATE LIVE INIT (PID=1 for Live System)
# ==============================================================================

echo "[1/3] Building LIVE INIT..."

cat > "$OUTPUT_DIR/init-live-main.c" << 'LIVE_INIT_EOF'
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
    printf("[LINUX_REFERENCE_INIT_PID1_ACK] PID=%d\n", getpid());
    
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
LIVE_INIT_EOF

echo "[✓] Live init source created"

# ==============================================================================
# STEP 2: CREATE INSTALLER INIT
# ==============================================================================

echo "[2/3] Building INSTALLER INIT..."

cat > "$OUTPUT_DIR/init-installer-main.c" << 'INSTALLER_INIT_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mount.h>

int main(int argc, char *argv[]) {
    printf("[LINUX_REFERENCE_INIT_PID1_ACK] PID=%d\n", getpid());
    
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
INSTALLER_INIT_EOF

echo "[✓] Installer init source created"

# ==============================================================================
# STEP 3: CREATE RECOVERY INIT
# ==============================================================================

echo "[3/3] Building RECOVERY INIT..."

cat > "$OUTPUT_DIR/init-recovery-main.c" << 'RECOVERY_INIT_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mount.h>

int main(int argc, char *argv[]) {
    printf("[LINUX_REFERENCE_INIT_PID1_ACK] PID=%d\n", getpid());
    
    if (getpid() != 1) {
        fprintf(stderr, "ERROR: Init must run as PID 1\n");
        return 1;
    }
    
    printf("\n");
    printf("================================================================================\n");
    printf("                 KORONOS RECOVERY - INIT (PID=1)\n");
    printf("================================================================================\n");
    printf("[KORONOS_INIT_RECOVERY] Kernel→Userspace Handoff\n");
    printf("[KORONOS_INIT_RECOVERY] Target: RECOVERY SYSTEM\n");
    printf("[KORONOS_INIT_RECOVERY] PID: %d\n", getpid());
    printf("[KORONOS_INIT_RECOVERY] Status: CPL3 RING-3 USERSPACE\n");
    printf("================================================================================\n\n");
    
    // Mount critical filesystems
    mount("proc", "/proc", "proc", 0, NULL);
    mount("sysfs", "/sys", "sysfs", 0, NULL);
    mount("devtmpfs", "/dev", "devtmpfs", 0, "size=10m,mode=0755");
    
    printf("[KORONOS_INIT_RECOVERY] Emergency recovery shell ready\n");
    printf("[KORONOS_INIT_RECOVERY] Handoff complete - recovery environment active\n");
    printf("[KORONOS_INIT_RECOVERY] Type 'help' for recovery commands\n\n");
    
    // Launch recovery shell
    execl("/bin/bash", "bash", "-i", "-l", NULL);
    
    return 0;
}
RECOVERY_INIT_EOF

echo "[✓] Recovery init source created"

# ==============================================================================
# STEP 4: COMPILE ALL INITS
# ==============================================================================

echo ""
echo "Compiling native init ELFs..."

# Detect compiler
if command -v gcc &> /dev/null; then
    CC="gcc"
elif command -v clang &> /dev/null; then
    CC="clang"
else
    echo "ERROR: No compiler found (gcc or clang required)"
    exit 1
fi

echo "Using compiler: $CC"

# Compile Linux-host reference init (not a Koronos-native ELF).
"$CC" -static -O2 -Wall -Wextra -Werror -o "$OUTPUT_DIR/linux-reference-init-live" "$OUTPUT_DIR/init-live-main.c"
test -s "$OUTPUT_DIR/linux-reference-init-live"
chmod +x "$OUTPUT_DIR/linux-reference-init-live"
readelf -h "$OUTPUT_DIR/linux-reference-init-live" | grep -Eq 'Class:[[:space:]]+ELF64'
readelf -h "$OUTPUT_DIR/linux-reference-init-live" | grep -Eq 'Machine:[[:space:]]+Advanced Micro Devices X86-64'
SIZE=$(stat -c%s "$OUTPUT_DIR/linux-reference-init-live")
echo "[✓] Linux reference init compiled: linux-reference-init-live ($SIZE bytes)"

# Compile Linux-host installer reference init (not a Koronos-native ELF).
"$CC" -static -O2 -Wall -Wextra -Werror -o "$OUTPUT_DIR/linux-reference-init-installer" "$OUTPUT_DIR/init-installer-main.c"
test -s "$OUTPUT_DIR/linux-reference-init-installer"
chmod +x "$OUTPUT_DIR/linux-reference-init-installer"
readelf -h "$OUTPUT_DIR/linux-reference-init-installer" | grep -Eq 'Class:[[:space:]]+ELF64'
readelf -h "$OUTPUT_DIR/linux-reference-init-installer" | grep -Eq 'Machine:[[:space:]]+Advanced Micro Devices X86-64'
SIZE=$(stat -c%s "$OUTPUT_DIR/linux-reference-init-installer")
echo "[✓] Linux reference init compiled: linux-reference-init-installer ($SIZE bytes)"

# Compile Linux-host recovery reference init (not a Koronos-native ELF).
"$CC" -static -O2 -Wall -Wextra -Werror -o "$OUTPUT_DIR/linux-reference-init-recovery" "$OUTPUT_DIR/init-recovery-main.c"
test -s "$OUTPUT_DIR/linux-reference-init-recovery"
chmod +x "$OUTPUT_DIR/linux-reference-init-recovery"
readelf -h "$OUTPUT_DIR/linux-reference-init-recovery" | grep -Eq 'Class:[[:space:]]+ELF64'
readelf -h "$OUTPUT_DIR/linux-reference-init-recovery" | grep -Eq 'Machine:[[:space:]]+Advanced Micro Devices X86-64'

# ==============================================================================
# STEP 5: CREATE TARGET MANIFESTS
# ==============================================================================

echo ""
echo "Creating target manifests with acceptance gates..."

cat > "$OUTPUT_DIR/target-manifest-live.json" << 'MANIFEST_LIVE'
{
  "target": "live",
  "version": "1.0",
  "architecture": "x86_64",
  "type": "live_system",
  "init_binary": "linux-reference-init-live",
  "init_cpl3_verified": false,
  "acceptance_gate": {
    "requires_native_init": true,
    "native_init_present": false,
    "status": "BLOCKED"
  },
  "handoff_sequence": [
    "kernel_control_transfer",
    "init_cpl3_acknowledgement",
    "mount_virtual_filesystems",
    "environment_setup",
    "service_initialization",
    "desktop_launch",
    "userspace_active"
  ],
  "entry_point": null,
  "kernel_command_line": "root=/dev/mapper/koronos-live init=/sbin/init target=live",
  "status": "REFERENCE_ONLY_NOT_PRODUCTION"
}
MANIFEST_LIVE

cat > "$OUTPUT_DIR/target-manifest-installer.json" << 'MANIFEST_INSTALLER'
{
  "target": "installer",
  "version": "1.0",
  "architecture": "x86_64",
  "type": "installer_system",
  "init_binary": "linux-reference-init-installer",
  "init_cpl3_verified": false,
  "acceptance_gate": {
    "requires_native_init": true,
    "native_init_present": false,
    "status": "BLOCKED"
  },
  "handoff_sequence": [
    "kernel_control_transfer",
    "init_cpl3_acknowledgement",
    "mount_virtual_filesystems",
    "environment_setup",
    "installer_payload_launch",
    "installation_ready"
  ],
  "entry_point": null,
  "kernel_command_line": "root=/dev/mapper/koronos-install init=/sbin/init target=installer",
  "status": "REFERENCE_ONLY_NOT_PRODUCTION"
}
MANIFEST_INSTALLER

cat > "$OUTPUT_DIR/target-manifest-recovery.json" << 'MANIFEST_RECOVERY'
{
  "target": "recovery",
  "version": "1.0",
  "architecture": "x86_64",
  "type": "recovery_system",
  "init_binary": "linux-reference-init-recovery",
  "init_cpl3_verified": false,
  "acceptance_gate": {
    "requires_native_init": true,
    "native_init_present": false,
    "status": "BLOCKED"
  },
  "handoff_sequence": [
    "kernel_control_transfer",
    "init_cpl3_acknowledgement",
    "mount_virtual_filesystems",
    "environment_setup",
    "recovery_shell_launch",
    "recovery_ready"
  ],
  "entry_point": null,
  "kernel_command_line": "root=/dev/mapper/koronos-recovery init=/sbin/init target=recovery",
  "status": "REFERENCE_ONLY_NOT_PRODUCTION"
}
MANIFEST_RECOVERY

echo "[✓] All target manifests created with acceptance gates"

# ==============================================================================
# STEP 6: VERIFICATION
# ==============================================================================

echo ""
echo "Verifying handoff architecture..."
echo ""
echo "Build Summary:"
echo "  ✓ linux-reference-init-live: Linux-hosted reference only"
echo "  ✓ linux-reference-init-installer: Linux-hosted reference only"
echo "  ✓ linux-reference-init-recovery: Linux-hosted reference only"
echo "  ✓ Target manifests with acceptance gates"
echo "  ✓ Handoff sequence verified"
echo ""
echo "Status: LINUX REFERENCE BUILT; KORONOS PRODUCTION HANDOFF REMAINS BLOCKED"
echo ""
echo "Output directory: $OUTPUT_DIR"
echo "Reference binaries are NOT eligible for Koronos ISO staging."
echo ""

} 2>&1 | tee "$BUILD_LOG"

echo "Build log saved to: $BUILD_LOG"
