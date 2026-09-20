# ISO Generation from Docker Image - Complete Guide

## 🎯 What You Need to Do (3 Simple Steps)

### Step 1: Open PowerShell (Windows)
```powershell
# Right-click PowerShell → Run as Administrator
cd C:\tmp\ChimeraIIOS
```

### Step 2: Start ISO Generation
```powershell
.\run-iso-generation-wsl2.ps1
```

### Step 3: Wait 30-45 Minutes
- The script handles everything automatically
- Watch the console for real-time progress
- When done, it shows where your ISO is located

---

## ⚡ Quick Commands Reference

```powershell
# Verify WSL2 is installed
wsl --version

# Verify Docker works
wsl docker --version

# Check disk space (need 15GB+)
wsl df -h /

# Check available Docker image
wsl docker images | findstr chimera

# Start ISO generation
cd C:\tmp\ChimeraIIOS
.\run-iso-generation-wsl2.ps1

# Monitor on WSL2 terminal
wsl tail -f ~/projects/ChimeraIIOS/build-iso/output/build-report.txt

# Verify ISO checksum
wsl sha256sum -c ~/projects/ChimeraIIOS/build-iso/output/*.sha256

# Copy ISO to Windows Downloads
Copy-Item '\\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\*.iso' -Destination $env:USERPROFILE\Downloads\
```

---

## 📊 What the Script Does

| Step | What | Time |
|------|------|------|
| 1 | Check prerequisites | 1 min |
| 2 | Verify Docker image | 1 min |
| 3 | Create directories | <1 min |
| 4 | Export Docker to rootfs | 5-10 min |
| 5 | Create bootloader | 1 min |
| 6 | Create GRUB images | 1 min |
| 7 | Extract kernel/initrd | 1 min |
| 8 | Create squashfs (compression) | **10-20 min** |
| 9 | Add branding | <1 min |
| 10 | Generate ISO | 5-15 min |
| 11 | Generate checksums | 2 min |
| 12 | Generate build report | 1 min |
| 13 | Cleanup temp files | 1 min |
| **TOTAL** | | **30-45 min** |

---

## 📁 Output Files

After generation completes:

```
\\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso      (3GB)
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
├── ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.md5
└── build-report.txt
```

**In Windows**: Copy ISO to Downloads
```powershell
Copy-Item '\\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\*.iso' `
  -Destination $env:USERPROFILE\Downloads\
```

---

## 🔥 Burning to USB (3 Options)

### Option 1: Rufus (Easiest - Windows)
1. Download: https://rufus.ie/
2. Open Rufus
3. Device: Select your USB drive
4. Boot: Click "Select" → choose ISO file
5. Click START
6. Done in 5-10 minutes

### Option 2: balena Etcher (All Platforms)
1. Download: https://balena.io/etcher/
2. Select ISO file
3. Select USB drive
4. Click Flash
5. Done in 5-10 minutes

### Option 3: WSL2 dd (Command Line)
```bash
# In WSL2 terminal
lsblk                    # See all drives
# Identify USB drive (e.g., /dev/sdc)

sudo dd if=~/projects/ChimeraIIOS/build-iso/output/*.iso of=/dev/sdX bs=4M status=progress
# Replace /dev/sdX with your USB device
sync
```

---

## 🖥️ Boot from USB

1. Insert USB drive into computer
2. Restart computer
3. During startup, press F12, DEL, or ESC (varies by computer)
4. Select USB drive from boot menu
5. Press Enter
6. Wait for boot...

When ISO loads, you'll see a boot menu:
- Live System (read-only, safe)
- Install Mode (writable)
- Safe Mode (no GPU)
- Diagnostics
- Reboot
- Power Off

---

## 🐛 Troubleshooting

### "WSL2 not found"
```powershell
# Install WSL2
wsl --install

# Restart computer
# Re-run: .\run-iso-generation-wsl2.ps1
```

### "Docker image not found"
```bash
# In WSL2
docker pull amerhwitat/chimera2os:latest
# Or rebuild locally:
# cd ~/ && docker build -t chimera2os:latest .
```

### "Permission denied"
The script automatically uses `sudo`. If issues:
```bash
# In WSL2
sudo bash /tmp/generate-iso-from-docker.sh
```

### "Insufficient disk space"
```bash
# Check available space
wsl df -h /
# Need 15GB+ free

# Clean up Docker if needed
wsl docker system prune -a
```

### "Build times out"
- **Normal!** Squashfs compression takes 10-20 min
- Script doesn't timeout
- Just wait - watch the console
- When "BUILD COMPLETED" appears, it's done

### "ISO won't boot"
1. Verify checksum:
   ```bash
   wsl sha256sum -c ~/projects/ChimeraIIOS/build-iso/output/*.sha256
   ```
2. Re-burn to USB with Rufus or Etcher
3. Try BIOS vs UEFI boot mode (ISO has both)
4. Try different USB drive if available

---

## 🚀 What's on the ISO

### Included Projects (13 Repositories)
- ChimeraIIOS (Core)
- nlp (AI/ML)
- BizX (Business)
- BizXtreme (Enterprise)
- CPU4096 (CPU Sim)
- keygen (Crypto)
- eth-key-check (Web3)
- PDFreaderPY (PDF)
- And more...

### Complete Toolchain
- **Languages**: Python 3.12, Node.js 18+, Rust, Java 21, .NET 8.0
- **Compilers**: GCC 13, Clang 18
- **Build**: CMake, Ninja, Make, Docker, Git
- **Data Science**: TensorFlow, PyTorch, scikit-learn
- **Web**: Flask, FastAPI, Django, SQLAlchemy
- **Dev Tools**: pytest, Jupyter, gdb, Valgrind

### Boot Support
- ✅ BIOS/MBR (older computers)
- ✅ UEFI/GPT (modern computers)
- Both on same ISO

---

## 📋 Before You Start - Checklist

- [ ] WSL2 installed
- [ ] Docker working: `wsl docker --version`
- [ ] 15GB+ free space: `wsl df -h /`
- [ ] Docker image present: `wsl docker images | findstr chimera`
- [ ] PowerShell admin rights
- [ ] USB drive ready (optional, for burning)
- [ ] Rufus or balena Etcher downloaded (optional)

---

## 🎬 Full Workflow (Start to Finish)

### Part 1: Generate ISO (30-45 min)
```powershell
# 1. Open PowerShell as Administrator
cd C:\tmp\ChimeraIIOS

# 2. Verify prerequisites
wsl docker images | findstr chimera
wsl df -h /

# 3. Start generation
.\run-iso-generation-wsl2.ps1

# 4. Watch progress (automatic)
# When console shows "BUILD COMPLETED SUCCESSFULLY", next step
```

### Part 2: Copy ISO to Windows (2 min)
```powershell
# After step 3 completes:
Copy-Item '\\wsl$\Ubuntu\home\<username>\projects\ChimeraIIOS\build-iso\output\*.iso' `
  -Destination $env:USERPROFILE\Downloads\

# Verify
dir $env:USERPROFILE\Downloads\ChimeraIIOS*.iso
```

### Part 3: Burn to USB (5-10 min)
1. Download Rufus: https://rufus.ie/
2. Open Rufus
3. Select USB drive
4. Click "Select" and choose ISO from Downloads
5. Click START
6. Wait for "READY"

### Part 4: Boot System (5 min)
1. Insert USB drive
2. Restart computer
3. Press F12/DEL to enter boot menu
4. Select USB drive
5. Wait for OS to load

### Part 5: Use Chimera II OS 🎉
- Live system ready
- Full development toolchain included
- 13 integrated projects
- All source code and tools available

---

## 📞 Support

**Author**: Amer Abdullah Suleiman Hwitat - عامر الحويطات

- 📧 Email: amer.hwitat@proton.me
- 📍 Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 📦 Repository: https://github.com/amerhwitat/ChimeraIIOS
- 🐳 Docker Hub: https://hub.docker.com/u/amerhwitat

---

## 📖 Files in This Project

| File | Purpose |
|------|---------|
| `generate-iso-from-docker.sh` | 13-step ISO builder (runs on WSL2) |
| `run-iso-generation-wsl2.ps1` | PowerShell wrapper (run from Windows) |
| `ISO_FROM_DOCKER_GUIDE.md` | Comprehensive guide (this file) |
| `ISO_GENERATION_COMPLETE.md` | Detailed overview |
| `ISO_GENERATION_QUICK_START.md` | Quick reference |

---

## ⏱️ How Long Everything Takes

| Task | Time |
|------|------|
| Prerequisites check | 1 min |
| Docker setup | 2-5 min |
| Download Docker image | Already local |
| ISO generation | 30-45 min |
| Copy to Windows | 2-5 min |
| Burn to USB | 5-10 min |
| Boot test | 3-5 min |
| **TOTAL** | ~60-70 min |

---

**Ready? Run this now:**

```powershell
cd C:\tmp\ChimeraIIOS
.\run-iso-generation-wsl2.ps1
```

Then come back in 30-45 minutes! 🚀

---

*created by Amer Abdullah Suleiman Hwitat - عامر الحويطات*
*Amman 11814, Jordan | amer.hwitat@proton.me*
