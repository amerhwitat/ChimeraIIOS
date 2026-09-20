# Chimera II OS - ISO Generation from Docker Image

## Quick Start (5 Commands)

```powershell
# 1. On Windows, open PowerShell as Administrator
cd C:\tmp\ChimeraIIOS

# 2. Run ISO generation
.\run-iso-generation-wsl2.ps1

# 3. Wait 30-45 minutes...
# (The script handles everything automatically)

# 4. When done, copy to Windows
Copy-Item '\\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\*.iso' -Destination $env:USERPROFILE\Downloads\

# 5. Burn to USB using Rufus or balena Etcher
```

## Prerequisites

### On Windows
- [ ] WSL2 installed with Ubuntu
- [ ] PowerShell 5.0+
- [ ] Administrator privileges

### In WSL2 Ubuntu
The script will auto-install if missing:
- [ ] Docker (or script installs it)
- [ ] Tools: `grub-pc-bin`, `grub-efi-amd64-bin`, `xorriso`, `squashfs-tools`
- [ ] 15GB free disk space

Verify prerequisites:
```bash
# On Windows PowerShell
wsl uname -a                    # Check WSL2
wsl docker --version           # Check Docker
wsl df -h /                     # Check disk space
```

## How It Works

### The 13-Step Process

The `generate-iso-from-docker.sh` script performs these steps:

1. **Check Prerequisites** - Verify Docker, tools, disk space, root access
2. **Verify Docker Image** - Confirm `chimera2os:latest` exists
3. **Create Directories** - Build structure for ISO generation
4. **Export Docker Image** - Extract Docker image to rootfs (~5-10 min)
5. **Create Bootloader** - GRUB2 configuration for multiboot
6. **Create GRUB Images** - BIOS/MBR + UEFI/GPT bootloaders
7. **Extract Kernel/Initrd** - Copy kernel and initrd from rootfs
8. **Create Squashfs** - Compress filesystem with xz (~10-20 min)
9. **Add Branding** - OS release info and boot messages
10. **Create ISO** - Generate bootable ISO image (~5-15 min)
11. **Generate Checksums** - SHA256 and MD5 verification
12. **Generate Report** - Build summary and verification info
13. **Cleanup** - Remove temporary files

### Timeline
- Total: **30-45 minutes**
- Fastest: ~30 min (powerful CPU, fast SSD)
- Slowest: ~45 min (average system)

### Output Files
```
~/projects/ChimeraIIOS/build-iso/output/
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso      (~3GB)
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.md5
└── build-report.txt
```

## Step-by-Step Instructions

### Option 1: Use PowerShell Wrapper (Recommended for Windows)

**1. Verify Prerequisites**
```powershell
# Check WSL2
wsl --version

# Check Docker in WSL2
wsl docker --version

# Check disk space (need 15GB+)
wsl df -h /

# Check Docker image
wsl docker images | findstr chimera
```

**2. Run the Generation Script**
```powershell
cd C:\tmp\ChimeraIIOS
.\run-iso-generation-wsl2.ps1
```

The script will:
- Copy files to WSL2
- Verify Docker image
- Run 13-step ISO generation
- Show progress with timestamps
- Display next steps when complete

**3. Monitor Progress**
The script prints detailed progress:
```
[INFO] STEP 4: EXPORTING DOCKER IMAGE TO ROOTFS
[INFO] Creating temporary container...
[SUCCESS] Container created: abc123...
[INFO] Exporting container filesystem...
[SUCCESS] Export successful (Takes 5-10 min)
...
[SUCCESS] ISO image created successfully
```

### Option 2: Manual WSL2 Command (Advanced)

**1. Open WSL2 Ubuntu Terminal**
```bash
wsl
cd ~/projects/ChimeraIIOS
```

**2. Copy script if not present**
```bash
# From Windows PowerShell first
copy-item C:\tmp\ChimeraIIOS\generate-iso-from-docker.sh /tmp/ -Force
```

**3. Make executable and run**
```bash
chmod +x /tmp/generate-iso-from-docker.sh
sudo bash /tmp/generate-iso-from-docker.sh
```

**4. Wait for completion**
- Script prints real-time progress
- Estimated: 30-45 minutes
- Console will show "BUILD COMPLETED SUCCESSFULLY"

## Accessing Output Files

### From Windows File Explorer
```
\\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\
```

### Copy ISO to Windows
```powershell
# Option 1: PowerShell
Copy-Item '\\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\*.iso' `
  -Destination $env:USERPROFILE\Downloads\

# Option 2: Command line
xcopy \\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\*.iso %USERPROFILE%\Downloads\
```

### Verify Integrity
```bash
# In WSL2
cd ~/projects/ChimeraIIOS/build-iso/output/
sha256sum -c *.sha256
md5sum -c *.md5
```

## Using the ISO

### 1. View Build Report
```bash
# In WSL2
cat ~/projects/ChimeraIIOS/build-iso/output/build-report.txt

# Shows:
# - ISO specifications
# - Included toolchain
# - Boot options
# - How to use the ISO
```

### 2. Burn to USB (Windows)

#### Using Rufus (Recommended)
1. Download: https://rufus.ie/
2. Open Rufus
3. Select Device: Your USB drive
4. Select Boot selection: Click "Select"
5. Choose: `ChimeraIIOS-comprehensive-1.0.0-x86_64.iso`
6. Click "START"
7. Wait for "READY"

#### Using balena Etcher
1. Download: https://balena.io/etcher/
2. Click "Flash from file"
3. Select: `ChimeraIIOS-comprehensive-1.0.0-x86_64.iso`
4. Click "Select target"
5. Select: Your USB drive
6. Click "Flash"
7. Wait for completion

#### Using WSL2 dd (Linux)
```bash
# In WSL2
sudo dd if=~/projects/ChimeraIIOS/build-iso/output/*.iso of=/dev/sdX bs=4M status=progress
# Replace /dev/sdX with your USB device (check with: lsblk)
```

### 3. Boot from USB
1. Insert USB drive
2. Restart computer
3. Enter BIOS/Boot menu (usually F12, DEL, or ESC during startup)
4. Select USB drive
5. Press Enter

### 4. Boot Menu Options
When ISO boots, select:
- **Live System** - Read-only, safe testing
- **Install Mode** - Live with write permissions
- **Safe Mode** - No GPU drivers (troubleshooting)
- **Diagnostics** - System tests
- **Reboot** - Restart
- **Power Off** - Shutdown

### 5. Test in Virtual Machine (Optional)

#### QEMU (Linux/WSL2)
```bash
sudo apt install qemu-system-x86-64
qemu-system-x86_64 \
  -cdrom ~/projects/ChimeraIIOS/build-iso/output/*.iso \
  -m 4G \
  -cpu host \
  -enable-kvm
```

#### VirtualBox (Windows/Mac/Linux)
1. Create new VM
2. Allocate 4GB+ RAM
3. Set CD-ROM to ISO file
4. Boot VM

#### VMware (Windows/Mac/Linux)
1. Create new VM
2. Attach ISO as CD-ROM
3. Boot VM

## Included in the ISO

### Integrated Projects (13 Repositories)
- **ChimeraIIOS** - Core operating system
- **nlp** - Natural Language Processing
- **BizX** - Business logic
- **BizXtreme** - Enterprise tools
- **CPU4096** - CPU simulator
- **CPU4096Simulator** - Web-based CPU sim
- **keygen** - Cryptographic tools
- **eth-key-check** - Ethereum utilities
- **bruteforce** - Security testing
- **PDFreaderPY** - PDF processing
- **general** - General utilities
- **test** - Testing framework
- **amerhwitat.github.io** - Portfolio

### Toolchain
- **Compilers**: GCC 13, Clang/LLVM 18
- **Languages**: Python 3.12, Node.js 18+, Rust, Java 21, .NET 8.0
- **Build Tools**: CMake, Ninja, Make, Git, Docker
- **Data Science**: TensorFlow, PyTorch, scikit-learn
- **Web**: Flask, FastAPI, SQLAlchemy, Django
- **Development**: pytest, Jupyter, gdb, Valgrind, strace

### Boot Support
- ✅ BIOS/MBR (Legacy) - Older computers
- ✅ UEFI/GPT (Modern) - Newer computers
- ✅ Both on same ISO

## Troubleshooting

### "WSL2 not found"
```powershell
# Install WSL2
wsl --install

# Restart computer
# Re-run: .\run-iso-generation-wsl2.ps1
```

### "Docker image not found"
```bash
# In WSL2, build or pull the image
docker pull amerhwitat/chimera2os:latest
# or
docker build -t chimera2os:latest .
```

### "Permission denied"
```bash
# Must run with sudo
sudo bash generate-iso-from-docker.sh
```

### "Disk space insufficient"
```bash
# Check available space (need 15GB+)
df -h /

# Clean up Docker images if needed
docker system prune -a
```

### "Build times out"
```bash
# Normal - can take 30-45 minutes
# Just wait - script doesn't timeout
# For status, watch the console output
```

### "ISO won't boot"
```bash
# 1. Verify checksum
sha256sum -c *.sha256

# 2. Re-burn to USB using Rufus or Etcher

# 3. Try BIOS vs UEFI mode
# (ISO has both)

# 4. Rebuild if corrupted
sudo bash generate-iso-from-docker.sh
```

## Advanced Options

### Custom Docker Image
```powershell
.\run-iso-generation-wsl2.ps1 -DockerImage myimage:tag
```

### Custom WSL Distro
```powershell
.\run-iso-generation-wsl2.ps1 -WSLDistro "Ubuntu-22.04"
```

### Manual Build Parameters
```bash
# In WSL2
sudo bash generate-iso-from-docker.sh [image] [build-dir]
# Example:
sudo bash generate-iso-from-docker.sh chimera2os:latest /tmp/my-build
```

## Performance Tips

### Faster Build
- Use SSD for WSL2 (not HDD)
- Allocate 4+ CPU cores to WSL2
- Close other applications
- Use WSL2 Gen 2 (newer systems)

### Check WSL2 Resources
```powershell
# In Windows PowerShell
wsl --status
wsl -l -v
```

### Increase WSL2 Limits
Edit `%USERPROFILE%\.wslconfig`:
```ini
[wsl2]
memory=8GB
processors=4
```

## Security Notes

### Checksums
- SHA256 provided: `*.sha256`
- MD5 provided: `*.md5` (legacy, use SHA256)

Verify before using:
```bash
sha256sum -c ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
```

### Source Code
- All 13 projects are open source
- GitHub: https://github.com/amerhwitat/ChimeraIIOS
- License: See LICENSE file in repository

## Support & Contact

**Author**: Amer Abdullah Suleiman Hwitat - عامر الحويطات

- 📧 Email: amer.hwitat@proton.me
- 📍 Location: Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 📦 Repository: https://github.com/amerhwitat/ChimeraIIOS
- 🐳 Docker Hub: https://hub.docker.com/u/amerhwitat

For issues: amer.hwitat@proton.me or GitHub Issues

## Quick Reference

| Task | Command |
|------|---------|
| Check WSL2 | `wsl --version` |
| Check Docker | `wsl docker --version` |
| Check space | `wsl df -h /` |
| Start generation | `.\run-iso-generation-wsl2.ps1` |
| View progress | Watch console (auto-updating) |
| Copy to Windows | `Copy-Item '\\wsl$\...' -Destination Downloads` |
| Verify ISO | `wsl sha256sum -c *.sha256` |
| View report | `wsl cat build-report.txt` |
| Burn to USB | Use Rufus or balena Etcher |
| Test in QEMU | `qemu-system-x86_64 -cdrom *.iso -m 4G` |

---

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحويطات

Amman 11814, Jordan | amer.hwitat@proton.me

Ready to generate your bootable ISO! Follow the "Quick Start" section above. 🚀
