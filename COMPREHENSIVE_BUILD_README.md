# CHIMERA II OS - COMPREHENSIVE DOCKER IMAGE
## All amerhwitat GitHub Repositories Integrated & Compiled

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحويطات  
**Location**: Amman 11814, Jordan  
**Contact**: amer.hwitat@proton.me

---

## Overview

This Docker image integrates **ALL** repositories from the amerhwitat GitHub account and creates a comprehensive development environment with:

- **ChimeraIIOS**: Core operating system platform
- **NLP**: Natural language processing and AI tools
- **BizX & BizXtreme**: Business applications
- **CPU4096 & CPU4096Simulator**: 4096-bit CPU simulators
- **Crypto Tools**: Keygen, ETH key checking, bruteforce utilities
- **Utilities**: PDF reader and other tools
- **Complete Toolchain**: C++, Python, Node.js, Java, Rust, .NET, and more

---

## Included Repositories

| Repository | Language | Purpose |
|-----------|----------|---------|
| ChimeraIIOS | Python/C++ | Core OS platform |
| nlp | Python | NLP, AI, neural networks |
| BizX | JavaScript | Business application |
| BizXtreme | Python | Enterprise platform |
| CPU4096 | C++ | 4096-bit CPU simulator |
| CPU4096Simulator | JavaScript | Web-based simulator |
| keygen | Java | Cryptographic key generation |
| eth-key-check | Python | Ethereum key validation |
| bruteforce | Python | Security testing tools |
| PDFreaderPY | Python | PDF processing |
| general | Python | Utilities and reference |
| test | Python | Testing framework |
| amerhwitat.github.io | HTML/CSS | Portfolio and documentation |

---

## Build Instructions

### Prerequisites
- Docker installed and running
- At least 50GB free disk space
- 30-45 minutes build time

### Quick Build

```bash
# Navigate to ChimeraIIOS directory
cd /path/to/ChimeraIIOS

# Make build script executable
chmod +x build-comprehensive.sh

# Run the build
./build-comprehensive.sh
```

### Custom Build

```bash
docker build \
    -f Dockerfile.comprehensive \
    -t chimera2os-comprehensive:latest \
    --progress=plain \
    .
```

### Build with Specific Tag

```bash
docker build \
    -f Dockerfile.comprehensive \
    -t chimera2os-comprehensive:v1.0 \
    -t chimera2os-comprehensive:latest \
    .
```

---

## Running the Container

### Basic Interactive Shell

```bash
docker run -it --rm chimera2os-comprehensive:latest
```

### With Volume Mount

```bash
docker run -it --rm \
    -v $(pwd)/workspace:/workspace \
    chimera2os-comprehensive:latest
```

### With Port Mappings

```bash
docker run -it --rm \
    -p 8000:8000 \
    -p 8080:8080 \
    -p 9000:9000 \
    -p 5000:5000 \
    -p 3000:3000 \
    chimera2os-comprehensive:latest
```

### Run Specific Application

```bash
# Run NLP module
docker run --rm \
    -v $(pwd)/data:/workspace \
    chimera2os-comprehensive:latest \
    python3 /opt/chimera/applications/nlp/main.py

# Run BizX application
docker run --rm \
    -p 8000:8000 \
    chimera2os-comprehensive:latest \
    npm start --prefix /opt/chimera/applications/BizX
```

---

## Environment Variables

Inside the container, the following are available:

```bash
# Application directories
INSTALL_DIR=/opt/chimera
APPS_DIR=/opt/chimera/applications
SRC_DIR=/src/chimera

# Python path
PYTHONPATH=/opt/chimera/applications:/opt/chimera/lib/python

# Library path
LD_LIBRARY_PATH=/opt/chimera/lib

# Executable path
PATH=/opt/chimera/bin:/opt/chimera/applications/bin:$PATH
```

---

## Included Toolchain

### Compilers & Languages
- GCC 13 / G++ 13
- Clang / LLVM
- Python 3.12 with ML libraries (TensorFlow, PyTorch, scikit-learn)
- Node.js 18+ with npm/yarn
- Rust + Cargo
- Java 21 JDK
- .NET SDK 8.0
- Perl

### Build Tools
- CMake 3.28+
- Ninja Build System
- Make / Automake
- Git / Git Flow

### Libraries
- Boost (all)
- OpenSSL / Crypto++
- libsodium
- PostgreSQL Client
- SQLite 3
- X11/Mesa (graphics)

### Python Data Science Stack
- NumPy, SciPy, Pandas
- Scikit-learn, XGBoost, LightGBM
- Matplotlib, Seaborn
- TensorFlow, PyTorch, Keras
- NLTK, spaCy, Gensim
- OpenCV, Pillow

### Web Frameworks
- Flask, FastAPI, Uvicorn
- Django (optional)
- SQLAlchemy ORM

### Development Tools
- pytest, pytest-cov
- Pylint, Black, Flake8, mypy
- Sphinx documentation
- Jupyter, IPython
- gdb, Valgrind, Strace

---

## Directory Structure in Container

```
/opt/chimera/
├── bin/                          # Compiled binaries
├── lib/                          # Compiled libraries
├── include/                      # Header files
├── applications/                 # All applications
│   ├── ChimeraIIOS/
│   ├── nlp/
│   ├── BizX/
│   ├── BizXtreme/
│   ├── CPU4096/
│   ├── CPU4096Simulator/
│   ├── keygen/
│   ├── eth-key-check/
│   ├── bruteforce/
│   ├── PDFreaderPY/
│   ├── general/
│   ├── test/
│   └── portfolio/
└── scripts/
    ├── init-chimera.sh           # Initialization script
    └── docker-entrypoint.sh      # Entry point

/src/chimera/                     # Source code for all repositories
├── ChimeraIIOS/
├── nlp/
├── BizX/
└── ... (all repos)

/workspace/                       # User workspace (mounted)
```

---

## Usage Examples

### Example 1: NLP Text Processing

```bash
docker run --rm \
    -v /path/to/data:/workspace \
    chimera2os-comprehensive:latest \
    bash -c "cd /opt/chimera/applications/nlp && python3 nlp_processor.py"
```

### Example 2: CPU4096 Simulation

```bash
docker run --rm \
    chimera2os-comprehensive:latest \
    bash -c "cd /opt/chimera/applications/CPU4096 && ./simulator"
```

### Example 3: Development Environment

```bash
docker run -it --rm \
    -v $(pwd):/workspace \
    -w /workspace \
    chimera2os-comprehensive:latest \
    bash
```

### Example 4: Web Service

```bash
docker run -d \
    --name chimera-web \
    -p 8000:8000 \
    -p 5000:5000 \
    -v /data:/workspace \
    chimera2os-comprehensive:latest \
    bash -c "cd /opt/chimera/applications/BizX && npm start"
```

---

## Customization

### Extend the Image

Create a new Dockerfile:

```dockerfile
FROM chimera2os-comprehensive:latest

# Add custom applications
RUN pip3 install your-package
RUN npm install -g your-tool

# Copy custom code
COPY ./my-app /opt/chimera/applications/my-app

# Set new entrypoint
CMD ["bash"]
```

Build it:

```bash
docker build -t my-chimera-app:latest -f CustomDockerfile .
```

---

## Performance Tips

1. **Use `.dockerignore`** to exclude large files from build context
2. **Layer caching**: Order commands from least to most frequently changed
3. **Multi-stage build**: Reduces final image size by ~40%
4. **Volume mounts**: Use for frequently accessed data

---

## Troubleshooting

### Build Fails Due to Memory

Increase Docker memory allocation:
```bash
# Docker Desktop: Settings → Resources → Memory: 8GB+
# Docker on Linux: Adjust /etc/docker/daemon.json
```

### Application Not Found

Verify installation:
```bash
docker run --rm chimera2os-comprehensive:latest \
    ls -la /opt/chimera/applications/
```

### Permission Denied

Check user permissions:
```bash
docker run --rm --user chimera chimera2os-comprehensive:latest \
    ls -la /opt/chimera/
```

---

## Docker Registry Deployment

### Push to Docker Hub

```bash
docker tag chimera2os-comprehensive:latest your-username/chimera2os-comprehensive:latest
docker login
docker push your-username/chimera2os-comprehensive:latest
```

### Pull from Registry

```bash
docker pull your-username/chimera2os-comprehensive:latest
docker run -it your-username/chimera2os-comprehensive:latest
```

---

## License

All integrated repositories maintain their original licenses (primarily GPL-3.0).

---

## Support

For issues or questions:
- **Email**: amer.hwitat@proton.me
- **GitHub**: https://github.com/amerhwitat
- **Location**: Amman 11814, Jordan

---

**"Created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"**  
**Amman 11814, Jordan**  
**For support contact: amer.hwitat@proton.me**
