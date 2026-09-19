# WSL2 SETUP GUIDE - CHIMERA II OS
## Complete Guide to Building Chimera II OS in WSL2 on Windows

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحويطات  
**Contact**: amer.hwitat@proton.me  
**Location**: Amman 11814, Jordan

---

## Overview

This guide provides step-by-step instructions to:
1. Enable WSL2 on Windows 10/11
2. Install Ubuntu in WSL2
3. Set up Docker in WSL2
4. Build the complete Chimera II OS (Docker image + ISO)
5. Manage WSL2 distributions

---

## Prerequisites

- **Windows 10** (Build 19041 or later) or **Windows 11**
- **8GB+ RAM** (16GB+ recommended)
- **100GB+ free disk space**
- Administrator access
- Virtualization enabled in BIOS

---

## PART 1: ENABLE WSL2

### Step 1.1: Check Windows Version

Open PowerShell as Administrator and run:

```powershell
Get-ComputerInfo | Select-Object OSName, OSVersion, OSBuildNumber
```

Expected: Windows 10 Build 19041+ or Windows 11

### Step 1.2: Enable WSL Feature

Run as Administrator in PowerShell:

```powershell
# Enable WSL
wsl --install
```

This will:
- Enable Windows Subsystem for Linux
- Enable Virtual Machine Platform
- Install Ubuntu (latest) by default
- Install WSL kernel

**If prompted to restart, do so.**

### Step 1.3: Alternative - Manual Enable (if `wsl --install` fails)

```powershell
# Enable features manually
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart

# Restart
Restart-Computer
```

### Step 1.4: Download WSL2 Kernel

After restart, run:

```powershell
# Download latest WSL2 kernel
wsl --update
```

### Step 1.5: Verify WSL2 Installation

```powershell
# Check WSL version
wsl --version

# List installed distributions
wsl --list --verbose
```

Expected output:
```
WSL version: 2.x.x
...
NAME       STATE      VERSION
Ubuntu     Running    2
```

---

## PART 2: INSTALL UBUNTU IN WSL2

### Step 2.1: Download Ubuntu

Option A - Automatic (Recommended):

```powershell
# Install latest Ubuntu
wsl --install -d Ubuntu
```

Option B - Manual:

```powershell
# List available distributions
wsl --list --online

# Install specific version
wsl --install -d Ubuntu-22.04
```

### Step 2.2: First Launch & Setup

After installation, Ubuntu WSL will launch automatically. You'll be prompted to:

```bash
# Create username (choose something simple, e.g., 'builder')
Enter new UNIX username: builder

# Create password
Enter new UNIX password: ****
Retype password: ****
```

Save your credentials securely.

### Step 2.3: Initialize Ubuntu

Once logged in, run:

```bash
# Update package lists
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y

# Install essential utilities
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    ca-certificates \
    vim \
    nano
```

### Step 2.4: Configure WSL2 Resources

Create/edit `C:\Users\<YourUsername>\.wslconfig`:

```ini
[wsl2]
memory=16GB
processors=4
swap=4GB
localhostForwarding=true
```

Restart WSL:

```powershell
# From Windows PowerShell (Admin)
wsl --shutdown
```

Then launch Ubuntu again.

---

## PART 3: INSTALL DOCKER IN WSL2

### Step 3.1: Install Docker Community Edition

In WSL2 Ubuntu terminal:

```bash
# Install Docker setup prerequisites
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker run hello-world
```

### Step 3.2: Configure Docker for WSL2

Edit `/etc/docker/daemon.json`:

```bash
sudo nano /etc/docker/daemon.json
```

Add or modify:

```json
{
    "data-root": "/mnt/docker-data",
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
```

Restart Docker:

```bash
sudo systemctl restart docker
```

### Step 3.3: Allocate Storage Space

```bash
# Create docker data directory on fast drive
mkdir -p /mnt/docker-data

# Verify Docker can write
docker run --rm busybox echo "Docker is working!"
```

---

## PART 4: CLONE CHIMERA II OS REPOSITORY

### Step 4.1: Clone from GitHub

In WSL2 Ubuntu:

```bash
# Create workspace
mkdir -p ~/projects
cd ~/projects

# Clone repository (will be added after push)
git clone https://github.com/amerhwitat/ChimeraIIOS.git
cd ChimeraIIOS

# Or if using local files, copy from Windows
cp -r /mnt/c/tmp/ChimeraIIOS/* .
```

### Step 4.2: Verify Files

```bash
# List files
ls -la

# Verify key files
ls -la Dockerfile.fixed docker-compose.yml build-chimera-iso.sh
```

---

## PART 5: BUILD DOCKER IMAGE IN WSL2

### Step 5.1: Build the Image

```bash
cd ~/projects/ChimeraIIOS

# Build Docker image (30-45 minutes)
docker build -f Dockerfile.fixed \
    -t chimera2os-comprehensive:latest \
    -t chimera2os-comprehensive:v1.0 \
    --progress=plain .
```

Monitor progress:

```bash
# In another terminal, watch Docker
docker images chimera2os-comprehensive
docker system df
```

### Step 5.2: Verify Image Built Successfully

```bash
# List images
docker images | grep chimera2os

# Expected output:
# chimera2os-comprehensive   latest   <IMAGE_ID>   <TIME>   ~3GB
# chimera2os-comprehensive   v1.0     <IMAGE_ID>   <TIME>   ~3GB

# Run container
docker run -it --rm chimera2os-comprehensive:latest

# Inside container, verify apps
ls -la /opt/chimera/applications
python3 --version
node --version
```

### Step 5.3: Save Image

```bash
# Export image to tar file (for backup/transfer)
docker save chimera2os-comprehensive:latest -o chimera2os-comprehensive.tar.gz

# List saved image
ls -lh chimera2os-comprehensive.tar.gz
```

---

## PART 6: CREATE BOOTABLE ISO IN WSL2

### Step 6.1: Install ISO Building Tools

```bash
sudo apt update
sudo apt install -y \
    xorriso \
    grub-pc-bin \
    grub-efi-amd64-bin \
    squashfs-tools \
    mtools \
    dosfstools
```

### Step 6.2: Run ISO Builder Script

```bash
cd ~/projects/ChimeraIIOS

# Make script executable
chmod +x build-chimera-iso.sh

# Run full build (Docker + ISO) - 1-2 hours total
sudo bash build-chimera-iso.sh
```

### Step 6.3: Monitor Build Progress

In another WSL2 terminal:

```bash
# Watch Docker image build
docker ps

# Watch disk space
df -h

# Watch logs
tail -f ~/projects/ChimeraIIOS/build.log 2>/dev/null || echo "Waiting for build.log..."
```

### Step 6.4: Verify ISO Creation

```bash
cd ~/projects/ChimeraIIOS

# Check ISO file
ls -lh ChimeraIIOS-comprehensive-*.iso*

# Verify checksums
sha256sum -c ChimeraIIOS-comprehensive-*.sha256

# Check file type
file ChimeraIIOS-comprehensive-*.iso
```

### Step 6.5: Transfer ISO to Windows

```bash
# Copy ISO to Windows accessible location
cp ChimeraIIOS-comprehensive-*.iso* /mnt/c/Users/$USER/Downloads/

# Verify in Windows
cd /mnt/c/Users/$USER/Downloads/
ls -lh ChimeraIIOS-comprehensive-*.iso*
```

---

## PART 7: USING THE ISO

### Step 7.1: Burn to USB (from Windows)

Download **Rufus** or **balena Etcher**:
- https://rufus.ie/
- https://www.balena.io/etcher/

Then:
1. Insert USB drive
2. Open Rufus/Etcher
3. Select ISO: `ChimeraIIOS-comprehensive-1.0.0-x86_64.iso`
4. Select USB drive
5. Click "Write" or "Flash"
6. Wait for completion

### Step 7.2: Test with QEMU in WSL2

```bash
# Install QEMU
sudo apt install -y qemu-system-x86 qemu-utils

# Boot ISO (30 second test)
timeout 30 qemu-system-x86_64 \
    -cdrom ~/projects/ChimeraIIOS/ChimeraIIOS-comprehensive-*.iso \
    -m 2G \
    -smp 2 \
    -serial stdio || echo "Boot test completed"
```

### Step 7.3: Boot from USB

1. Insert USB into computer
2. Restart computer
3. Enter BIOS (Del, F12, F2, or Esc - depends on manufacturer)
4. Set boot order: USB first
5. Save and exit
6. Computer boots Chimera II OS

---

## PART 8: WSL2 MANAGEMENT

### Common WSL2 Commands

```powershell
# From Windows PowerShell (Admin)

# List distributions
wsl --list --verbose

# Launch specific distribution
wsl -d Ubuntu

# Set default distribution
wsl --setdefault Ubuntu

# Terminate all WSL instances
wsl --shutdown

# Terminate specific distribution
wsl --terminate Ubuntu

# Export distribution (backup)
wsl --export Ubuntu C:\backup\ubuntu-backup.tar

# Import distribution (restore)
wsl --import Ubuntu C:\wsl\ubuntu ubuntu-backup.tar

# Remove distribution
wsl --unregister Ubuntu

# Check WSL version
wsl --version

# Update WSL kernel
wsl --update
```

### Storage Management

```bash
# In WSL2 Ubuntu

# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up old images
docker image prune -a

# Clean up stopped containers
docker container prune

# Clean up volumes
docker volume prune

# Total cleanup (WARNING: removes all)
docker system prune -a --volumes
```

### Performance Tuning

Create `.wslconfig`:

```ini
[wsl2]
# Memory allocation (in GB)
memory=16GB

# CPU count
processors=4

# Swap file size
swap=4GB

# Swap file location
swapfile=/mnt/wsl/swap.vhdx

# Localhost forwarding
localhostForwarding=true

# Nested virtualization (for QEMU)
nestedVirtualization=true

# IP Forwarding
ipForwarding=true
```

Then restart:

```powershell
wsl --shutdown
# Relaunch WSL2
```

---

## TROUBLESHOOTING

### Issue: "WSL 2 requires an update to its kernel component"

**Solution:**

```powershell
wsl --update
wsl --shutdown
```

### Issue: Docker fails to start in WSL2

**Solution:**

```bash
# In WSL2
sudo dockerd -D

# Or reset Docker
sudo systemctl reset-failed docker
sudo systemctl start docker
```

### Issue: Out of disk space in WSL2

**Solution:**

```bash
# Compact WSL2 virtual disk
wsl --shutdown
```

Then in PowerShell (Admin):

```powershell
# Find your Ubuntu distribution path
Get-ChildItem $env:LOCALAPPDATA\Packages -Filter "*Ubuntu*"

# Compact disk (replace USERNAME and PATH as needed)
diskpart
select vdisk file="C:\Users\USERNAME\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_XXXX\LocalState\ext4.vhdx"
compact vdisk
detach vdisk
exit
```

### Issue: Build fails with "Connection timed out"

**Solution:**

```bash
# In WSL2, use different mirror
sudo sed -i 's/archive.ubuntu.com/mirror.example.com/g' /etc/apt/sources.list

# Or manually edit
sudo nano /etc/apt/sources.list

# Update
sudo apt update
```

### Issue: ISO won't boot

**Checklist:**
- [ ] Verify checksums: `sha256sum -c *.sha256`
- [ ] Re-burn to USB with `--sync` flag
- [ ] Try different USB port
- [ ] Enable BIOS legacy boot mode
- [ ] Disable Secure Boot
- [ ] Try different USB drive

### Issue: Can't access Windows files from WSL2

**Solution:**

```bash
# Windows C: drive is mounted at /mnt/c
ls /mnt/c

# Access user profile
ls /mnt/c/Users/$USER

# Create symlink for easy access
ln -s /mnt/c/tmp ~/windows-tmp
```

---

## QUICK REFERENCE

### One-Command Setup (Fast)

```powershell
# Windows PowerShell (Admin)
wsl --install
```

Then in WSL2:

```bash
# Copy all commands from Step 3.1 - Install Docker
# Then
cd /path/to/ChimeraIIOS
docker build -f Dockerfile.fixed -t chimera2os-comprehensive:latest .
sudo bash build-chimera-iso.sh
```

### Directory Structure

```
Windows:
C:\Users\<USERNAME>
├── Downloads\
│   └── ChimeraIIOS-comprehensive-*.iso
└── AppData\Local\
    └── Packages\
        └── CanonicalGroupLimited.Ubuntu_XXXX\
            └── LocalState\
                └── ext4.vhdx (WSL2 disk)

WSL2 Ubuntu:
~/
├── projects\
│   └── ChimeraIIOS\
│       ├── Dockerfile.fixed
│       ├── build-chimera-iso.sh
│       ├── docker-compose.yml
│       └── ChimeraIIOS-comprehensive-*.iso
├── .wslconfig (if copied from C:\Users\<USERNAME>\)
└── .docker\
    └── config.json
```

---

## Performance Expectations

| Stage | Time | Resources |
|-------|------|-----------|
| WSL2 Setup | 10 min | Network |
| Docker Install | 5 min | 2GB |
| Docker Image Build | 30-45 min | 8GB RAM + CPU |
| ISO Creation | 10-15 min | 2GB RAM |
| **Total** | **1-2 hours** | **16GB RAM, 100GB disk** |

---

## Advanced: Multiple WSL2 Distributions

```powershell
# Install multiple distributions
wsl --install -d Ubuntu-22.04
wsl --install -d Debian
wsl --install -d Ubuntu-20.04

# Switch between them
wsl -d Ubuntu-22.04
wsl -d Debian

# Build in different distros
wsl -d Ubuntu-22.04 -e bash -c "cd ~/projects/ChimeraIIOS && docker build ..."
```

---

## Next Steps

1. ✅ Enable WSL2
2. ✅ Install Ubuntu
3. ✅ Install Docker
4. ✅ Clone repository
5. ✅ Build Docker image
6. ✅ Create ISO
7. ✅ Burn to USB or test in VM
8. ✅ Boot and install Chimera II OS

---

## Support & Resources

| Resource | Link |
|----------|------|
| **WSL Documentation** | https://learn.microsoft.com/en-us/windows/wsl/ |
| **Docker in WSL2** | https://docs.docker.com/desktop/wsl/ |
| **Chimera II OS** | https://github.com/amerhwitat/ChimeraIIOS |
| **Issues** | https://github.com/amerhwitat/ChimeraIIOS/issues |

---

## Author

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحويطات  
**Email**: amer.hwitat@proton.me  
**Location**: Amman 11814, Jordan  
**GitHub**: https://github.com/amerhwitat

---

**"created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"**  
**Amman 11814, Jordan | amer.hwitat@proton.me**
