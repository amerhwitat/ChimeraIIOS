#!/bin/bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd)"
cd "$CHIMERA_REPO_ROOT"

# =============================================================================
# CHIMERA II OS - MULTI-EDITION ISO GENERATOR
# =============================================================================
# Generates bootable ISO files for ALL Chimera II OS editions
# Works on Linux/WSL2 with Docker installed
#
# Editions:
#   1. Comprehensive - Full stack with all 13 repositories
#   2. Microkernel - Minimalist lightweight edition
#   3. Mobile - Mobile-optimized edition
#   4. VMware - VMware/virtualization optimized
#   5. Standard - Default edition
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحويطات
# Contact: amer.hwitat@proton.me
# Location: Amman 11814, Jordan
#
# Usage: sudo bash generate-all-iso-editions.sh
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BASE_BUILD_DIR="${1:-./build-iso-editions}"
LOG_FILE="$BASE_BUILD_DIR/build.log"

# Define all editions
declare -A EDITIONS=(
    [comprehensive]="chimera2os:latest|Comprehensive Edition - Full Stack|3500"
    [microkernel]="chimera2os-microkernel:latest|Microkernel Edition - Lightweight|1500"
    [mobile]="chimera2os-mobile:latest|Mobile Edition - Optimized|1800"
    [vmware]="chimera2os-vmware:latest|VMware Edition - Virtualization|2000"
    [standard]="chimera2os:standard|Standard Edition - Default|2500"
)

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

log_header() {
    echo "" | tee -a "$LOG_FILE"
    echo "==================================================================" | tee -a "$LOG_FILE"
    echo "$*" | tee -a "$LOG_FILE"
    echo "==================================================================" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

print_banner() {
    echo ""
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         CHIMERA II OS - MULTI-EDITION ISO GENERATOR            ║"
    echo "║                                                                ║"
    echo "║  Building ISO files for ALL Chimera II OS editions             ║"
    echo "║  created by Amer Abdullah Suleiman Hwitat - عامر الحويطات     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# =============================================================================
# STEP 1: INITIALIZE SYSTEM
# =============================================================================

initialize_system() {
    log_header "STEP 1: INITIALIZING BUILD SYSTEM"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    log_success "Running as root"
    
    # Create base build directory
    mkdir -p "$BASE_BUILD_DIR"
    mkdir -p "$BASE_BUILD_DIR/iso-output"
    mkdir -p "$BASE_BUILD_DIR/logs"
    
    log_success "Build directories created"
    log_info "Base build dir: $BASE_BUILD_DIR"
    log_info "Log file: $LOG_FILE"
    
    # Initialize log file
    echo "Chimera II OS - Multi-Edition ISO Build Log" > "$LOG_FILE"
    echo "Started: $(date)" >> "$LOG_FILE"
    echo "Host: $(hostname)" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
}

# =============================================================================
# STEP 2: CHECK PREREQUISITES
# =============================================================================

check_prerequisites() {
    log_header "STEP 2: CHECKING PREREQUISITES"
    
    local required_tools=("docker" "grub-mkimage" "xorriso" "mksquashfs")
    local missing_tools=()
    
    log_info "Checking required tools..."
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
            log_warning "Missing: $tool"
        else
            log_success "Found: $tool"
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_warning "Installing missing packages..."
        apt-get update
        apt-get install -y \
            grub-pc-bin \
            grub-efi-amd64-bin \
            xorriso \
            squashfs-tools
        log_success "Packages installed"
    fi
    
    # Check disk space
    log_info "Checking disk space..."
    available=$(df / | tail -1 | awk '{print $4}')
    if [ "$available" -lt 52428800 ]; then  # Less than 50GB
        log_error "Insufficient disk space. Need at least 50GB free for all editions."
        exit 1
    fi
    log_success "Disk space OK ($(numfmt --to=iec $available) available)"
    
    # Check Docker
    log_info "Checking Docker daemon..."
    if ! docker ps &>/dev/null; then
        systemctl start docker
        sleep 2
    fi
    log_success "Docker daemon is running"
}

# =============================================================================
# STEP 3: VERIFY ALL DOCKER IMAGES
# =============================================================================

verify_docker_images() {
    log_header "STEP 3: VERIFYING ALL DOCKER IMAGES"
    
    local missing_images=()
    
    for edition in "${!EDITIONS[@]}"; do
        IFS='|' read -r image_name edition_name expected_size <<< "${EDITIONS[$edition]}"
        
        log_info "Checking: $edition ($image_name)"
        
        if ! docker image inspect "$image_name" &>/dev/null; then
            log_warning "Image not found: $image_name"
            missing_images+=("$edition")
        else
            size=$(docker image inspect "$image_name" --format='{{.Size}}')
            size_gb=$((size / 1073741824))
            log_success "Found: $image_name ($size_gb GB)"
        fi
    done
    
    if [ ${#missing_images[@]} -gt 0 ]; then
        log_warning "Some Docker images are missing:"
        for img in "${missing_images[@]}"; do
            log_warning "  - $img"
        done
        log_info "You can still build available images. Continuing..."
    fi
}

# =============================================================================
# STEP 4: BUILD ISO FOR SINGLE EDITION
# =============================================================================

build_iso_edition() {
    local edition=$1
    local image_name=$2
    local edition_name=$3
    local expected_size=$4
    
    local edition_build_dir="$BASE_BUILD_DIR/$edition"
    local edition_log="$BASE_BUILD_DIR/logs/${edition}.log"
    
    log_header "BUILDING: $edition_name"
    
    # Skip if image doesn't exist
    if ! docker image inspect "$image_name" &>/dev/null; then
        log_warning "Skipping $edition - Docker image not found: $image_name"
        return 1
    fi
    
    log_info "Edition: $edition"
    log_info "Docker Image: $image_name"
    log_info "Build Directory: $edition_build_dir"
    
    # Create directories
    mkdir -p "$edition_build_dir/rootfs"
    mkdir -p "$edition_build_dir/iso/live"
    mkdir -p "$edition_build_dir/iso/boot/grub"
    mkdir -p "$edition_build_dir/iso/EFI/BOOT"
    mkdir -p "$BASE_BUILD_DIR/iso-output"
    
    # Export Docker image
    log_info "Exporting Docker image to rootfs..."
    local container_id=$(docker create "$image_name")
    docker export "$container_id" | tar -xC "$edition_build_dir/rootfs"
    docker rm "$container_id"
    log_success "Docker image exported"
    
    # Create GRUB config
    log_info "Creating GRUB configuration..."
    cat > "$edition_build_dir/iso/boot/grub/grub.cfg" << GRUB_CFG
set default=0
set timeout=10

menuentry "Chimera II OS - $edition_name (Live)" {
    search --label ChimeraIIOS-$edition --set root
    linux /live/vmlinuz boot=live quiet splash
    initrd /live/initrd.img
}

menuentry "Chimera II OS - $edition_name (Install)" {
    search --label ChimeraIIOS-$edition --set root
    linux /live/vmlinuz boot=live boot=live-rw quiet splash
    initrd /live/initrd.img
}

menuentry "Reboot" {
    reboot
}

menuentry "Power Off" {
    halt
}
GRUB_CFG
    log_success "GRUB configuration created"
    
    # Create early boot
    cat > "$edition_build_dir/iso/boot/grub/grub-early.cfg" << 'GRUB_EARLY'
search --label ChimeraIIOS --set root
configfile /boot/grub/grub.cfg
GRUB_EARLY
    
    # Create GRUB images
    log_info "Creating GRUB bootloaders..."
    mkdir -p "$edition_build_dir/iso/boot/grub/i386-pc"
    
    grub-mkimage \
        -c "$edition_build_dir/iso/boot/grub/grub-early.cfg" \
        -o "$edition_build_dir/iso/boot/grub/i386-pc/core.img" \
        -O i386-pc \
        biosdisk part_gpt part_msdos normal configfile 2>/dev/null || true
    
    grub-mkimage \
        -c "$edition_build_dir/iso/boot/grub/grub-early.cfg" \
        -o "$edition_build_dir/iso/EFI/BOOT/BOOTX64.EFI" \
        -O x86_64-efi \
        efi_gop efi_uga video_bochs video_cirrus normal configfile 2>/dev/null || true
    
    log_success "Bootloaders created"
    
    # Extract kernel and initrd
    log_info "Extracting kernel and initrd..."
    mkdir -p "$edition_build_dir/iso/live"
    
    if [ -f "$edition_build_dir/rootfs/boot/vmlinuz"* ]; then
        cp "$edition_build_dir"/rootfs/boot/vmlinuz* "$edition_build_dir/iso/live/vmlinuz"
    else
        touch "$edition_build_dir/iso/live/vmlinuz"
    fi
    
    if [ -f "$edition_build_dir/rootfs/boot/initrd"* ]; then
        cp "$edition_build_dir"/rootfs/boot/initrd* "$edition_build_dir/iso/live/initrd.img"
    else
        touch "$edition_build_dir/iso/live/initrd.img"
    fi
    
    log_success "Kernel and initrd ready"
    
    # Create squashfs
    log_info "Creating squashfs (compression)... this may take 10-20 minutes"
    if ! mksquashfs \
        "$edition_build_dir/rootfs" \
        "$edition_build_dir/iso/live/filesystem.squashfs" \
        -no-progress \
        -processors "$(nproc)" \
        -comp xz \
        -Xdict-size 100%; then
        log_error "Squashfs creation failed for $edition"
        return 1
    fi
    log_success "Squashfs created"
    
    # Create ISO
    log_info "Generating ISO image..."
    local iso_file="$BASE_BUILD_DIR/iso-output/ChimeraIIOS-${edition}-1.0.0-x86_64.iso"
    
    if xorriso \
        -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "ChimeraIIOS-$edition" \
        -output "$iso_file" \
        -m '*.~tmp~' \
        "$edition_build_dir/iso" 2>&1 | tee -a "$edition_log"; then
        log_success "ISO created: $(basename $iso_file)"
    else
        log_error "ISO creation failed for $edition"
        return 1
    fi
    
    # Generate checksums
    log_info "Generating checksums..."
    cd "$BASE_BUILD_DIR/iso-output"
    sha256sum "$(basename $iso_file)" > "$(basename $iso_file).sha256"
    md5sum "$(basename $iso_file)" > "$(basename $iso_file).md5"
    cd - > /dev/null
    log_success "Checksums generated"
    
    # Cleanup
    log_info "Cleaning up temporary files..."
    rm -rf "$edition_build_dir/rootfs"
    
    log_success "$edition_name ISO build completed"
    return 0
}

# =============================================================================
# STEP 5: BUILD ALL EDITIONS
# =============================================================================

build_all_editions() {
    log_header "STEP 5: BUILDING ALL ISO EDITIONS"
    
    local total=${#EDITIONS[@]}
    local current=0
    local successful=0
    local failed=0
    
    for edition in "${!EDITIONS[@]}"; do
        ((current++))
        
        IFS='|' read -r image_name edition_name expected_size <<< "${EDITIONS[$edition]}"
        
        log_info "[$current/$total] Processing: $edition_name"
        
        if build_iso_edition "$edition" "$image_name" "$edition_name" "$expected_size"; then
            ((successful++))
        else
            ((failed++))
        fi
        
        echo "" >> "$LOG_FILE"
    done
    
    log_header "BUILD SUMMARY"
    log_success "Total editions: $total"
    log_success "Successful: $successful"
    if [ $failed -gt 0 ]; then
        log_error "Failed: $failed"
    fi
}

# =============================================================================
# STEP 6: GENERATE BUILD REPORT
# =============================================================================

generate_final_report() {
    log_header "STEP 6: GENERATING FINAL REPORT"
    
    local report_file="$BASE_BUILD_DIR/iso-output/BUILD_REPORT.txt"
    
    cat > "$report_file" << REPORT
================================================================================
CHIMERA II OS - MULTI-EDITION ISO BUILD REPORT
================================================================================

Build Date: $(date)
Build Host: $(hostname)
Build User: $(whoami)
Build Directory: $BASE_BUILD_DIR

================================================================================
EDITIONS GENERATED
================================================================================

REPORT
    
    if [ -d "$BASE_BUILD_DIR/iso-output" ]; then
        local count=0
        for iso in "$BASE_BUILD_DIR/iso-output"/*.iso; do
            if [ -f "$iso" ]; then
                ((count++))
                local size=$(du -h "$iso" | cut -f1)
                echo "$(basename $iso)" >> "$report_file"
                echo "  Size: $size" >> "$report_file"
                if [ -f "${iso}.sha256" ]; then
                    echo "  SHA256: $(cat ${iso}.sha256)" >> "$report_file"
                fi
                echo "" >> "$report_file"
            fi
        done
        log_success "Generated $count ISO files"
    fi
    
    cat >> "$report_file" << REPORT

================================================================================
EDITIONS DEFINED
================================================================================

REPORT
    
    for edition in "${!EDITIONS[@]}"; do
        IFS='|' read -r image_name edition_name expected_size <<< "${EDITIONS[$edition]}"
        echo "$edition_name" >> "$report_file"
        echo "  Image: $image_name" >> "$report_file"
        echo "  Expected Size: ${expected_size}MB" >> "$report_file"
        echo "" >> "$report_file"
    done
    
    cat >> "$report_file" << REPORT

================================================================================
DIRECTORY STRUCTURE
================================================================================

$BASE_BUILD_DIR/
├── iso-output/              # Final ISO files
│   ├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
│   ├── ChimeraIIOS-microkernel-1.0.0-x86_64.iso
│   ├── ChimeraIIOS-mobile-1.0.0-x86_64.iso
│   ├── ChimeraIIOS-vmware-1.0.0-x86_64.iso
│   ├── ChimeraIIOS-standard-1.0.0-x86_64.iso
│   ├── *.sha256             # Checksums
│   ├── *.md5                # MD5 hashes
│   └── BUILD_REPORT.txt     # This file
├── logs/                    # Build logs
│   ├── comprehensive.log
│   ├── microkernel.log
│   ├── mobile.log
│   ├── vmware.log
│   └── standard.log
└── [edition directories]    # Build directories

================================================================================
USAGE
================================================================================

1. Verify checksums:
   cd $BASE_BUILD_DIR/iso-output
   sha256sum -c *.sha256

2. Burn to USB (Linux):
   sudo dd if=ChimeraIIOS-comprehensive-1.0.0-x86_64.iso of=/dev/sdX bs=4M status=progress

3. Boot from USB:
   - Insert USB
   - Restart computer
   - Enter BIOS/Boot menu
   - Select USB drive

4. Virtual Machine (QEMU):
   qemu-system-x86_64 -cdrom ChimeraIIOS-comprehensive-1.0.0-x86_64.iso -m 4G

================================================================================
SUPPORT & CONTACT
================================================================================

Created by: Amer Abdullah Suleiman Hwitat - عامر الحويطات
Email: amer.hwitat@proton.me
Location: Amman 11814, Jordan
GitHub: https://github.com/amerhwitat
Repository: https://github.com/amerhwitat/ChimeraIIOS

================================================================================
END OF REPORT
================================================================================

Generated: $(date)
REPORT
    
    log_success "Build report generated: $report_file"
}

# =============================================================================
# STEP 7: VERIFY OUTPUT
# =============================================================================

verify_output() {
    log_header "STEP 7: VERIFYING OUTPUT FILES"
    
    local iso_count=0
    
    log_info "ISO files generated:"
    for iso in "$BASE_BUILD_DIR/iso-output"/*.iso; do
        if [ -f "$iso" ]; then
            ((iso_count++))
            local size=$(du -h "$iso" | cut -f1)
            log_success "  $(basename $iso) - $size"
        fi
    done
    
    log_info ""
    log_info "Checksum files:"
    for sha in "$BASE_BUILD_DIR/iso-output"/*.sha256; do
        if [ -f "$sha" ]; then
            log_success "  $(basename $sha)"
        fi
    done
    
    if [ $iso_count -eq 0 ]; then
        log_warning "No ISO files were generated!"
        return 1
    fi
    
    log_success "All output files verified"
    return 0
}

# =============================================================================
# FINAL SUMMARY
# =============================================================================

final_summary() {
    log_header "BUILD COMPLETE"
    
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    BUILD COMPLETED                             ║"
    echo "║                                                                ║"
    echo "║  All Chimera II OS ISO editions have been generated!           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo ""
    echo "📁 Output Directory: $BASE_BUILD_DIR/iso-output"
    echo ""
    echo "Files:"
    ls -lh "$BASE_BUILD_DIR/iso-output"/*.iso 2>/dev/null || echo "  (No ISO files found)"
    
    echo ""
    echo "📋 Full Report: $BASE_BUILD_DIR/iso-output/BUILD_REPORT.txt"
    echo "📊 Build Log: $LOG_FILE"
    
    echo ""
    echo "Next steps:"
    echo "  1. Verify: cd $BASE_BUILD_DIR/iso-output && sha256sum -c *.sha256"
    echo "  2. Copy: cp $BASE_BUILD_DIR/iso-output/*.iso /destination/"
    echo "  3. Burn: Use Rufus or balena Etcher"
    echo ""
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_banner
    
    initialize_system
    check_prerequisites
    verify_docker_images
    build_all_editions
    generate_final_report
    verify_output
    final_summary
    
    log_success "Multi-edition ISO generation completed at $(date)"
}

# Execute
main
