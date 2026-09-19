# ISO GENERATION QUICK START - CHIMERA II OS
## Generate Bootable ISO from chimera2os Docker Image

**For**: WSL2 Ubuntu or Linux  
**Author**: Amer Abdullah Suleiman Hwitat - عامر الحويطات  
**Contact**: amer.hwitat@proton.me

---

## ⚡ QUICK START (30 SECONDS)

```bash
# In WSL2 Ubuntu:
cd ~/projects/ChimeraIIOS

# Make script executable
chmod +x generate-iso-from-docker.sh

# Generate ISO (requires sudo)
sudo bash generate-iso-from-docker.sh

# Wait 30-45 minutes...
# Result: ChimeraIIOS-comprehensive-1.0.0-x86_64.iso (~3GB)
```

---

## 📋 PREREQUISITES

### Docker Image Must Exist

First, build the Docker image if you haven't already:

```bash
cd ~/projects/ChimeraIIOS
docker build -f Dockerfile.fixed -t chimera2os:latest .
```

### Verify Docker Image

```bash
docker images | grep chimera2os
# Should show: chimera2os    latest    ...    2.15GB
```

### WSL2 Ubuntu Must Have Tools

```bash
# Install required tools (if not already installed)
sudo apt update
sudo apt install -y \
    grub-pc-bin \
    grub-efi-amd64-bin \
    xorriso \
    squashfs-tools \
    ca-certificates
```

---

## 🚀 GENERATE ISO

### Option 1: Default (Recommended)

```bash
sudo bash generate-iso-from-docker.sh
```

This uses `chimera2os:latest` image by default.

### Option 2: Custom Image

```bash
sudo bash generate-iso-from-docker.sh chimera2os:v1.0.0 ./custom-build-dir
```

Parameters:
- Image name: `chimera2os:v1.0.0`
- Build directory: `./custom-build-dir`

### Option 3: Monitor Progress

In another terminal:

```bash
# Watch build progress
watch -n 2 'ls -lh ~/projects/ChimeraIIOS/build-iso/output/'

# Or check file sizes
du -sh ~/projects/ChimeraIIOS/build-iso/*
```

---

## 📊 BUILD TIMELINE

| Phase | Time | Description |
|-------|------|-------------|
| Prerequisites check | 1 min | Verify Docker, tools, disk space |
| Docker export | 5-10 min | Export image to rootfs |
| Bootloader creation | 2 min | Create GRUB/UEFI |
| Squashfs compression | 10-20 min | **Longest step** |
| ISO creation | 5-10 min | Generate final ISO |
| Verification | 2 min | Checksums & cleanup |
| **TOTAL** | **30-45 min** | **Complete ISO ready** |

---

## ✅ VERIFY SUCCESS

### Check Output File

```bash
# See generated ISO
ls -lh ~/projects/ChimeraIIOS/build-iso/output/

# Should show:
# ChimeraIIOS-comprehensive-1.0.0-x86_64.iso (2.5-3.5 GB)
# ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
# ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.md5
# build-report.txt
```

### Verify Checksums

```bash
cd ~/projects/ChimeraIIOS/build-iso/output
sha256sum -c ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256

# Should show: OK
```

### Check File Type

```bash
file ChimeraIIOS-comprehensive-1.0.0-x86_64.iso

# Should show:
# ... ISO 9660 bootable CD image ...
```

---

## 📝 BUILD REPORT

After ISO generation, check:

```bash
cat ~/projects/ChimeraIIOS/build-iso/output/build-report.txt
```

Shows:
- Build date & time
- Docker image details
- ISO file information
- Included toolchain
- Boot options
- Usage instructions

---

## 📂 OUTPUT STRUCTURE

```
~/projects/ChimeraIIOS/build-iso/
├── output/
│   ├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso      (~3GB)
│   ├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
│   ├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.md5
│   └── build-report.txt
├── iso/
│   ├── live/
│   │   ├── vmlinuz
│   │   ├── initrd.img
│   │   └── filesystem.squashfs
│   ├── boot/grub/
│   │   └── grub.cfg
│   └── EFI/BOOT/
│       └── BOOTX64.EFI
└── rootfs/ (temporary)
```

---

## 🚀 USE THE ISO

### Copy to Windows Downloads

```bash
# From WSL2, copy ISO to Windows
cp ~/projects/ChimeraIIOS/build-iso/output/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso \
   /mnt/c/Users/$USER/Downloads/
```

### On Windows, Burn to USB

1. Download **Rufus** or **balena Etcher**
2. Select ISO: `ChimeraIIOS-comprehensive-1.0.0-x86_64.iso`
3. Select USB drive
4. Click "Write" or "Flash"
5. Wait for completion

### Test with QEMU (Linux/WSL2)

```bash
qemu-system-x86_64 \
    -cdrom ~/projects/ChimeraIIOS/build-iso/output/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso \
    -m 4G \
    -smp 4 \
    -enable-kvm
```

### Boot from USB

1. Insert USB into computer
2. Restart
3. Enter BIOS/Boot menu (Del, F12, F2, or Esc)
4. Select USB as boot device
5. Boot Chimera II OS

---

## 🐛 TROUBLESHOOTING

### "Docker image not found"

```bash
# Build the image first
cd ~/projects/ChimeraIIOS
docker build -f Dockerfile.fixed -t chimera2os:latest .
```

### "Permission denied"

```bash
# Use sudo
sudo bash generate-iso-from-docker.sh
```

### "grub-mkimage not found"

```bash
sudo apt install grub-pc-bin
```

### "Out of space"

```bash
# Clean Docker
docker system prune -a

# Check space
df -h

# Need at least 10GB free
```

### "xorriso not found"

```bash
sudo apt install xorriso
```

### "Build times out"

Script has no timeout. If stuck:
1. Check disk space: `df -h`
2. Check memory: `free -h`
3. Check processes: `ps aux | grep docker`
4. If needed, increase WSL2 memory in `.wslconfig`

### "ISO file corrupted"

```bash
# Verify with checksums
sha256sum -c ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256

# If fails, rebuild:
sudo bash generate-iso-from-docker.sh
```

---

## ⏱️ DISK SPACE REQUIREMENTS

| Phase | Space | Notes |
|-------|-------|-------|
| Docker image | 2.15 GB | Already exists |
| Rootfs (temporary) | 2.5-3.5 GB | Deleted after build |
| ISO intermediate files | 3-5 GB | Temporary |
| Final ISO | 2.5-3.5 GB | Kept |
| **Total needed** | **~15 GB** | Free disk space |

---

## 🎯 BOOT MENU OPTIONS

When ISO boots, select from menu:

```
1. Live System - Boot read-only OS
2. Install Mode - Writable live environment
3. Safe Mode - No GPU drivers
4. Diagnostics - System tests
5. Reboot - Restart computer
6. Power Off - Shutdown
```

---

## 📋 SCRIPT OPTIONS

### View Script Help

```bash
# Show script usage
head -50 generate-iso-from-docker.sh
```

### Custom Configurations

Edit script variables:

```bash
# In generate-iso-from-docker.sh, change:
DOCKER_IMAGE="chimera2os:latest"           # Image to use
ISO_NAME="ChimeraIIOS-comprehensive"       # ISO name prefix
ISO_VERSION="1.0.0"                        # Version number
BUILD_DIR="./build-iso"                    # Build directory
```

---

## ✨ ADVANCED OPTIONS

### Parallel Compression

```bash
# Edit script, modify mksquashfs line:
# Change: -processors "$(nproc)"
# To: -processors 8  (for 8 cores)
```

### Different Compression

```bash
# Edit script, modify mksquashfs line:
# Change: -comp xz
# To: -comp gzip (faster, larger) or -comp lzma (better compression)
```

### Keep Intermediate Files

```bash
# Comment out cleanup section in script
# around line "rm -rf $ROOTFS_DIR"
```

---

## 📊 EXPECTED OUTPUT

### Successful Build Messages

```
[INFO] Checking Docker daemon...
[SUCCESS] Docker daemon is running
[INFO] Checking Docker image: chimera2os:latest
[SUCCESS] Image found: chimera2os:latest
[INFO] Image size: 2.1G (~2GB)

... (various build steps)

[INFO] Creating squashfs from rootfs...
[SUCCESS] Squashfs created successfully
[INFO] Squashfs size: 542M

[INFO] Creating bootable ISO image...
[SUCCESS] ISO image created: ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
[INFO] ISO size: 563M

====================================================
BUILD COMPLETED SUCCESSFULLY
====================================================

[SUCCESS] ISO file created: ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
Location: /root/projects/ChimeraIIOS/build-iso/output/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
```

---

## 🔍 VERIFY OUTPUTS

```bash
# Navigate to output
cd ~/projects/ChimeraIIOS/build-iso/output

# List files
ls -lh

# Verify ISO
file *.iso

# Check checksums
sha256sum -c *.sha256
md5sum -c *.md5

# View report
less build-report.txt
```

---

## 📞 SUPPORT

| Issue | Solution |
|-------|----------|
| ISO won't boot | Verify checksums, re-burn to USB |
| Can't find ISO | Check: `ls ~/projects/ChimeraIIOS/build-iso/output/` |
| Build too slow | Check disk I/O, increase memory |
| Permission issues | Use `sudo bash generate-iso-from-docker.sh` |

---

## 🎉 NEXT STEPS

1. ✅ Generate ISO
2. ✅ Verify checksums
3. ✅ Copy to Windows
4. ✅ Burn to USB
5. ✅ Boot from USB
6. ✅ Install Chimera II OS
7. ✅ Deploy and use

---

## 👤 AUTHOR

**Amer Abdullah Suleiman Hwitat - عامر الحويطات**

- 📧 Email: amer.hwitat@proton.me
- 📍 Location: Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 📚 Repository: https://github.com/amerhwitat/ChimeraIIOS

---

**"created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"**  
**Amman 11814, Jordan | amer.hwitat@proton.me**

---

## 🚀 START GENERATING YOUR ISO NOW!

```bash
cd ~/projects/ChimeraIIOS
chmod +x generate-iso-from-docker.sh
sudo bash generate-iso-from-docker.sh

# In 30-45 minutes, your bootable ISO will be ready! 🎉
```
