# ChimeraIIOS - Comprehensive Edition

**A complete, production-ready Docker image and bootable ISO containing 13 integrated GitHub repositories**

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحويطات  
**Email**: amer.hwitat@proton.me  
**Location**: Amman 11814, Jordan

---

## 🎯 Overview

Chimera II OS is a comprehensive Docker-based Linux distribution that integrates **13 complete GitHub repositories** with a full development toolchain, data science stack, and web frameworks. The project includes:

- ✅ **Multi-stage Docker image** (~3GB, fully compiled)
- ✅ **Bootable ISO** (BIOS/UEFI dual-boot)
- ✅ **5 Docker Compose services** (NLP, BizX, CPU Simulator, Core, Dev)
- ✅ **Complete toolchain**: GCC 13, Clang, Python 3.12, Node 18+, Rust, Java 21, .NET 8.0
- ✅ **Data science stack**: TensorFlow, PyTorch, scikit-learn, Keras
- ✅ **Web frameworks**: Flask, FastAPI, SQLAlchemy
- ✅ **Development tools**: Git, Docker, Jupyter, pytest, Pylint, Black
- ✅ **13 integrated repositories**
- ✅ **Production-ready** with health checks, security hardening

---

## 📚 Quick Start

### Option 1: Docker Image Only (30-45 minutes)

```bash
# Build Docker image
docker build -f Dockerfile.fixed -t chimera2os-comprehensive:latest .

# Run container
docker run -it --rm chimera2os-comprehensive:latest

# Inside container, verify all 13 apps are available
ls -la /opt/chimera/applications/
```

### Option 2: Docker Compose (Easy)

```bash
# Build and start all services
docker-compose up -d

# Access services
# - Core: http://localhost:8000
# - NLP:  http://localhost:8001
# - BizX: http://localhost:3001
# - CPU:  http://localhost:3002

docker-compose logs -f
```

### Option 3: Complete ISO Build (1-2 hours on WSL2)

```bash
# On Windows: Enable WSL2 first
# See: WSL2_SETUP_GUIDE.md

# In WSL2 Ubuntu:
cd ~/projects/ChimeraIIOS
docker build -f Dockerfile.fixed -t chimera2os-comprehensive:latest .
sudo bash build-chimera-iso.sh

# Result: ChimeraIIOS-comprehensive-1.0.0-x86_64.iso (~3GB)
# Burn to USB or test with QEMU
```

---

## 📂 Repository Structure

```
ChimeraIIOS/
├── Dockerfile.fixed ......................... Fixed production Dockerfile
├── Dockerfile.iso-builder ................... Containerized ISO builder
├── Dockerfile ............................ Simple alternative
├── docker-compose.yml ..................... 5-service orchestration
│
├── build-chimera-iso.sh ................... Complete ISO build pipeline
├── build-comprehensive.sh ................. Docker image builder only
│
├── WSL2_SETUP_GUIDE.md ................... Complete WSL2 setup (THIS SYSTEM)
├── ISO_BUILD_GUIDE.md .................... ISO building instructions
├── COMPREHENSIVE_BUILD_README.md .......... Docker image documentation
├── DOCKERFILE_SUMMARY.md ................. Technical specifications
├── QUICK_REFERENCE.md .................... 1-page quick reference
├── FILE_INDEX.md .......................... File listing & navigation
├── BUILD_SYSTEM_COMPLETE.md .............. System overview
│
├── .dockerignore .......................... Docker build exclude patterns
├── .gitignore ............................ Git ignore patterns
│
└── [13 integrated GitHub repositories]
    ├── ChimeraIIOS/ (core OS)
    ├── nlp/ (NLP/AI)
    ├── BizX/ (business app)
    ├── BizXtreme/ (enterprise)
    ├── CPU4096/ (4096-bit CPU sim)
    ├── CPU4096Simulator/ (web sim)
    ├── keygen/ (cryptography)
    ├── eth-key-check/ (ethereum)
    ├── bruteforce/ (security)
    ├── PDFreaderPY/ (PDF)
    ├── general/ (utilities)
    ├── test/ (testing)
    └── amerhwitat.github.io/ (docs)
```

---

## 🚀 Building on THIS SYSTEM (Windows with WSL2)

### Prerequisites

- Windows 10 (Build 19041+) or Windows 11 ✅
- 16GB+ RAM ✅
- 100GB+ free disk space ✅
- WSL2 installed ✅

### Fast Start (5 minutes)

```powershell
# Windows PowerShell (Admin)
git clone https://github.com/amerhwitat/ChimeraIIOS.git
cd ChimeraIIOS

# Launch WSL2
wsl -d Ubuntu

# In WSL2:
cd /mnt/c/path/to/ChimeraIIOS
docker build -f Dockerfile.fixed -t chimera2os-comprehensive:latest .
```

### Full Setup with WSL2

See **[WSL2_SETUP_GUIDE.md](WSL2_SETUP_GUIDE.md)** for:
- ✅ Enable WSL2 (automated)
- ✅ Install Ubuntu in WSL2
- ✅ Install Docker in WSL2
- ✅ Build Docker image
- ✅ Create ISO
- ✅ Manage WSL2
- ✅ Troubleshooting

---

## 📦 13 Integrated Repositories

| # | Repository | Language | Purpose |
|---|-----------|----------|---------|
| 1 | **ChimeraIIOS** | Python/C++ | Core OS platform |
| 2 | **nlp** | Python | NLP, BTC, OCR, neural networks |
| 3 | **BizX** | JavaScript | Business application |
| 4 | **BizXtreme** | Python | Enterprise platform |
| 5 | **CPU4096** | C++ | 4096-bit CPU simulator |
| 6 | **CPU4096Simulator** | JavaScript | Web simulator UI |
| 7 | **keygen** | Java | Cryptographic key generation |
| 8 | **eth-key-check** | Python | Ethereum key validation |
| 9 | **bruteforce** | Python | Security testing tools |
| 10 | **PDFreaderPY** | Python | PDF processing |
| 11 | **general** | Python | Utilities framework |
| 12 | **test** | Python | Testing infrastructure |
| 13 | **amerhwitat.github.io** | HTML/CSS | Portfolio & documentation |

---

## 🛠️ Complete Toolchain Included

### Compilers & Languages
- **GCC 13**, **Clang/LLVM**
- **Python 3.12** + pip, venv, setuptools
- **Node.js 18+** + npm
- **Rust** (latest) + Cargo
- **Java 21 JDK** (headless + full)
- **.NET SDK 8.0**
- **Perl** + modules
- **Rustc** (latest)

### Build Tools
- **CMake 3.x**, **Ninja**, **Make**
- **Automake**, **Autoconf**, **Libtool**
- **Git** (with git-flow)
- **Docker**, **Docker Compose**

### Data Science Stack
- **NumPy**, **SciPy**, **Pandas**
- **TensorFlow**, **Keras**
- **PyTorch**
- **scikit-learn**
- **Matplotlib**, **Plotly**
- **Jupyter**, **IPython**
- **NLTK**, **spaCy**

### Web Frameworks
- **Flask**, **FastAPI**, **Uvicorn**
- **SQLAlchemy**, **SQLite3**
- **PostgreSQL client**, **Redis**

### Development & Testing
- **pytest**, **unittest**
- **gdb**, **Valgrind**, **strace**
- **Pylint**, **Black**, **Flake8**
- **Sphinx**, **Doxygen**, **Graphviz**

### Utilities
- **curl**, **wget**, **openssh**
- **tar**, **gzip**, **bzip2**, **xz**
- **vim**, **nano**
- **systemd**, **systemctl**

---

## 🐳 Docker Compose Services

### Run All Services

```bash
docker-compose up -d
```

| Service | Port | Image | Purpose |
|---------|------|-------|---------|
| **chimera-core** | 8000 | chimera2os | Main development environment |
| **nlp-service** | 8001, 5000 | chimera2os | NLP processing API |
| **bizx-service** | 3001, 8002 | chimera2os | Business application |
| **cpu-simulator** | 3002, 3000 | chimera2os | CPU simulator web UI |
| **dev-shell** | - | chimera2os | Interactive dev environment |

### Commands

```bash
# Build all
docker-compose build

# Start all
docker-compose up -d

# View logs
docker-compose logs -f nlp-service

# Scale service
docker-compose up -d --scale nlp-service=3

# Stop all
docker-compose down -v
```

---

## 📊 Build Specifications

| Aspect | Value |
|--------|-------|
| **Base OS** | Ubuntu 24.04 LTS |
| **Docker Image Size** | 2.5-3.5 GB |
| **ISO Size** | 2.5-3.5 GB (compressed) |
| **Build Time** | 30-45 min (Docker), 1-2 hours (ISO) |
| **Boot Methods** | BIOS/MBR + UEFI/GPT |
| **User Account** | chimera (UID 10001) |
| **Working Directory** | /workspace (in container) |
| **Repositories** | 13 integrated, all compiled |

---

## 🖥️ System Requirements

### For Building (Minimum)

- 8GB RAM (16GB+ recommended)
- 100GB+ free disk space
- 4+ CPU cores
- Network connection (1+ Mbps)

### For Building on Windows (Recommended)

- Windows 10 Build 19041+ or Windows 11
- 16GB+ RAM allocated to WSL2
- 100GB+ free disk space
- WSL2 enabled
- Docker Desktop (optional, or install Docker in WSL2)

### For Running Container

- Docker 20.10+
- 4GB+ available RAM
- 10GB+ disk space

---

## 🚀 Usage Examples

### Run Interactive Shell

```bash
docker run -it --rm chimera2os-comprehensive:latest /bin/bash
```

### Run with Mounted Workspace

```bash
docker run -it --rm \
  -v $(pwd)/workspace:/workspace \
  -p 8000:8000 -p 5000:5000 \
  chimera2os-comprehensive:latest
```

### Run NLP Service Only

```bash
docker run -it --rm \
  -p 5000:5000 \
  -e "SERVICE=nlp" \
  chimera2os-comprehensive:latest
```

### Run in Background

```bash
docker run -d \
  --name chimera-dev \
  -v $(pwd)/src:/workspace/src \
  -p 8000:8000 \
  chimera2os-comprehensive:latest
```

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[WSL2_SETUP_GUIDE.md](WSL2_SETUP_GUIDE.md)** | Complete WSL2 setup (THIS SYSTEM) |
| **[ISO_BUILD_GUIDE.md](ISO_BUILD_GUIDE.md)** | Building bootable ISO image |
| **[COMPREHENSIVE_BUILD_README.md](COMPREHENSIVE_BUILD_README.md)** | Docker image details |
| **[DOCKERFILE_SUMMARY.md](DOCKERFILE_SUMMARY.md)** | Technical specifications |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Quick command reference |

---

## 🔧 Building Docker Image

### Standard Build

```bash
docker build -f Dockerfile.fixed -t chimera2os-comprehensive:latest .
```

### With Progress Output

```bash
docker build -f Dockerfile.fixed \
  -t chimera2os-comprehensive:latest \
  --progress=plain .
```

### With Custom Tag

```bash
docker build -f Dockerfile.fixed \
  -t registry.example.com/chimera2os:v1.0 \
  -t chimera2os-comprehensive:latest .
```

### Build Time

```
Package download & install:  ~10-15 min
Repository cloning:           ~5-10 min
Compilation & setup:         ~10-20 min
Total:                        ~30-45 minutes
```

---

## 📦 Creating ISO (Linux/WSL2 Only)

```bash
# In Linux/WSL2 environment
cd ~/projects/ChimeraIIOS

# Full build (Docker + ISO)
sudo bash build-chimera-iso.sh

# Or Docker image only
sudo bash build-chimera-iso.sh --docker-only

# Or ISO only (Docker already exists)
sudo bash build-chimera-iso.sh --iso-only
```

### Expected Output

```
ChimeraIIOS-comprehensive-1.0.0-x86_64.iso      (~3 GB)
ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.sha256
ChimeraIIOS-comprehensive-1.0.0-x86_64.iso.md5
build-report.txt
```

---

## 🔐 Security Features

- ✅ Multi-stage build (minimal runtime)
- ✅ Non-root chimera user (UID 10001)
- ✅ Health checks enabled
- ✅ No hardcoded secrets
- ✅ Layer caching for faster rebuilds
- ✅ Clean package cache

---

## 🐛 Troubleshooting

### Build fails with network timeout

```bash
# Retry with different mirror
sudo sed -i 's/archive.ubuntu.com/mirror.example.com/g' /etc/apt/sources.list
sudo apt update
```

### Docker image too large

```bash
# Clean up after build
docker system prune -a
```

### WSL2 out of disk space

See **[WSL2_SETUP_GUIDE.md](WSL2_SETUP_GUIDE.md)** § Storage Management

### ISO won't boot

See **[ISO_BUILD_GUIDE.md](ISO_BUILD_GUIDE.md)** § Troubleshooting

---

## 📝 License

This project integrates 13 repositories. Each maintains its original license. For commercial use, verify licenses of integrated components.

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📞 Support

| Type | Contact |
|------|---------|
| **Issues** | GitHub Issues |
| **Email** | amer.hwitat@proton.me |
| **GitHub** | https://github.com/amerhwitat |

---

## 👤 Author

**Amer Abdullah Suleiman Hwitat - عامر الحويطات**

- 📧 Email: amer.hwitat@proton.me
- 📍 Location: Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 📚 Portfolio: https://amerhwitat.github.io

---

**"created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"**  
**Amman 11814, Jordan | amer.hwitat@proton.me**

---

### Quick Links

- 🚀 **[WSL2 Setup](WSL2_SETUP_GUIDE.md)** - For Windows users (recommended)
- 🔨 **[ISO Build](ISO_BUILD_GUIDE.md)** - For Linux/WSL2 users
- 📖 **[Quick Reference](QUICK_REFERENCE.md)** - Commands & usage
- 📋 **[File Index](FILE_INDEX.md)** - Complete file listing

---

*Last updated: 2026-09-19*  
*Status: ✅ Production Ready*  
*Build version: 1.0.0*
