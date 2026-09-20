# Chimera II OS - Generate All Editions ISO Files

## Quick Start

```powershell
# 1. Open PowerShell as Administrator
cd C:\tmp\ChimeraIIOS

# 2. Start generation
.\generate-all-iso-editions-wsl2.ps1

# 3. Wait 3-5 hours for all editions to complete
```

## What Gets Built

5 Complete ISO files, one for each edition:

| Edition | Size | Purpose | Best For |
|---------|------|---------|----------|
| **Comprehensive** | ~3.5 GB | Full stack, all 13 projects | Complete development |
| **Microkernel** | ~1.5 GB | Lightweight OS | Resource-constrained systems |
| **Mobile** | ~1.8 GB | Mobile-optimized | Mobile development |
| **VMware** | ~2.0 GB | Virtualization optimized | VM deployment |
| **Standard** | ~2.5 GB | Default edition | General use |

**Total disk usage: ~10-12 GB per architecture**

## Prerequisites

### System Requirements
- **RAM**: 8GB+ (16GB recommended)
- **Disk Space**: 50GB+ free (for building all editions)
- **CPU**: 4+ cores (for parallel compression)
- **Network**: 5 Mbps+ for pulling Docker images
- **Time**: 3-5 hours

### Software Requirements
- Windows 10/11 with WSL2 enabled
- Ubuntu 20.04+ on WSL2
- Docker installed on WSL2
- PowerShell 5.0+

### Verify Prerequisites

```powershell
# Check WSL2
wsl --version

# Check Docker
wsl docker --version

# Check disk space (need 50GB+)
wsl df -h /

# Check available Docker images
wsl docker images | findstr chimera
```

## How It Works

### The Build Process

```
For each edition:
  1. Export Docker image to rootfs (~5-10 min)
  2. Create bootloader (BIOS + UEFI)
  3. Extract kernel/initrd
  4. Create squashfs filesystem (~10-20 min per edition)
  5. Generate ISO image (~5-10 min)
  6. Generate checksums (SHA256, MD5)
  7. Cleanup temporary files

Total: ~60 min per edition × 5 editions = ~3-5 hours
```

### Build Timeline

```
Comprehensive:  ~60-75 min
Microkernel:    ~40-50 min
Mobile:         ~45-55 min
VMware:         ~50-65 min
Standard:       ~55-70 min
Reporting:      ~5-10 min
─────────────────────────
Total:          ~3-5 hours
```

## Running the Generator

### Option 1: Windows PowerShell (Recommended)

**Step 1: Verify Prerequisites**
```powershell
cd C:\tmp\ChimeraIIOS

# Check everything is ready
wsl uname -a                    # WSL2 version
wsl docker --version           # Docker
wsl df -h /                     # Disk space
wsl docker images | findstr chimera  # Docker images
```

**Step 2: Start Generation**
```powershell
.\generate-all-iso-editions-wsl2.ps1
```

The script will:
- Verify all prerequisites
- List available Docker images
- Confirm before starting
- Build all 5 editions (with real-time progress)
- Copy ISOs to Windows
- Generate build report

**Step 3: Monitor Progress**
- Watch the console output (auto-updating)
- Check individual logs in WSL2: `wsl ls -la /root/build-iso-editions/logs/`
- Each edition shows progress timestamps

### Option 2: WSL2 Terminal (Advanced)

**From WSL2 Ubuntu:**
```bash
# Copy script
cp /mnt/c/tmp/ChimeraIIOS/generate-all-iso-editions.sh ~/

# Make executable
chmod +x generate-all-iso-editions.sh

# Run
sudo bash generate-all-iso-editions.sh
```

**Optionally customize build directory:**
```bash
sudo bash generate-all-iso-editions.sh /custom/build/path
```

## Output Structure

After generation completes:

```
Windows (PowerShell default):
$env:USERPROFILE\Downloads\ChimeraIIOS-ISOs\
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
├── ChimeraIIOS-microkernel-1.0.0-x86_64.iso
├── ChimeraIIOS-microkernel-1.0.0-x86_64.iso.sha256
├── ChimeraIIOS-mobile-1.0.0-x86_64.iso
├── ChimeraIIOS-mobile-1.0.0-x86_64.iso.sha256
├── ChimeraIIOS-vmware-1.0.0-x86_64.iso
├── ChimeraIIOS-vmware-1.0.0-x86_64.iso.sha256
├── ChimeraIIOS-standard-1.0.0-x86_64.iso
├── ChimeraIIOS-standard-1.0.0-x86_64.iso.sha256
└── BUILD_REPORT.txt

WSL2 location:
/root/build-iso-editions/iso-output/
├── Same structure as above
└── Also: *.md5 files
```

## Accessing Output Files

### From Windows
```powershell
# Default location
cd $env:USERPROFILE\Downloads\ChimeraIIOS-ISOs

# Or via WSL2 path
\\wsl$\Ubuntu\root\build-iso-editions\iso-output\
```

### From WSL2
```bash
ls -lh ~/build-iso-editions/iso-output/
cd ~/build-iso-editions/iso-output
```

### View Build Report
```bash
# In WSL2
cat ~/build-iso-editions/iso-output/BUILD_REPORT.txt

# Or in Windows
notepad $env:USERPROFILE\Downloads\ChimeraIIOS-ISOs\BUILD_REPORT.txt
```

## Verifying ISO Integrity

### Windows (PowerShell)
```powershell
cd $env:USERPROFILE\Downloads\ChimeraIIOS-ISOs

# Verify all ISOs
Get-ChildItem *.sha256 | ForEach-Object {
    $iso = $_.Name -replace '\.sha256$', ''
    Write-Host "Verifying $iso..."
    certutil -hashfile $iso SHA256 | Select-Object -First 1
    Get-Content $_ | Select-Object -First 1
}
```

### WSL2 (Bash)
```bash
cd ~/build-iso-editions/iso-output
sha256sum -c *.sha256
md5sum -c *.md5
```

## Using the ISOs

### 1. Burn to USB

#### Using Rufus (Windows)
1. Download: https://rufus.ie/
2. Open Rufus
3. Select device: Your USB drive
4. Select boot: Click "Select", choose ISO
5. Click "START"
6. Wait for completion

#### Using balena Etcher (All Platforms)
1. Download: https://balena.io/etcher/
2. Select ISO file
3. Select USB drive
4. Click "Flash"

#### Using dd (WSL2)
```bash
# List drives
lsblk

# Burn (replace /dev/sdX with your device)
sudo dd if=~/build-iso-editions/iso-output/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso of=/dev/sdX bs=4M status=progress
sync
```

### 2. Boot from USB

1. Insert USB drive
2. Restart computer
3. During startup, press F12/DEL/ESC (varies by computer)
4. Select USB drive from boot menu
5. Press Enter
6. Wait for OS to load

### 3. Test in Virtual Machine

#### QEMU (WSL2)
```bash
# Install QEMU
sudo apt install qemu-system-x86-64

# Run
qemu-system-x86_64 \
  -cdrom ~/build-iso-editions/iso-output/ChimeraIIOS-comprehensive-1.0.0-x86_64.iso \
  -m 4G \
  -cpu host \
  -enable-kvm
```

#### VirtualBox (Windows/Mac/Linux)
1. Create new VM
2. Allocate 4GB+ RAM
3. Set CD-ROM to ISO file
4. Start VM

#### VMware (Windows/Mac/Linux)
1. Create new VM
2. Attach ISO as CD-ROM
3. Power on

## Troubleshooting

### "Insufficient disk space"
```bash
# Check available space
wsl df -h /
# Need 50GB+

# Clean Docker if needed
wsl docker system prune -a

# Remove previous builds
wsl rm -rf ~/build-iso-editions
```

### "Docker image not found"
```bash
# Verify images exist
wsl docker images | findstr chimera

# If missing, build them first:
cd /mnt/c/tmp/ChimeraIIOS
wsl docker build -f Dockerfile.comprehensive -t chimera2os:latest .
```

### "Permission denied"
The script requires sudo. If issues:
```bash
wsl sudo bash /tmp/generate-all-iso-editions.sh
```

### "Build times out"
- Normal! Squashfs compression takes 10-20 min per edition
- Script doesn't timeout
- Just wait, watch the console
- Each edition shows progress timestamps

### "ISO won't boot"
1. Verify checksum: `sha256sum -c *.sha256`
2. Re-burn to USB (use Rufus)
3. Try different USB drive
4. Try BIOS vs UEFI boot mode (ISO has both)

### "Can't access output files"
```powershell
# Try alternate WSL path
\\wsl$\Ubuntu\home\<username>\build-iso-editions\iso-output\

# Or check WSL2 logs
wsl cat /root/build-iso-editions/build.log
```

## Performance Optimization

### Speed Up Build

```bash
# On WSL2, use more CPUs
# Edit .wslconfig:
notepad %USERPROFILE%\.wslconfig

# Set:
[wsl2]
processors=8
memory=16GB
```

### Monitor Build Progress

```bash
# In separate WSL2 terminal
watch -n 5 'du -sh ~/build-iso-editions/* 2>/dev/null'

# Or view specific edition
tail -f ~/build-iso-editions/logs/comprehensive.log
```

## Advanced Usage

### Custom Build Location
```powershell
# Modify script before running
# Or pass parameter (if supported)
.\generate-all-iso-editions-wsl2.ps1 -OutputPath "E:\ISOs"
```

### Build Single Edition
```bash
# In WSL2, edit script to comment out other editions
# Or create custom script for single edition
```

### Parallel Builds (Not Recommended)
```bash
# Requires 100GB+ disk space
# Not recommended - I/O intensive
# Sequential build (default) is safer
```

## Support & Documentation

### Files in Project
- **generate-all-iso-editions.sh** - Main build script (runs on WSL2)
- **generate-all-iso-editions-wsl2.ps1** - PowerShell wrapper (Windows)
- **ALL_EDITIONS_GUIDE.md** - This guide
- **ISO_GENERATION_START_HERE.md** - Quick start
- **ISO_FROM_DOCKER_GUIDE.md** - Single edition guide

### Contact

**Author**: Amer Abdullah Suleiman Hwitat - عامر الحويطات

- 📧 Email: amer.hwitat@proton.me
- 📍 Location: Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 📦 Repository: https://github.com/amerhwitat/ChimeraIIOS
- 🐳 Docker Hub: https://hub.docker.com/u/amerhwitat

## Quick Commands Reference

| Task | Command |
|------|---------|
| Check WSL2 | `wsl --version` |
| Check Docker | `wsl docker --version` |
| Check space | `wsl df -h /` |
| List images | `wsl docker images` |
| Start build | `.\generate-all-iso-editions-wsl2.ps1` |
| View build log | `wsl cat /root/build-iso-editions/build.log` |
| List ISOs | `dir $env:USERPROFILE\Downloads\ChimeraIIOS-ISOs` |
| Verify checksums | `sha256sum -c *.sha256` (in WSL2) |
| Copy to Downloads | `Copy-Item '\\wsl$\Ubuntu\root\build-iso-editions\iso-output\*.iso' -Destination $env:USERPROFILE\Downloads\` |
| Burn to USB | Use Rufus: https://rufus.ie/ |

---

**Ready to generate all editions?**

```powershell
cd C:\tmp\ChimeraIIOS
.\generate-all-iso-editions-wsl2.ps1
```

Then come back in 3-5 hours! ⏰

---

*created by Amer Abdullah Suleiman Hwitat - عامر الحويطات*
*Amman 11814, Jordan | amer.hwitat@proton.me*
