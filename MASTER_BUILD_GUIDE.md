# MASTER BUILD ORCHESTRATOR - BUILD ALL REPOSITORIES
## Complete Build, Release, and Docker Hub Deployment System

**Created by**: Amer Abdullah Suleiman Hwitat - عامر الحowiتات  
**Contact**: amer.hwitat@proton.me  
**GitHub**: https://github.com/amerhwitat/

---

## 📋 OVERVIEW

The Master Build Orchestrator automates:
- Building all 13 repositories
- Compiling to target languages
- Creating releases
- Building Docker images
- Pushing to Docker Hub

---

## 🚀 QUICK START

```bash
# Run full build + releases + Docker push
bash master-build.sh

# Build repositories only
bash master-build.sh --no-docker --no-release

# Docker only (images already built)
bash master-build.sh --docker-only

# Skip Docker push
bash master-build.sh --no-docker
```

---

## 📦 REPOSITORIES & LANGUAGES

| Repository | Language | Build Tool | Release Type |
|-----------|----------|-----------|--------------|
| ChimeraIIOS | Python/C++ | setup.py, CMake | wheel, binary |
| nlp | Python | setup.py | wheel |
| BizX | JavaScript | npm | tarball |
| BizXtreme | Python | setup.py | wheel |
| CPU4096 | C++ | CMake | binary |
| CPU4096Simulator | JavaScript | npm | tarball |
| keygen | Java | Maven/Gradle | JAR |
| eth-key-check | Python | setup.py | wheel |
| bruteforce | Python | setup.py | wheel |
| PDFreaderPY | Python | setup.py | wheel |
| general | Python | setup.py | wheel |
| test | Python | setup.py | wheel |

---

## 🔨 BUILD PROCESS

### Python Projects (8 repos)
```bash
python3 setup.py build
python3 setup.py sdist bdist_wheel
# Creates: dist/*.whl, dist/*.tar.gz
```

### JavaScript Projects (2 repos)
```bash
npm install
npm run build
# Creates: dist/, node_modules/
```

### C++ Projects (2 repos)
```bash
mkdir build && cd build
cmake -GNinja ..
ninja
ninja install
# Creates: build/lib, build/bin
```

### Java Projects (1 repo)
```bash
# Maven
mvn clean package

# Or Gradle
gradle build
# Creates: target/*.jar
```

---

## 🐳 DOCKER IMAGES

All images pushed to Docker Hub:

```
amerhwitat/chimera2os:latest          (3 GB)
amerhwitat/chimera2os:v1.0.0
amerhwitat/chimera2os:vmware          (3 GB, CPU fix)
amerhwitat/chimera2os:microkernel     (50 MB, minimal)
```

### Docker Hub URLs
- https://hub.docker.com/r/amerhwitat/chimera2os
- https://hub.docker.com/u/amerhwitat

---

## 📤 RELEASE ARTIFACTS

Each repo gets a `v1.0.0` release with:
- Compiled binaries
- Python wheels
- JavaScript bundles
- CHANGELOG.md
- Source archives

### GitHub Releases Created
- ChimeraIIOS/releases/tag/v1.0.0
- nlp/releases/tag/v1.0.0
- BizX/releases/tag/v1.0.0
- ... (all 13 repos)

---

## 📊 BUILD OUTPUT STRUCTURE

```
builds-PID/
├── ChimeraIIOS/
│   ├── dist/
│   ├── build/
│   └── releases/v1.0.0/
├── nlp/
│   ├── dist/
│   └── releases/v1.0.0/
├── BizX/
│   ├── dist/
│   └── releases/v1.0.0/
... (all 13 repos)
```

---

## 🔑 REQUIREMENTS

```bash
# Python build tools
pip install wheel setuptools twine

# Node.js
node --version  # v18+
npm --version

# C++ build tools
cmake --version
ninja --version
gcc --version

# Java
javac -version
mvn --version

# Docker
docker --version
```

---

## 🔧 CONFIGURATION

Edit `master-build.sh` to customize:

```bash
GITHUB_USER="amerhwitat"           # GitHub username
DOCKER_REGISTRY="docker.io"        # Docker registry
DOCKER_USERNAME="amerhwitat"       # Docker Hub username
VERSION="1.0.0"                    # Release version
RELEASE_DATE=$(date +%Y-%m-%d)     # Release date
```

---

## 📝 RELEASE STRUCTURE

Each repo gets:

```
releases/v1.0.0/
├── CHANGELOG.md
├── *.whl                (Python wheels)
├── *.tar.gz             (Source archives)
├── *.jar                (Java JARs)
├── dist/                (JavaScript builds)
└── bin/                 (C++ binaries)
```

---

## 🚀 FULL BUILD WORKFLOW

```bash
# 1. Clone all repos
for repo in ChimeraIIOS nlp BizX BizXtreme CPU4096 CPU4096Simulator keygen eth-key-check bruteforce PDFreaderPY general test; do
  git clone https://github.com/amerhwitat/$repo.git
done

# 2. Build each repo (handled by master-build.sh)
bash master-build.sh --no-docker --no-release

# 3. Create releases (handled by master-build.sh)
bash master-build.sh --no-docker

# 4. Build Docker images (handled by master-build.sh)
bash master-build.sh

# 5. Push to GitHub (manual - use gh or git push)
for repo in */; do
  cd $repo
  git add -A
  git commit -m "Release v1.0.0"
  git push origin main
  cd ..
done
```

---

## 📦 PUSH TO DOCKER HUB

```bash
# Login (if not already logged in)
docker login -u amerhwitat

# Images automatically pushed during master-build.sh
# Or manually:
docker push amerhwitat/chimera2os:latest
docker push amerhwitat/chimera2os:vmware
docker push amerhwitat/chimera2os:microkernel
```

---

## 🔄 CI/CD INTEGRATION

### GitHub Actions Example

```yaml
name: Build & Release

on: [push, workflow_dispatch]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Master Build
        run: bash master-build.sh
      - name: Push to Docker Hub
        run: |
          docker login -u ${{ secrets.DOCKER_USER }} -p ${{ secrets.DOCKER_TOKEN }}
          docker push ${{ secrets.DOCKER_USER }}/chimera2os:*
```

---

## 📋 BUILDING SPECIFIC REPOS

```bash
# Build and push single repo
cd builds-xxx/ChimeraIIOS
python3 setup.py sdist bdist_wheel
cd ../..

# Push to PyPI (Python)
pip install twine
twine upload builds-xxx/ChimeraIIOS/dist/*

# Publish NPM (JavaScript)
npm publish builds-xxx/BizX

# Deploy Maven (Java)
mvn deploy -f builds-xxx/keygen/pom.xml
```

---

## 🐛 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Build fails | Check language tools installed |
| Docker push fails | Run `docker login` first |
| Missing dependencies | Check `requirements.txt`, `package.json` |
| Release directory not created | Ensure repos cloned successfully |

---

## ✅ VERIFICATION

After build:

```bash
# Check Docker images
docker images amerhwitat/chimera2os

# Check Docker Hub
curl https://hub.docker.com/v2/repositories/amerhwitat/chimera2os/tags

# Check GitHub releases
curl https://api.github.com/repos/amerhwitat/ChimeraIIOS/releases

# Check build artifacts
ls builds-xxx/*/dist/
ls builds-xxx/*/releases/v1.0.0/
```

---

## 📊 BUILD TIME ESTIMATES

| Repo | Language | Time |
|------|----------|------|
| ChimeraIIOS | Python/C++ | 15-20 min |
| nlp | Python | 5 min |
| BizX | JavaScript | 5 min |
| BizXtreme | Python | 5 min |
| CPU4096 | C++ | 10-15 min |
| CPU4096Simulator | JavaScript | 5 min |
| keygen | Java | 10-15 min |
| eth-key-check | Python | 3 min |
| bruteforce | Python | 3 min |
| PDFreaderPY | Python | 3 min |
| general | Python | 3 min |
| test | Python | 3 min |
| **Docker images** | - | **30-45 min** |
| **TOTAL** | - | **~2-3 hours** |

---

## 🔗 RESOURCES

- Master Build Script: `master-build.sh`
- Docker Hub: https://hub.docker.com/u/amerhwitat
- GitHub: https://github.com/amerhwitat
- Release Docs: EDITIONS_AND_TOOLS_GUIDE.md

---

## 👤 AUTHOR

**Amer Abdullah Suleiman Hwitat - عامر الحowiتات**

- 📧 Email: amer.hwitat@proton.me
- 📍 Location: Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 🐳 Docker Hub: https://hub.docker.com/u/amerhwitat

---

**"created by Amer Abdullah Suleiman Hwitat - عامر الحowiتات"**  
**Amman 11814, Jordan | amer.hwitat@proton.me**

---

## 🚀 READY TO BUILD!

Everything is set up and ready. Run:

```bash
bash master-build.sh
```

This will:
1. Clone all 13 repositories
2. Build each to its target language
3. Create releases with artifacts
4. Build Docker images
5. Push to Docker Hub

**Total time**: ~2-3 hours  
**Docker Hub**: amerhwitat/chimera2os
