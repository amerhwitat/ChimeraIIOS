# Chimera II OS - Fix Line Ending Issues in Docker Images

**Fixing: `/usr/bin/env: 'bash\r': No such file or directory`**

## 🚀 Quick Fix (1-2 Hours)

```powershell
cd C:\tmp\ChimeraIIOS
.\fix-line-endings-wsl2.ps1
```

**What happens:**
- Converts CRLF to LF in all scripts
- Fixes shebang lines
- Rebuilds 39 Docker images
- Pushes corrected images to Docker Hub

## 🔍 Problem Analysis

### Symptoms
```
/usr/bin/env: 'bash\r': No such file or directory
/usr/bin/env: use -[v]S to pass options in shebang lines
```

### Root Cause
- Windows CRLF line endings (`\r\n`) in bash scripts
- Correct format is LF only (`\n`)
- Docker runs on Linux which doesn't expect `\r`

### Affected Files
- All `.sh` files (shell scripts)
- Dockerfiles
- Entrypoint scripts
- Startup scripts
- Init scripts

## 📋 What Gets Fixed

### File Conversions
- ✅ Convert all CRLF (`\r\n`) to LF (`\n`)
- ✅ Fix shebang lines (`#!/bin/bash`)
- ✅ Fix entrypoint scripts
- ✅ Fix Dockerfiles
- ✅ Create `.dockerignore` files
- ✅ Make scripts executable

### Docker Images Rebuilt
```
13 Repositories:
  • ChimeraIIOS
  • nlp
  • BizX
  • BizXtreme
  • CPU4096
  • CPU4096Simulator
  • keygen
  • eth-key-check
  • bruteforce
  • PDFreaderPY
  • general
  • test
  • amerhwitat.github.io

39 Total Images (13 × 3 tags each):
  • latest (corrected)
  • v1.0.0-fixed (version)
  • stable (stable)
```

## ⏱️ Timeline

| Phase | Duration |
|-------|----------|
| Fix line endings | 5 min |
| Create Dockerfiles | 5 min |
| Fix entrypoint scripts | 5 min |
| Rebuild 13 images | 30-60 min |
| Push 39 images | 20-40 min |
| Verify & report | 5 min |
| **TOTAL** | **1-2 hours** |

## ✅ Prerequisites

```powershell
wsl --version          # WSL2
wsl docker --version   # Docker
wsl git --version      # Git
wsl df -h /            # 50GB+ free
```

## 🎯 How It Works

### Step 1: Fix Line Endings (5 min)
```bash
# Convert CRLF to LF
sed -i 's/\r$//' *.sh
sed -i 's/\r$//' Dockerfile*

# Fix shebang lines
sed -i '1s/^.*$/#!/bin/bash/' script.sh

# Make executable
chmod +x *.sh
```

### Step 2: Create Dockerfiles (5 min)
```bash
# If Dockerfile missing, create basic one
cat > Dockerfile << 'EOF'
FROM ubuntu:24.04
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y build-essential
CMD ["/bin/bash"]
EOF
```

### Step 3: Fix Entrypoint Scripts (5 min)
```bash
# Find and fix all entrypoint scripts
find . -name "entrypoint.sh" -exec sed -i 's/\r$//' {} +
find . -name "entrypoint.sh" -exec chmod +x {} +
```

### Step 4: Rebuild Images (30-60 min)
```bash
# Remove old image
docker rmi image:latest

# Build corrected image
docker build -t image:latest .

# Tag versions
docker tag image:latest image:v1.0.0-fixed
docker tag image:latest image:stable
```

### Step 5: Push to Docker Hub (20-40 min)
```bash
# Login
docker login -u amerhwitat

# Push all tags
docker push image:latest
docker push image:v1.0.0-fixed
docker push image:stable
```

### Step 6: Verify (5 min)
```bash
# Test image
docker run --rm image:latest /bin/bash -c "echo 'Fixed!'"
```

## 📚 Usage After Fix

### Pull Corrected Images
```bash
# Get latest corrected version
docker pull amerhwitat/chimeraiios:latest

# Get specific fixed version
docker pull amerhwitat/chimeraiios:v1.0.0-fixed

# Get stable corrected version
docker pull amerhwitat/chimeraiios:stable
```

### Run Container
```bash
# Interactive bash
docker run -it amerhwitat/chimeraiios:latest bash

# With volume mount
docker run -it -v $(pwd):/workspace amerhwitat/chimeraiios:latest bash

# In background
docker run -d amerhwitat/chimeraiios:latest
```

### Deploy with Docker Compose
```bash
# Pull latest corrected images
docker-compose -f docker-compose-full.yml pull

# Restart with corrected images
docker-compose -f docker-compose-full.yml down
docker-compose -f docker-compose-full.yml up -d
```

### Deploy to Kubernetes
```bash
# Update deployment with corrected image
kubectl set image deployment/chimera-core \
  chimera-core=amerhwitat/chimeraiios:latest \
  -n chimera-system

# Check rollout
kubectl rollout status deployment/chimera-core -n chimera-system
```

## 🔍 Verification

### Check Line Endings
```bash
# On Linux/WSL2
file script.sh  # Should show "ASCII text, with LF line terminators"

# On Windows (Powershell)
wsl file script.sh
```

### Verify Shebang
```bash
# Check first line
head -1 script.sh  # Should show: #!/bin/bash

# No carriage return
head -1 script.sh | od -c | grep -v "\\n"  # Should output nothing
```

### Test Docker Image
```bash
# Run test in image
docker run --rm amerhwitat/chimeraiios:latest \
  /bin/bash -c "echo 'Success!'"
```

## 🛡️ Prevention for Future

### 1. Configure Git
```bash
# Set auto line ending conversion to LF on commit
git config --global core.safecrlf true
git config --global core.autocrlf input
```

### 2. Create .gitattributes
```
* text=auto
*.sh text eol=lf
Dockerfile text eol=lf
*.py text eol=lf
*.js text eol=lf
```

### 3. Add to Dockerfile
```dockerfile
# Fix any remaining line endings
RUN find / -name "*.sh" -type f -exec sed -i 's/\r$//' {} + 2>/dev/null || true
```

### 4. Use WSL2 for Building
```bash
# On Windows, build in WSL2 instead of native Windows Docker
wsl docker build -t image .
```

## 📁 Output Files

```
~/docker-fix-chimera/
├── repos/ (13 fixed repositories)
├── docker-fix.log
└── LINE_ENDING_FIX_REPORT.txt
```

## 📊 Files Fixed

### Per Repository
- ✅ All `.sh` files
- ✅ All `Dockerfile*` files
- ✅ `entrypoint.sh` / `docker-entrypoint.sh`
- ✅ `startup.sh` scripts
- ✅ `init.sh` scripts
- ✅ `.dockerignore` files

### Total
- ✅ ~50+ shell scripts
- ✅ ~13+ Dockerfiles
- ✅ ~20+ entrypoint/startup scripts
- ✅ All converted from CRLF to LF

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Fix takes too long** | Normal (1-2 hours), don't interrupt |
| **Docker build fails** | Check logs: `docker logs <container>` |
| **Push fails** | Verify credentials: `docker login` |
| **Image still has error** | Rebuild: `docker rmi image:latest` |
| **Line ending not fixed** | Run fix again: `.\fix-line-endings-wsl2.ps1` |

## 📞 Support

**Amer Abdullah Suleiman Hwitat - عامر الحويطات**

- 📧 amer.hwitat@proton.me
- 📍 Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 🐳 Docker Hub: https://hub.docker.com/u/amerhwitat

## 🏁 Next Steps

1. **Run the fix** (1-2 hours)
   ```powershell
   .\fix-line-endings-wsl2.ps1
   ```

2. **Verify corrected images**
   ```bash
   docker pull amerhwitat/chimeraiios:latest
   docker run -it amerhwitat/chimeraiios:latest bash
   ```

3. **Update deployments**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

4. **Prevent future issues**
   ```bash
   git config --global core.autocrlf input
   ```

---

**Status: ✅ READY TO FIX**

All scripts and tools ready. Run the PowerShell wrapper to fix all 39 Docker images.
