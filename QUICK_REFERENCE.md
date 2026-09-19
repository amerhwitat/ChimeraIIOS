# QUICK REFERENCE - CHIMERA II OS COMPREHENSIVE BUILD

**Author**: Amer Abdullah Suleiman Hwitat - عامر الحويطات  
**Email**: amer.hwitat@proton.me  
**Location**: Amman 11814, Jordan

---

## Files Created

| File | Size | Purpose |
|------|------|---------|
| **Dockerfile.comprehensive** | 11.2 KB | Main multi-stage build (ALL repos) |
| **docker-compose.yml** | 4.4 KB | 5-service orchestration |
| **build-comprehensive.sh** | 2.4 KB | Automated build script |
| **COMPREHENSIVE_BUILD_README.md** | 7.9 KB | Full documentation |
| **DOCKERFILE_SUMMARY.md** | 7.3 KB | Build specifications |

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Navigate to repo
cd /path/to/ChimeraIIOS

# 2. Make script executable
chmod +x build-comprehensive.sh

# 3. Build
./build-comprehensive.sh
```

**Expected**: 30-45 min build, ~3GB image, all 13 repos compiled

---

## 📦 What's Included

**13 GitHub Repositories** | **Complete Toolchain**
---|---
ChimeraIIOS | GCC 13, Clang/LLVM
nlp | Python 3.12 + ML stack
BizX | Node.js 18+
BizXtreme | Rust + Cargo
CPU4096 | Java 21 JDK
CPU4096Simulator | .NET SDK 8.0
keygen | CMake, Ninja
eth-key-check | TensorFlow, PyTorch
bruteforce | scikit-learn
PDFreaderPY | Flask, FastAPI
general | SQL databases
test | Git, Docker
portfolio | Testing tools

---

## 🐳 Running Container

### Basic
```bash
docker run -it --rm chimera2os-comprehensive:latest
```

### With Mounts & Ports
```bash
docker run -it --rm \
  -v $(pwd)/workspace:/workspace \
  -p 8000:8000 -p 5000:5000 \
  chimera2os-comprehensive:latest
```

### All Services (Docker Compose)
```bash
docker-compose up -d
docker-compose logs -f
```

---

## 📂 Container Structure

```
/opt/chimera/
  ├── applications/        ← All 13 apps
  ├── bin/                 ← Executables
  ├── lib/                 ← Libraries
  └── scripts/
        ├── init-chimera.sh
        └── docker-entrypoint.sh

/src/chimera/             ← Source code
/workspace/               ← User workspace (mounted)
```

---

## 🔧 Common Tasks

### NLP Processing
```bash
docker run --rm \
  -v /data:/workspace \
  chimera2os-comprehensive:latest \
  bash -c "cd /opt/chimera/applications/nlp && python3 main.py"
```

### BizX Web Service
```bash
docker run -d \
  --name bizx \
  -p 8000:8000 \
  chimera2os-comprehensive:latest \
  bash -c "cd /opt/chimera/applications/BizX && npm start"
```

### CPU Simulator
```bash
docker run -it --rm \
  -p 3000:3000 \
  chimera2os-comprehensive:latest \
  bash -c "cd /opt/chimera/applications/CPU4096Simulator && npm start"
```

### Dev Shell
```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  chimera2os-comprehensive:latest \
  bash
```

---

## 🐳 Docker Compose Commands

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale NLP service (3 instances)
docker-compose up -d --scale nlp-service=3

# Run specific service
docker-compose up nlp-service
docker-compose up bizx-service
docker-compose up cpu-simulator

# Stop all
docker-compose down

# Clean volumes
docker-compose down -v

# Execute command in running service
docker-compose exec chimera-core ls -la /opt/chimera/applications
```

---

## 🔌 Exposed Ports

| Port | Service |
|------|---------|
| 8000 | Web services |
| 8080 | Alternative web |
| 8001 | NLP API (compose) |
| 8002 | BizX API (compose) |
| 9000 | APIs |
| 9001 | Admin panel |
| 5000 | Flask development |
| 3000 | Node.js services |
| 3001 | BizX UI (compose) |
| 3002 | CPU Simulator (compose) |

---

## 📤 Deployment

### Docker Hub
```bash
docker tag chimera2os-comprehensive:latest your-username/chimera2os-comprehensive:latest
docker login
docker push your-username/chimera2os-comprehensive:latest
```

### Private Registry
```bash
docker tag chimera2os-comprehensive:latest registry.example.com/chimera2os-comprehensive:latest
docker push registry.example.com/chimera2os-comprehensive:latest
```

### Pull & Use
```bash
docker pull your-username/chimera2os-comprehensive:latest
docker run -it your-username/chimera2os-comprehensive:latest
```

---

## ⚙️ Environment Variables (Container)

```bash
INSTALL_DIR=/opt/chimera
APPS_DIR=/opt/chimera/applications
SRC_DIR=/src/chimera
PYTHONPATH=/opt/chimera/applications:/opt/chimera/lib/python
LD_LIBRARY_PATH=/opt/chimera/lib
PATH=/opt/chimera/bin:/opt/chimera/applications/bin:$PATH
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Build timeout | Increase Docker memory to 8GB+ |
| Out of disk | Need 50GB+ free space |
| App not found | `docker run --rm chimera2os-comprehensive:latest ls -la /opt/chimera/applications` |
| Permission denied | Check user (chimera, UID 10001) |
| Port in use | Map to different host port: `-p 9000:8000` |

---

## 📚 Documentation

- **Full README**: `COMPREHENSIVE_BUILD_README.md`
- **Build Specs**: `DOCKERFILE_SUMMARY.md`
- **Dockerfile**: `Dockerfile.comprehensive`
- **Compose Config**: `docker-compose.yml`
- **Build Script**: `build-comprehensive.sh`

---

## 👤 Author & Support

| Detail | Value |
|--------|-------|
| **Created by** | Amer Abdullah Suleiman Hwitat - عامر الحويطات |
| **Email** | amer.hwitat@proton.me |
| **Location** | Amman 11814, Jordan |
| **GitHub** | https://github.com/amerhwitat |
| **Repositories** | 13 integrated into single image |

---

## ✅ Checklist Before Building

- [ ] Docker installed and running
- [ ] 50GB+ free disk space
- [ ] 8GB+ Docker memory allocated
- [ ] CD to ChimeraIIOS directory
- [ ] Read `COMPREHENSIVE_BUILD_README.md`

---

## 🚀 Start Building

```bash
./build-comprehensive.sh
# or
docker build -f Dockerfile.comprehensive -t chimera2os-comprehensive:latest .
```

**Estimated time**: 30-45 minutes  
**Final image size**: 2.5-3.5 GB

---

**"created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"**  
**Amman 11814, Jordan | amer.hwitat@proton.me**
