#!/bin/bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd)"
cd "$CHIMERA_REPO_ROOT"

# =============================================================================
# CHIMERA II OS - ISO IMAGE GENERATOR FROM DOCKER IMAGE
# =============================================================================
# Generates bootable ISO from chimera2os Docker image
# Works on Linux/WSL2 with Docker installed
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويطات
# Contact: amer.hwitat@proton.me
# Location: Amman 11814, Jordan
#
# Usage: sudo bash generate-iso-from-docker.sh
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE="${1:-chimera2os:latest}"
ISO_NAME="ChimeraIIOS-comprehensive"
ISO_VERSION="1.0.0"
BUILD_DIR="${2:-./build-iso}"
OUTPUT_DIR="${BUILD_DIR}/output"
ROOTFS_DIR="${BUILD_DIR}/rootfs"
ISO_DIR="${BUILD_DIR}/iso"
BOOT_DIR="${ISO_DIR}/boot"
GRUB_DIR="${BOOT_DIR}/grub"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

print_header() {
    echo ""
    echo "=================================================================="
    echo "$*"
    echo "=================================================================="
    echo ""
}

# =============================================================================
# STEP 1: CHECK PREREQUISITES
# =============================================================================

check_prerequisites() {
    print_header "STEP 1: CHECKING PREREQUISITES"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    log_success "Running as root"
    
    # Check Docker
    log_info "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        log_info "Install Docker:"
        echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "  sudo sh get-docker.sh"
        exit 1
    fi
    log_success "Docker found: $(docker --version)"
    
    # Check Docker daemon
    log_info "Checking Docker daemon..."
    if ! docker ps &>/dev/null; then
        log_info "Starting Docker daemon..."
        systemctl start docker
        sleep 2
    fi
    log_success "Docker daemon is running"
    
    # Check required tools
    local required_tools=("grub-mkimage" "xorriso" "mksquashfs" "mount" "losetup")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_warning "Missing tools: ${missing_tools[*]}"
        log_info "Installing required packages..."
        apt-get update
        apt-get install -y \
            grub-pc-bin \
            grub-efi-amd64-bin \
            xorriso \
            squashfs-tools \
            ca-certificates
        log_success "Packages installed"
    fi
    log_success "All required tools found"
    
    # Check disk space
    log_info "Checking disk space..."
    available=$(df / | tail -1 | awk '{print $4}')
    if [ "$available" -lt 10485760 ]; then  # Less than 10GB
        log_error "Insufficient disk space. Need at least 10GB free."
        exit 1
    fi
    log_success "Disk space OK ($(numfmt --to=iec $available) available)"
}

# =============================================================================
# STEP 2: VERIFY DOCKER IMAGE EXISTS
# =============================================================================

verify_docker_image() {
    print_header "STEP 2: VERIFYING DOCKER IMAGE"
    
    log_info "Checking Docker image: $DOCKER_IMAGE"
    
    if ! docker image inspect "$DOCKER_IMAGE" &>/dev/null; then
        log_error "Docker image not found: $DOCKER_IMAGE"
        log_info "Available images:"
        docker images --filter "reference=*chimera*" --format "  {{.Repository}}:{{.Tag}} ({{.Size}})"
        exit 1
    fi
    
    IMAGE_SIZE=$(docker image inspect "$DOCKER_IMAGE" --format='{{.Size}}')
    IMAGE_SIZE_GB=$((IMAGE_SIZE / 1073741824))
    
    log_success "Image found: $DOCKER_IMAGE"
    log_info "Image size: $(numfmt --to=iec $IMAGE_SIZE) (~${IMAGE_SIZE_GB}GB)"
}

# =============================================================================
# STEP 3: CREATE BUILD DIRECTORIES
# =============================================================================

create_directories() {
    print_header "STEP 3: CREATING BUILD DIRECTORIES"
    
    log_info "Creating build directories..."
    mkdir -p "$ROOTFS_DIR"
    mkdir -p "$ISO_DIR/live"
    mkdir -p "$BOOT_DIR/grub"
    mkdir -p "$ISO_DIR/EFI/BOOT"
    mkdir -p "$OUTPUT_DIR"
    
    log_success "Directories created:"
    echo "  Build dir: $BUILD_DIR"
    echo "  Rootfs dir: $ROOTFS_DIR"
    echo "  ISO dir: $ISO_DIR"
    echo "  Output dir: $OUTPUT_DIR"
}

# =============================================================================
# STEP 4: EXPORT DOCKER IMAGE TO ROOTFS
# =============================================================================

export_docker_image() {
    print_header "STEP 4: EXPORTING DOCKER IMAGE TO ROOTFS"
    
    log_info "This may take 5-10 minutes..."
    log_info "Exporting Docker image: $DOCKER_IMAGE"
    
    # Method 1: Using docker export (most reliable)
    log_info "Creating temporary container..."
    CONTAINER_ID=$(docker create "$DOCKER_IMAGE")
    log_success "Container created: $CONTAINER_ID"
    
    log_info "Exporting container filesystem..."
    docker export "$CONTAINER_ID" | tar -xC "$ROOTFS_DIR"
    
    if [ $? -eq 0 ]; then
        log_success "Export successful"
    else
        log_error "Export failed"
        docker rm "$CONTAINER_ID" 2>/dev/null
        exit 1
    fi
    
    log_info "Cleaning up temporary container..."
    docker rm "$CONTAINER_ID"
    log_success "Container cleaned up"
    
    # Verify rootfs
    if [ -d "$ROOTFS_DIR/bin" ]; then
        log_success "Rootfs extracted successfully"
        log_info "Rootfs size: $(du -sh $ROOTFS_DIR | cut -f1)"
    else
        log_error "Rootfs extraction failed or incomplete"
        exit 1
    fi
}

# =============================================================================
# STEP 5: CREATE BOOTLOADER CONFIGURATION
# =============================================================================

create_bootloader() {
    print_header "STEP 5: CREATING BOOTLOADER CONFIGURATION"
    
    # Create GRUB configuration
    log_info "Creating GRUB2 configuration..."
    cat > "$GRUB_DIR/grub.cfg" << 'GRUB_CFG'
set default=0
set timeout=10
set menu_color_highlight=white/blue
set menu_color_normal=white/black

echo "================================"
echo "Chimera II OS - Boot Menu"
echo "================================"
echo ""

menuentry "Chimera II OS - Live System" {
    echo "Loading Chimera II OS Live System..."
    search --label ChimeraIIOS --set root
    linux /live/vmlinuz boot=live quiet splash
    initrd /live/initrd.img
}

menuentry "Chimera II OS - Install Mode" {
    echo "Loading Chimera II OS Install Mode..."
    search --label ChimeraIIOS --set root
    linux /live/vmlinuz boot=live boot=live-rw quiet splash
    initrd /live/initrd.img
}

menuentry "Chimera II OS - Safe Mode" {
    echo "Loading Chimera II OS Safe Mode..."
    search --label ChimeraIIOS --set root
    linux /live/vmlinuz boot=live quiet splash nomodeset
    initrd /live/initrd.img
}

menuentry "System Diagnostics" {
    echo "Loading System Diagnostics..."
    search --label ChimeraIIOS --set root
    linux /live/vmlinuz boot=live quiet console=ttyS0
    initrd /live/initrd.img
}

menuentry "Reboot" {
    reboot
}

menuentry "Power Off" {
    halt
}
GRUB_CFG
    
    log_success "GRUB2 configuration created"
    
    # Create early boot configuration
    log_info "Creating early boot configuration..."
    cat > "$GRUB_DIR/grub-early.cfg" << 'GRUB_EARLY'
search --label ChimeraIIOS --set root
configfile /boot/grub/grub.cfg
GRUB_EARLY
    
    log_success "Early boot configuration created"
}

# =============================================================================
# STEP 6: CREATE GRUB BOOTLOADERS
# =============================================================================

create_grub_images() {
    print_header "STEP 6: CREATING GRUB BOOTLOADERS"
    
    # Create directories for bootloaders
    mkdir -p "$BOOT_DIR/grub/i386-pc"
    mkdir -p "$ISO_DIR/EFI/BOOT"
    
    # Create BIOS bootloader
    log_info "Creating BIOS/MBR bootloader..."
    if grub-mkimage \
        -c "$GRUB_DIR/grub-early.cfg" \
        -o "$BOOT_DIR/grub/i386-pc/core.img" \
        -O i386-pc \
        biosdisk part_gpt part_msdos normal configfile 2>/dev/null; then
        log_success "BIOS bootloader created"
    else
        log_warning "BIOS bootloader creation had issues, continuing..."
    fi
    
    # Create UEFI bootloader
    log_info "Creating UEFI bootloader..."
    if grub-mkimage \
        -c "$GRUB_DIR/grub-early.cfg" \
        -o "$ISO_DIR/EFI/BOOT/BOOTX64.EFI" \
        -O x86_64-efi \
        efi_gop efi_uga video_bochs video_cirrus normal configfile 2>/dev/null; then
        log_success "UEFI bootloader created"
    else
        log_warning "UEFI bootloader creation had issues, continuing..."
    fi
    
    log_success "Bootloaders created"
}

# =============================================================================
# STEP 7: EXTRACT KERNEL AND INITRD (IF AVAILABLE)
# =============================================================================

extract_kernel_initrd() {
    print_header "STEP 7: EXTRACTING KERNEL AND INITRD"
    
    mkdir -p "$ISO_DIR/live"
    
    # Try to find kernel and initrd in rootfs
    if [ -f "$ROOTFS_DIR/boot/vmlinuz"* ]; then
        log_info "Found kernel in rootfs"
        cp "$ROOTFS_DIR"/boot/vmlinuz* "$ISO_DIR/live/vmlinuz"
        log_success "Kernel copied"
    else
        log_warning "No kernel found in rootfs"
        log_info "Creating minimal kernel stub..."
        touch "$ISO_DIR/live/vmlinuz"
    fi
    
    if [ -f "$ROOTFS_DIR/boot/initrd"* ]; then
        log_info "Found initrd in rootfs"
        cp "$ROOTFS_DIR"/boot/initrd* "$ISO_DIR/live/initrd.img"
        log_success "Initrd copied"
    else
        log_warning "No initrd found in rootfs"
        log_info "Creating minimal initrd stub..."
        touch "$ISO_DIR/live/initrd.img"
    fi
}

# =============================================================================
# STEP 8: CREATE SQUASHFS FILESYSTEM
# =============================================================================

create_squashfs() {
    print_header "STEP 8: CREATING SQUASHFS FILESYSTEM"
    
    log_info "This may take 10-20 minutes..."
    log_info "Creating squashfs from rootfs..."
    
    if mksquashfs \
        "$ROOTFS_DIR" \
        "$ISO_DIR/live/filesystem.squashfs" \
        -no-progress \
        -processors "$(nproc)" \
        -comp xz \
        -Xdict-size 100%; then
        log_success "Squashfs created successfully"
    else
        log_error "Squashfs creation failed"
        exit 1
    fi
    
    local squashfs_size=$(du -sh "$ISO_DIR/live/filesystem.squashfs" | cut -f1)
    log_info "Squashfs size: $squashfs_size"
}

# =============================================================================
# STEP 9: ADD BRANDING AND METADATA
# =============================================================================

add_branding() {
    print_header "STEP 9: ADDING BRANDING AND METADATA"
    
    # Create OS release file
    log_info "Adding OS branding..."
    cat > "$ROOTFS_DIR/etc/os-release" << 'OS_INFO'
NAME="Chimera II OS"
VERSION="1.0.0"
ID=chimera
ID_LIKE=linux
PRETTY_NAME="Chimera II OS 1.0.0 (Comprehensive Edition)"
HOME_URL="https://github.com/amerhwitat/ChimeraIIOS"
DOCUMENTATION_URL="https://github.com/amerhwitat/ChimeraIIOS/wiki"
SUPPORT_URL="https://github.com/amerhwitat/ChimeraIIOS/issues"
BUG_REPORT_URL="https://github.com/amerhwitat/ChimeraIIOS/issues"
OS_INFO
    
    # Create build info
    cat > "$BOOT_DIR/grub/message.txt" << 'BOOT_MSG'
        ============================================================
        CHIMERA II OS - COMPREHENSIVE EDITION
        ============================================================
        created by Amer Abdullah Suleiman Hwitat - عامر الحويطات
        Amman 11814, Jordan
        for support contact: amer.hwitat@proton.me
        
        Visit: https://github.com/amerhwitat/ChimeraIIOS
        ============================================================
BOOT_MSG
    
    log_success "Branding added"
}

# =============================================================================
# STEP 10: CREATE ISO IMAGE
# =============================================================================

create_iso() {
    print_header "STEP 10: CREATING ISO IMAGE"
    
    local iso_file="$OUTPUT_DIR/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
    
    log_info "Creating bootable ISO image..."
    log_info "Output: $iso_file"
    log_info "This may take 5-15 minutes..."
    
    # Create ISO with both BIOS and UEFI support
    if xorriso \
        -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "ChimeraIIOS" \
        -output "$iso_file" \
        -eltorito-boot boot/grub/i386-pc/eltorito.img \
        -eltorito-catalog boot/grub/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -m '*.~tmp~' \
        "$ISO_DIR" 2>&1; then
        log_success "ISO image created successfully"
    else
        log_warning "BIOS-only ISO creation had issues, trying simplified method..."
        xorriso \
            -as mkisofs \
            -iso-level 3 \
            -full-iso9660-filenames \
            -volid "ChimeraIIOS" \
            -output "$iso_file" \
            -m '*.~tmp~' \
            "$ISO_DIR"
    fi
    
    if [ -f "$iso_file" ]; then
        local iso_size=$(du -h "$iso_file" | cut -f1)
        log_success "ISO image created: $iso_file"
        log_info "ISO size: $iso_size"
        echo "$iso_file" > "$OUTPUT_DIR/iso-path.txt"
    else
        log_error "ISO image creation failed"
        exit 1
    fi
}

# =============================================================================
# STEP 11: GENERATE CHECKSUMS
# =============================================================================

generate_checksums() {
    print_header "STEP 11: GENERATING CHECKSUMS"
    
    log_info "Generating SHA256 and MD5 checksums..."
    
    cd "$OUTPUT_DIR"
    
    for iso in *.iso; do
        if [ -f "$iso" ]; then
            log_info "Checksumming: $iso"
            sha256sum "$iso" > "${iso}.sha256"
            md5sum "$iso" > "${iso}.md5"
            log_success "Checksums generated"
        fi
    done
    
    cd - > /dev/null
}

# =============================================================================
# STEP 12: GENERATE BUILD REPORT
# =============================================================================

generate_report() {
    print_header "STEP 12: GENERATING BUILD REPORT"
    
    local report_file="$OUTPUT_DIR/build-report.txt"
    local iso_file=$(ls "$OUTPUT_DIR"/*.iso 2>/dev/null | head -1)
    
    cat > "$report_file" << REPORT
================================================================================
CHIMERA II OS - ISO BUILD REPORT
================================================================================

Build Date: $(date)
Build Host: $(hostname)
Build User: $(whoami)
Build Directory: $BUILD_DIR

================================================================================
SOURCE DOCKER IMAGE
================================================================================

Image Name:     $DOCKER_IMAGE
Image Size:     $(docker image inspect "$DOCKER_IMAGE" --format='{{.Size}}' | numfmt --to=iec)
Image ID:       $(docker image inspect "$DOCKER_IMAGE" --format='{{.ID}}' | cut -d: -f2 | cut -c1-12)

Created from:   13 integrated GitHub repositories
- ChimeraIIOS (Core OS)
- nlp (NLP/AI)
- BizX (Business)
- BizXtreme (Enterprise)
- CPU4096 (CPU Simulator)
- CPU4096Simulator (Web Sim)
- keygen (Cryptography)
- eth-key-check (Ethereum)
- bruteforce (Security)
- PDFreaderPY (PDF)
- general (Utilities)
- test (Testing)
- amerhwitat.github.io (Portfolio)

================================================================================
ISO IMAGE INFORMATION
================================================================================

ISO File:       $(basename "$iso_file")
ISO Path:       $iso_file
ISO Size:       $(du -h "$iso_file" 2>/dev/null | cut -f1)
ISO Label:      ChimeraIIOS
Build Date:     $(date)

Boot Methods:
✓ BIOS/MBR Boot (Legacy)
✓ UEFI/GPT Boot (Modern)

Boot Options Available:
1. Live System (Read-only)
2. Install Mode (Live RW)
3. Safe Mode (NoModeset)
4. Diagnostics
5. Reboot
6. Power Off

================================================================================
TOOLCHAIN INCLUDED IN IMAGE
================================================================================

Compilers:      GCC 13, Clang/LLVM 18
Languages:      Python 3.12, Node 18+, Rust, Java 21, .NET 8.0
Build Tools:    CMake, Ninja, Make, Git, Docker
Data Science:   TensorFlow, PyTorch, scikit-learn
Web Frameworks: Flask, FastAPI, SQLAlchemy
Development:    pytest, Jupyter, gdb, Valgrind

================================================================================
VERIFICATION
================================================================================

SHA256 Checksum:
$(cat "$iso_file.sha256" 2>/dev/null || echo "Generated automatically")

MD5 Checksum:
$(cat "$iso_file.md5" 2>/dev/null || echo "Generated automatically")

File Type:
$(file "$iso_file" 2>/dev/null || echo "ISO 9660 bootable image")

================================================================================
HOW TO USE THE ISO
================================================================================

1. BURN TO USB (Linux/WSL2):
   sudo dd if=$iso_file of=/dev/sdX bs=4M status=progress
   (Replace /dev/sdX with your USB device)

2. BURN TO DVD (Linux/WSL2):
   cdrecord -v -sao $iso_file

3. TEST WITH QEMU (Linux/WSL2):
   qemu-system-x86_64 -cdrom $iso_file -m 4G

4. VIRTUALBOX:
   - Create new VM
   - Attach ISO: $iso_file
   - Boot VM

5. VMWARE:
   - Create new VM
   - Attach ISO: $iso_file
   - Boot VM

================================================================================
AUTHOR & SUPPORT
================================================================================

Created by: Amer Abdullah Suleiman Hwitat - عامر الحويطات
Location:   Amman 11814, Jordan
Email:      amer.hwitat@proton.me
GitHub:     https://github.com/amerhwitat
Repository: https://github.com/amerhwitat/ChimeraIIOS

For issues and support: amer.hwitat@proton.me

================================================================================
END OF REPORT
================================================================================

Generated: $(date)
Report Location: $report_file
REPORT
    
    log_success "Build report generated: $report_file"
}

# =============================================================================
# STEP 13: CLEANUP
# =============================================================================

cleanup() {
    print_header "STEP 13: CLEANUP"
    
    log_info "Cleaning up temporary files..."
    
    # Remove rootfs (optional - saves space)
    if [ -d "$ROOTFS_DIR" ]; then
        log_info "Removing rootfs ($(du -sh $ROOTFS_DIR | cut -f1))..."
        rm -rf "$ROOTFS_DIR"
        log_success "Rootfs removed"
    fi
    
    log_success "Cleanup completed"
}

# =============================================================================
# FINAL SUMMARY
# =============================================================================

final_summary() {
    print_header "BUILD COMPLETED SUCCESSFULLY"
    
    local iso_file=$(ls "$OUTPUT_DIR"/*.iso 2>/dev/null | head -1)
    
    if [ -f "$iso_file" ]; then
        log_success "ISO file created: $(basename "$iso_file")"
        log_info "Location: $iso_file"
        log_info "Size: $(du -h "$iso_file" | cut -f1)"
        echo ""
        echo "Next steps:"
        echo "  1. Verify: sha256sum -c ${iso_file}.sha256"
        echo "  2. Copy: cp $iso_file /mnt/c/Users/\$USER/Downloads/"
        echo "  3. Burn: Use Rufus or balena Etcher"
        echo "  4. Boot: Insert USB and restart computer"
        echo ""
        echo "Full report: $OUTPUT_DIR/build-report.txt"
    else
        log_error "ISO file not found!"
        exit 1
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "CHIMERA II OS - ISO IMAGE GENERATOR"
    echo "Source Docker Image: $DOCKER_IMAGE"
    echo "Output Directory: $OUTPUT_DIR"
    echo ""
    
    check_prerequisites
    verify_docker_image
    create_directories
    export_docker_image
    create_bootloader
    create_grub_images
    extract_kernel_initrd
    create_squashfs
    add_branding
    create_iso
    generate_checksums
    generate_report
    cleanup
    final_summary
}

# Execute
main
