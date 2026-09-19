# CHIMERA II OS - BOOTABLE ISO BUILD GUIDE
## Complete Guide to Building and Deploying Bootable ISO Image

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحويطات  
**Location**: Amman 11814, Jordan  
**Contact**: amer.hwitat@proton.me

---

## Overview

This guide provides complete instructions for building a bootable ISO image of ChimeraIIOS from the comprehensive Docker image. The ISO supports both:

- **BIOS/MBR** (Legacy BIOS boot)
- **UEFI/GPT** (Modern UEFI boot)

---

## Prerequisites

### System Requirements
- Ubuntu 20.04+ (or similar Linux distribution)
- Minimum 100GB free disk space
- 16GB+ RAM
- Internet connection
- Root/sudo access

### Required Packages

The build scripts will automatically install dependencies, but you can pre-install them:

```bash
sudo apt-get update
sudo apt-get install -y \
    docker.io \
    xorriso \
    grub-pc-bin \
    grub-efi-amd64-bin \
    squashfs-tools \
    curl \
    wget \
    ca-certificates
```

---

## Method 1: Native Build (Recommended)

### Step 1: Install Docker

```bash
# Install Docker setup script requirements
sudo apt update
sudo apt install ca-certificates curl

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
```

### Step 2: Prepare Build Environment

```bash
# Clone or navigate to ChimeraIIOS repository
cd /path/to/ChimeraIIOS

# Verify required files exist
ls -la Dockerfile.comprehensive build-chimera-iso.sh docker-compose.yml

# Make build script executable
sudo chmod +x build-chimera-iso.sh
```

### Step 3: Build Docker Image

```bash
# Option A: Build Docker image and ISO
sudo bash build-chimera-iso.sh

# Option B: Build Docker image only
sudo bash build-chimera-iso.sh --docker-only

# Option C: Build from existing Docker image (skip Docker build)
sudo bash build-chimera-iso.sh --iso-only

# Option D: With custom Docker tag
sudo bash build-chimera-iso.sh --tag custom-v1.0

# Option E: Push to registry after build
sudo bash build-chimera-iso.sh --push --registry docker.io/username
```

### Step 4: Wait for Build Completion

The build process will:
1. Build the Docker image (30-45 minutes)
2. Export Docker image to rootfs (5-10 minutes)
3. Create squashfs filesystem (10-15 minutes)
4. Create bootloaders (2-3 minutes)
5. Generate ISO image (5-10 minutes)
6. Verify and generate checksums (1-2 minutes)

**Total estimated time: 1-2 hours**

### Step 5: Verify ISO Build

```bash
# Check ISO file
ls -lh ChimeraIIOS-comprehensive-1.0.0-x86_64.iso*

# Verify SHA256
sha256sum -c ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256

# Check file integrity
file ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
```

---

## Method 2: Docker-Based Build (Containerized)

This method builds the ISO entirely inside a container, avoiding host dependencies.

### Step 1: Build ISO Builder Image

```bash
docker build \
    -f Dockerfile.iso-builder \
    -t chimera-iso-builder:latest \
    .
```

### Step 2: Build Docker Image

```bash
docker build \
    -f Dockerfile.comprehensive \
    -t chimera2os-comprehensive:latest \
    .
```

### Step 3: Run ISO Builder

```bash
docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $(pwd)/output:/output \
    chimera-iso-builder:latest \
    chimera2os-comprehensive latest ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
```

### Step 4: Extract ISO

```bash
# ISO will be in ./output/ directory
ls -lh output/*.iso
cp output/*.iso .
```

---

## Using the ISO Image

### Method 1: Burn to USB

```bash
# Identify USB device
lsblk

# Burn ISO (replace sdX with your USB device)
sudo dd if=ChimeraIIOS-comprehensive-1.0.0-x86_64.iso of=/dev/sdX bs=4M status=progress
sudo sync

# Eject USB
sudo eject /dev/sdX
```

### Method 2: Burn to DVD

```bash
# Using cdrecord
cdrecord -v -sao ChimeraIIOS-comprehensive-1.0.0-x86_64.iso

# Or with wodim
wodim -v ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
```

### Method 3: QEMU Emulation (Testing)

```bash
# Boot ISO in QEMU
qemu-system-x86_64 \
    -cdrom ChimeraIIOS-comprehensive-1.0.0-x86_64.iso \
    -m 4G \
    -smp 4 \
    -enable-kvm

# Or with EFI BIOS
qemu-system-x86_64 \
    -cdrom ChimeraIIOS-comprehensive-1.0.0-x86_64.iso \
    -bios /usr/share/ovmf/OVMF.fd \
    -m 4G
```

### Method 4: VirtualBox

1. Open VirtualBox
2. Create new VM
3. Configure storage to attach ISO: `ChimeraIIOS-comprehensive-1.0.0-x86_64.iso`
4. Set boot order to CD/DVD
5. Start VM

### Method 5: VMware

1. Create new VM
2. Configure CD/DVD to use ISO: `ChimeraIIOS-comprehensive-1.0.0-x86_64.iso`
3. Set boot order to CD
4. Power on VM

---

## Boot Menu Options

Once the ISO boots, you'll see the GRUB menu with these options:

| Option | Description | Use Case |
|--------|-------------|----------|
| **Live System** | Read-only environment | Testing/Live demo |
| **Install Mode** | Writable live environment | Installation |
| **Safe Mode** | Disabled GPU drivers | Troubleshooting |
| **Diagnostics** | System diagnostic tools | Hardware testing |
| **Reboot** | Restart the computer | - |
| **Power Off** | Shutdown | - |

---

## ISO Contents

```
ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
├── boot/
│   └── grub/
│       ├── grub.cfg          # GRUB2 configuration
│       ├── i386-pc/          # BIOS bootloader
│       └── fonts/
├── EFI/
│   └── BOOT/
│       └── BOOTX64.EFI       # UEFI bootloader
└── live/
    └── filesystem.squashfs   # Root filesystem (compressed)
```

---

## Build Output Files

After successful build:

```bash
ChimeraIIOS-comprehensive-1.0.0-x86_64.iso          # Main ISO file
ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256   # SHA256 checksum
ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.md5      # MD5 checksum
build-report.txt                                     # Build details
```

---

## Customization

### Modify Boot Menu

Edit `boot/grub/grub.cfg` in the build directory before creating the ISO:

```bash
# After building docker image, before creating ISO
nano build/iso/boot/grub/grub.cfg
```

### Change Boot Timeout

```bash
sed -i 's/set timeout=10/set timeout=30/' build/iso/boot/grub/grub.cfg
```

### Add Custom Boot Parameters

Edit kernel command line in `grub.cfg`:

```
linux /live/vmlinuz boot=live quiet splash nomodeset
```

Available parameters:
- `quiet` - Suppress boot messages
- `splash` - Show splash screen
- `nomodeset` - Disable GPU drivers
- `memtest86` - Run memory test
- `single` - Single user mode

---

## Troubleshooting

### Build Fails: "Dockerfile.comprehensive not found"

```bash
# Ensure you're in the ChimeraIIOS directory
pwd
# Should output: /path/to/ChimeraIIOS

# Verify file exists
ls -la Dockerfile.comprehensive
```

### Build Fails: "docker: command not found"

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Or use apt
sudo apt-get install docker.io
```

### Build Fails: "Out of space"

```bash
# Check available space
df -h

# Clean Docker cache
docker system prune -a

# Create more space if needed
# Remove large files or expand disk
```

### ISO won't boot

- Verify ISO integrity: `sha256sum -c *.sha256`
- Re-burn to USB with `--sync` flag
- Try different USB port
- Check BIOS boot order
- Disable Secure Boot in BIOS

### QEMU boot fails

```bash
# Check if KVM is available
kvm-ok

# Run without KVM
qemu-system-x86_64 -cdrom ChimeraIIOS-comprehensive-1.0.0-x86_64.iso -m 4G
```

---

## Advanced Options

### Build with Custom Docker Registry

```bash
sudo bash build-chimera-iso.sh \
    --push \
    --registry registry.example.com \
    --tag v1.0-prod
```

### Build ISO Only (Docker image exists)

```bash
sudo bash build-chimera-iso.sh --iso-only
```

### Build Docker Only (no ISO)

```bash
sudo bash build-chimera-iso.sh --docker-only
```

---

## Verification & Testing

### Verify ISO Structure

```bash
# Mount ISO temporarily
mkdir -p /tmp/chimera-iso
sudo mount -o loop ChimeraIIOS-comprehensive-1.0.0-x86_64.iso /tmp/chimera-iso

# List contents
ls -la /tmp/chimera-iso/

# Unmount
sudo umount /tmp/chimera-iso
```

### Test Boot with QEMU

```bash
# 30-second boot test
timeout 30 qemu-system-x86_64 \
    -cdrom ChimeraIIOS-comprehensive-1.0.0-x86_64.iso \
    -m 2G \
    -serial stdio || echo "Boot test completed"
```

### Verify Bootloaders

```bash
# List ISO contents
xorriso -indev ChimeraIIOS-comprehensive-1.0.0-x86_64.iso -ls -R

# Check for bootloader files
xorriso -indev ChimeraIIOS-comprehensive-1.0.0-x86_64.iso -find /boot -type f -exec ls
```

---

## Build Report

After a successful build, review `build-report.txt` for:
- Exact build date and time
- Docker image size
- ISO file size
- SHA256 and MD5 checksums
- Boot parameters
- Included repositories
- System information

---

## Distribution & Release

### Create Release Package

```bash
# Create compressed archive
tar -czf ChimeraIIOS-comprehensive-1.0.0.tar.gz \
    ChimeraIIOS-comprehensive-1.0.0-x86_64.iso* \
    build-report.txt

# Or use zip
zip -r ChimeraIIOS-comprehensive-1.0.0.zip \
    ChimeraIIOS-comprehensive-1.0.0-x86_64.iso* \
    build-report.txt
```

### Upload to GitHub Releases

```bash
gh release create v1.0.0 \
    ChimeraIIOS-comprehensive-1.0.0-x86_64.iso \
    ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256 \
    build-report.txt
```

### Create Mirrors

```bash
# AWS S3
aws s3 cp ChimeraIIOS-comprehensive-1.0.0-x86_64.iso s3://chimera-iios-releases/

# Generic HTTP server
python3 -m http.server 8000
```

---

## Support & Documentation

| Resource | Location |
|----------|----------|
| GitHub Repo | https://github.com/amerhwitat/ChimeraIIOS |
| Issues | https://github.com/amerhwitat/ChimeraIIOS/issues |
| Wiki | https://github.com/amerhwitat/ChimeraIIOS/wiki |
| Email Support | amer.hwitat@proton.me |

---

## Author & Contact

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحويطات  
**Location**: Amman 11814, Jordan  
**Email**: amer.hwitat@proton.me  
**GitHub**: https://github.com/amerhwitat

For issues, questions, or contributions, contact the author directly or submit issues to the GitHub repository.

---

**"created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"**  
**Amman 11814, Jordan | amer.hwitat@proton.me**
