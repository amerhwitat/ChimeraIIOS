# Chimera II OS - ISO Generation Complete Guide

## 🚀 Get Started in 3 Steps

```powershell
# 1. Open PowerShell (Administrator)
cd C:\tmp\ChimeraIIOS

# 2. Run all-editions builder
.\generate-all-iso-editions-wsl2.ps1

# 3. Wait 3-5 hours...
```

## 📦 What You Get

**5 Bootable ISO Files** (~10-12 GB total):

```
ChimeraIIOS-comprehensive-1.0.0-x86_64.iso    (3.5 GB)  ← Full stack
ChimeraIIOS-microkernel-1.0.0-x86_64.iso      (1.5 GB)  ← Lightweight
ChimeraIIOS-mobile-1.0.0-x86_64.iso           (1.8 GB)  ← Mobile-optimized
ChimeraIIOS-vmware-1.0.0-x86_64.iso           (2.0 GB)  ← Virtualization
ChimeraIIOS-standard-1.0.0-x86_64.iso         (2.5 GB)  ← Default
```

Each ISO:
- ✅ Bootable (BIOS + UEFI)
- ✅ Live system (read-only boot)
- ✅ Install mode (writable)
- ✅ SHA256 checksums
- ✅ Complete toolchain included

## 📋 Editions Explained

| Edition | Use Case | Size | Features |
|---------|----------|------|----------|
| **Comprehensive** | Full development | 3.5 GB | All 13 repos, all tools, complete stack |
| **Microkernel** | Minimal systems | 1.5 GB | Core OS only, lightweight kernel |
| **Mobile** | Mobile dev | 1.8 GB | Mobile SDKs, emulators, optimization |
| **VMware** | Virtual machines | 2.0 GB | VM drivers, optimization, tools |
| **Standard** | General use | 2.5 GB | Balanced features and size |

## ⏱️ Timeline

| Phase | Time |
|-------|------|
| Comprehensive | ~60-75 min |
| Microkernel | ~40-50 min |
| Mobile | ~45-55 min |
| VMware | ~50-65 min |
| Standard | ~55-70 min |
| Reporting | ~5-10 min |
| **TOTAL** | **~3-5 hours** |

## 📚 Documentation

### Start Here
- **ALL_EDITIONS_GUIDE.md** ← Complete guide for all editions
- **ISO_GENERATION_START_HERE.md** ← Quick reference

### Single Edition
- **ISO_FROM_DOCKER_GUIDE.md** ← Build one edition
- **ISO_GENERATION_COMPLETE.md** ← Detailed overview

### Scripts
- **generate-all-iso-editions-wsl2.ps1** ← Windows wrapper (use this!)
- **generate-all-iso-editions.sh** ← WSL2 bash script

## 🎯 Quick Commands

```powershell
# Start all-editions build
cd C:\tmp\ChimeraIIOS
.\generate-all-iso-editions-wsl2.ps1

# Monitor build progress (in separate terminal)
wsl tail -f /root/build-iso-editions/build.log

# Check disk space
wsl df -h /

# Verify Docker images exist
wsl docker images | findstr chimera

# Copy ISOs to Windows Downloads
Copy-Item "\\wsl$\Ubuntu\root\build-iso-editions\iso-output\*.iso" -Destination $env:USERPROFILE\Downloads\

# Verify checksums
cd $env:USERPROFILE\Downloads\ChimeraIIOS-ISOs
certutil -hashfile ChimeraIIOS-comprehensive-1.0.0-x86_64.iso SHA256
Get-Content ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
```

## ✅ Prerequisites

- [ ] Windows 10/11 with WSL2
- [ ] Ubuntu on WSL2
- [ ] Docker installed
- [ ] 50GB+ free disk space
- [ ] 8GB+ RAM (16GB recommended)
- [ ] 3-5 hours available
- [ ] Administrator privileges

**Verify:**
```powershell
wsl --version              # WSL2
wsl docker --version      # Docker
wsl df -h /               # Disk space (need 50GB+)
wsl docker images         # Docker images
```

## 🔥 Burning to USB

### Option 1: Rufus (Windows - Easiest)
1. Download: https://rufus.ie/
2. Select USB drive
3. Click "Select" → Choose ISO
4. Click "START"
5. Done in 5-10 minutes

### Option 2: balena Etcher (All Platforms)
1. Download: https://balena.io/etcher/
2. Select ISO file
3. Select USB drive
4. Click "Flash"
5. Done in 5-10 minutes

### Option 3: dd (WSL2 Command Line)
```bash
# Identify USB
lsblk

# Burn (replace /dev/sdX)
sudo dd if=ChimeraIIOS-comprehensive-1.0.0-x86_64.iso of=/dev/sdX bs=4M status=progress
sync
```

## 🖥️ Boot from USB

1. Insert USB drive
2. Restart computer
3. Press F12/DEL/ESC during startup
4. Select USB drive
5. Wait for OS to boot

## 🧪 Test Before Burning

### QEMU (WSL2)
```bash
sudo apt install qemu-system-x86-64

qemu-system-x86_64 \
  -cdrom ChimeraIIOS-comprehensive-1.0.0-x86_64.iso \
  -m 4G \
  -cpu host \
  -enable-kvm
```

### VirtualBox
1. Create new VM
2. Set CD-ROM to ISO
3. Power on

## 📊 Output Structure

After generation:

```
Windows Downloads:
$env:USERPROFILE\Downloads\ChimeraIIOS-ISOs\
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
├── ChimeraIIOS-microkernel-1.0.0-x86_64.iso
├── ... (other editions)
├── BUILD_REPORT.txt
└── (all checksums included)

WSL2 Location:
/root/build-iso-editions/iso-output/
├── Same structure
├── Individual logs: /root/build-iso-editions/logs/
└── Build log: /root/build-iso-editions/build.log
```

## 🐛 Troubleshooting

### Build Fails
```bash
# Check disk space
wsl df -h /

# Clean Docker cache
wsl docker system prune -a

# Check individual logs
wsl ls -la /root/build-iso-editions/logs/
wsl cat /root/build-iso-editions/logs/comprehensive.log
```

### Docker Image Not Found
```bash
# Verify images exist
wsl docker images | findstr chimera

# Build missing image
cd /mnt/c/tmp/ChimeraIIOS
wsl docker build -f Dockerfile.comprehensive -t chimera2os:latest .
```

### ISO Won't Boot
1. Verify checksum
2. Re-burn with Rufus or Etcher
3. Try BIOS vs UEFI mode
4. Try different USB drive

### Can't Find Output Files
```powershell
# Try WSL path directly
\\wsl$\Ubuntu\root\build-iso-editions\iso-output\

# Or view in WSL2
wsl ls -lh /root/build-iso-editions/iso-output/
```

## 📞 Support

**Author**: Amer Abdullah Suleiman Hwitat - عامر الحويطات

- 📧 Email: amer.hwitat@proton.me
- 📍 Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 📦 Repository: https://github.com/amerhwitat/ChimeraIIOS
- 🐳 Docker Hub: https://hub.docker.com/u/amerhwitat

## 🔗 Related Files

```
Project root: C:\tmp\ChimeraIIOS\

ISO Generation:
├── generate-all-iso-editions.sh          # Main builder
├── generate-all-iso-editions-wsl2.ps1    # Windows wrapper
├── ALL_EDITIONS_GUIDE.md                 # Complete guide
├── ISO_GENERATION_START_HERE.md          # Quick start
├── ISO_FROM_DOCKER_GUIDE.md              # Single edition
└── ISO_GENERATION_COMPLETE.md            # Detailed overview

Docker Builds:
├── Dockerfile.comprehensive    # Comprehensive edition
├── Dockerfile.microkernel      # Microkernel edition
├── Dockerfile.mobile           # Mobile edition
├── Dockerfile.vmware           # VMware edition
├── Dockerfile                  # Standard edition
└── docker-compose.yml          # Orchestration

Documentation:
├── COMPREHENSIVE_BUILD_README.md
├── MASTER_BUILD_GUIDE.md
└── PROJECT_COMPLETE.md

Docker Hub:
├── docker-hub-push.ps1
├── docker-hub-push.sh
└── DOCKER_HUB_GUIDE.md
```

## 🎬 Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PREPARE (5 min)                                          │
│   - Verify WSL2, Docker, disk space                        │
│   - Check Docker images exist                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. BUILD ALL EDITIONS (3-5 hours)                          │
│   - Comprehensive: ~75 min                                 │
│   - Microkernel: ~50 min                                   │
│   - Mobile: ~55 min                                        │
│   - VMware: ~65 min                                        │
│   - Standard: ~70 min                                      │
│   - Reporting: ~10 min                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. COPY TO WINDOWS (5-10 min)                              │
│   - ISOs copied to Downloads\ChimeraIIOS-ISOs              │
│   - Checksums included                                     │
│   - Build report generated                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. BURN TO USB (5-10 min)                                  │
│   - Use Rufus or balena Etcher                             │
│   - Select ISO and USB drive                               │
│   - Click START                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. BOOT FROM USB (5 min)                                   │
│   - Insert USB drive                                       │
│   - Restart computer                                       │
│   - Press F12/DEL, select USB                              │
│   - Wait for boot                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. ENJOY! 🎉                                               │
│   - 5 different editions ready                             │
│   - Complete development environment                       │
│   - All 13 GitHub projects included                        │
└─────────────────────────────────────────────────────────────┘
```

## 🏁 Next Steps

1. **Verify Prerequisites**
   ```powershell
   wsl --version
   wsl docker --version
   wsl df -h /
   ```

2. **Start Generation**
   ```powershell
   cd C:\tmp\ChimeraIIOS
   .\generate-all-iso-editions-wsl2.ps1
   ```

3. **Wait 3-5 Hours**
   - Watch progress on console
   - ISOs will be generated
   - Checksums verified automatically

4. **Burn to USB**
   - Download Rufus
   - Select ISO and USB drive
   - Click START

5. **Boot and Enjoy! 🚀**

---

**Ready to generate all editions?**

```powershell
.\generate-all-iso-editions-wsl2.ps1
```

Then come back in 3-5 hours! ⏰

---

*created by Amer Abdullah Suleiman Hwitat - عامر الحويطات*
*Amman 11814, Jordan | amer.hwitat@proton.me*
*GitHub: https://github.com/amerhwitat/ChimeraIIOS*
