#!/bin/bash

# =============================================================================
# CHIMERA II OS - ISO TOOL
# =============================================================================
# Manage and manipulate ISO images (extract, modify, repackage)
#
# Author: Amer Abdullah Suleiman Hwitat - عامر الحowiتات
# Contact: amer.hwitat@proton.me
#
# Operations:
# - Extract ISO contents
# - Modify files in ISO
# - Repackage into new ISO
# - Test/verify ISO integrity
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
ISO_FILE=""
WORK_DIR="./iso-work-$$"
OUTPUT_ISO=""
OPERATION=""

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }

print_header() {
    echo ""
    echo "=================================================================="
    echo "$*"
    echo "=================================================================="
    echo ""
}

print_usage() {
    cat << 'EOF'
CHIMERA II OS - ISO TOOL

Usage: iso-tool.sh <operation> <iso-file> [options]

Operations:
  extract    Extract ISO contents to directory
  repack     Repackage ISO from directory
  modify     Modify file in ISO
  verify     Verify ISO integrity
  info       Show ISO information
  test       Test ISO with QEMU

Examples:
  # Extract ISO
  ./iso-tool.sh extract chimera.iso

  # Modify file in ISO
  ./iso-tool.sh modify chimera.iso /path/in/iso /local/file

  # Repackage ISO
  ./iso-tool.sh repack chimera-modified.iso

  # Verify ISO
  ./iso-tool.sh verify chimera.iso

  # Show ISO info
  ./iso-tool.sh info chimera.iso

  # Test with QEMU
  ./iso-tool.sh test chimera.iso
EOF
}

extract_iso() {
    local iso="$1"
    local output="${2:-.}"
    
    print_header "EXTRACTING ISO"
    
    log_info "ISO: $iso"
    log_info "Output: $output"
    
    if [ ! -f "$iso" ]; then
        log_error "ISO file not found: $iso"
        exit 1
    fi
    
    mkdir -p "$output"
    
    log_info "Mounting ISO..."
    mkdir -p "$WORK_DIR/iso"
    mount -o loop "$iso" "$WORK_DIR/iso" || exit 1
    
    log_info "Copying files..."
    cp -r "$WORK_DIR/iso"/* "$output/" || true
    
    log_info "Unmounting..."
    umount "$WORK_DIR/iso"
    rm -rf "$WORK_DIR"
    
    log_success "ISO extracted to: $output"
}

repack_iso() {
    local source="${1:-.}"
    local output="${2:-chimera-repacked.iso}"
    
    print_header "REPACKING ISO"
    
    log_info "Source: $source"
    log_info "Output: $output"
    
    if [ ! -d "$source" ]; then
        log_error "Source directory not found: $source"
        exit 1
    fi
    
    log_info "Creating ISO..."
    xorriso -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "ChimeraIIOS" \
        -output "$output" \
        "$source"
    
    log_success "ISO created: $output"
    log_info "Size: $(du -h $output | cut -f1)"
}

modify_iso() {
    local iso="$1"
    local iso_path="$2"
    local local_file="$3"
    
    print_header "MODIFYING ISO"
    
    log_info "ISO: $iso"
    log_info "Path in ISO: $iso_path"
    log_info "Local file: $local_file"
    
    if [ ! -f "$iso" ]; then
        log_error "ISO not found: $iso"
        exit 1
    fi
    
    if [ ! -f "$local_file" ]; then
        log_error "Local file not found: $local_file"
        exit 1
    fi
    
    # Extract, modify, repack
    local extract_dir="$WORK_DIR/extracted"
    extract_iso "$iso" "$extract_dir"
    
    log_info "Modifying: $iso_path"
    mkdir -p "$(dirname "$extract_dir/$iso_path")"
    cp "$local_file" "$extract_dir/$iso_path"
    
    # Repack
    repack_iso "$extract_dir" "${iso%.iso}-modified.iso"
    
    rm -rf "$extract_dir"
    log_success "Modified ISO created"
}

verify_iso() {
    local iso="$1"
    
    print_header "VERIFYING ISO"
    
    log_info "ISO: $iso"
    
    # File check
    if [ ! -f "$iso" ]; then
        log_error "ISO file not found"
        exit 1
    fi
    
    # Size check
    local size=$(stat -f%z "$iso" 2>/dev/null || stat -c%s "$iso" 2>/dev/null)
    if [ "$size" -lt 1073741824 ]; then
        log_warning "ISO is smaller than 1GB - may be incomplete"
    else
        log_success "ISO size: $(numfmt --to=iec $size 2>/dev/null || echo $size bytes)"
    fi
    
    # Type check
    local type=$(file "$iso")
    if echo "$type" | grep -q "ISO 9660"; then
        log_success "Valid ISO 9660 image"
    else
        log_warning "May not be valid ISO image"
    fi
    
    # Checksum if available
    if [ -f "${iso}.sha256" ]; then
        log_info "Verifying checksum..."
        if sha256sum -c "${iso}.sha256"; then
            log_success "Checksum valid"
        else
            log_error "Checksum mismatch!"
            exit 1
        fi
    fi
    
    log_success "Verification complete"
}

show_info() {
    local iso="$1"
    
    print_header "ISO INFORMATION"
    
    log_info "File: $iso"
    log_info "Size: $(du -h $iso | cut -f1)"
    log_info "Type: $(file $iso)"
    log_info ""
    
    if command -v isoinfo &> /dev/null; then
        log_info "ISO Details:"
        isoinfo -i "$iso" -f 2>/dev/null | head -20 || true
    fi
}

test_iso() {
    local iso="$1"
    
    print_header "TESTING ISO WITH QEMU"
    
    if ! command -v qemu-system-x86_64 &> /dev/null; then
        log_error "QEMU not installed"
        exit 1
    fi
    
    log_info "ISO: $iso"
    log_info "Starting QEMU..."
    
    qemu-system-x86_64 \
        -cdrom "$iso" \
        -m 2G \
        -smp 2 \
        -enable-kvm 2>/dev/null || \
    qemu-system-x86_64 \
        -cdrom "$iso" \
        -m 2G \
        -smp 2
    
    log_success "Test complete"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    print_header "CHIMERA II OS - ISO TOOL"
    
    if [ $# -lt 2 ]; then
        print_usage
        exit 1
    fi
    
    OPERATION="$1"
    ISO_FILE="$2"
    
    case "$OPERATION" in
        extract)
            extract_iso "$ISO_FILE" "${3:-.}"
            ;;
        repack)
            repack_iso "${3:-.}" "$ISO_FILE"
            ;;
        modify)
            modify_iso "$ISO_FILE" "$3" "$4"
            ;;
        verify)
            verify_iso "$ISO_FILE"
            ;;
        info)
            show_info "$ISO_FILE"
            ;;
        test)
            test_iso "$ISO_FILE"
            ;;
        *)
            log_error "Unknown operation: $OPERATION"
            print_usage
            exit 1
            ;;
    esac
}

# Execute
main "$@"
