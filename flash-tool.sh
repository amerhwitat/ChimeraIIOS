#!/bin/bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd)"
cd "$CHIMERA_REPO_ROOT"

# =============================================================================
# CHIMERA II OS - FLASH TOOL
# =============================================================================
# Flash Chimera II OS to USB or mobile devices
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحowiتات
# Contact: amer.hwitat@proton.me
#
# Supported targets:
# - USB drives (x86_64)
# - Mobile devices (ARM64)
# - SD cards (Raspberry Pi, etc.)
# - Partition flashing
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "CHIMERA II OS - FLASH TOOL"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    log_success "Running as root"
    
    # Get ISO file
    if [ -z "$1" ]; then
        log_error "Usage: sudo bash flash-tool.sh <iso-file> <device>"
        log_info "Example: sudo bash flash-tool.sh chimera.iso /dev/sdX"
        exit 1
    fi
    
    ISO_FILE="$1"
    DEVICE="${2:-}"
    
    # Verify ISO exists
    if [ ! -f "$ISO_FILE" ]; then
        log_error "ISO file not found: $ISO_FILE"
        exit 1
    fi
    
    log_info "ISO file: $ISO_FILE"
    log_info "Size: $(du -h $ISO_FILE | cut -f1)"
    
    # List available devices
    log_info "Available devices:"
    lsblk | grep -E "^sd|^hd|^nvme"
    echo ""
    
    # Get target device
    if [ -z "$DEVICE" ]; then
        log_warning "No device specified"
        read -p "Enter device (e.g., /dev/sdX): " DEVICE
    fi
    
    # Verify device
    if [ ! -b "$DEVICE" ]; then
        log_error "Device not found: $DEVICE"
        exit 1
    fi
    
    # Unmount device
    log_info "Unmounting $DEVICE..."
    for partition in ${DEVICE}*; do
        if mountpoint -q "$partition"; then
            log_info "Unmounting $partition..."
            umount "$partition" || log_warning "Failed to unmount $partition"
        fi
    done
    log_success "Device unmounted"
    
    # Flash ISO
    log_info "Flashing ISO to $DEVICE..."
    log_warning "This will erase all data on $DEVICE!"
    read -p "Continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_error "Cancelled"
        exit 1
    fi
    
    log_info "Starting flash process..."
    dd if="$ISO_FILE" of="$DEVICE" bs=4M status=progress
    
    if [ $? -eq 0 ]; then
        log_success "ISO flashed successfully"
    else
        log_error "Flash failed"
        exit 1
    fi
    
    # Sync
    log_info "Syncing filesystem..."
    sync
    log_success "Flash complete"
    
    # Eject
    log_info "Ejecting device..."
    eject "$DEVICE" 2>/dev/null || udisksctl power-off -b "$DEVICE" 2>/dev/null || log_warning "Could not eject device"
    
    log_success "Ready to boot from $DEVICE"
}

# Execute
main "$@"
