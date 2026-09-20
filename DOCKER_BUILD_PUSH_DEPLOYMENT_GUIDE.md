# Chimera II OS - Docker Build, Push & Deployment Guide

**Complete guide for building Docker images, pushing to Docker Hub, and deploying**

## 🚀 Quick Start (Build & Push)

```powershell
# 1. Windows PowerShell (Administrator)
cd C:\tmp\ChimeraIIOS

# 2. Start Docker build and push
.\docker-build-push-wsl2.ps1

# 3. Wait 1-2 hours for build and push to complete...
```

## 📦 What Gets Built

**39 Docker Images (13 repositories × 3 tags each):**

```
amerhwitat/chimeraiios:latest, v1.0.0, stable
amerhwitat/nlp:latest, v1.0.0, stable
amerhwitat/bizx:latest, v1.0.0, stable
amerhwitat/bizxtreme:latest, v1.0.0, stable
amerhwitat/cpu4096:latest, v1.0.0, stable
amerhwitat/cpu4096simulator:latest, v1.0.0, stable
amerhwitat/keygen:latest, v1.0.0, stable
amerhwitat/eth-key-check:latest, v1.0.0, stable
amerhwitat/bruteforce:latest, v1.0.0, stable
amerhwitat/pdfreadery:latest, v1.0.0, stable
amerhwitat/general:latest, v1.0.0, stable
amerhwitat/test:latest, v1.0.0, stable
amerhwitat/amerhwitat.github.io:latest, v1.0.0, stable
```

## ⏱️ Build Timeline

| Phase | Duration |
|-------|----------|
| Initialize | 1 min |
| Clone/update repos | 5-10 min |
| Build 13 images | 30-60 min |
| Login to Docker Hub | 1 min |
| Push 39 images | 20-40 min |
| Verify | 5 min |
| Report | 2 min |
| **TOTAL** | **1-2 hours** |

## ✅ Prerequisites

**System:**
- Windows 10/11 with WSL2
- Ubuntu 20.04+ on WSL2
- Docker installed
- 50GB+ free disk
- 16GB+ RAM

**Verify:**
```powershell
wsl --version
wsl docker --version
wsl df -h /
wsl git --version
```

## 🎬 Build Process (7 Steps)

### Step 1: Initialize Build Environment (1 min)
- Create build directories
- Check Git, Docker, prerequisites
- Initialize logging

### Step 2: Clone/Update Repositories (5-10 min)
- Clone 13 repositories from GitHub
- Update existing repositories
- Organize in ~/docker-build-chimera/repos/

### Step 3: Build Docker Images (30-60 min)
- Build image for each repository
- Create Dockerfile if missing
- Tag: latest, v1.0.0, stable

### Step 4: Login to Docker Hub (1 min)
- Authenticate with Docker Hub
- Provide credentials or PAT

### Step 5: Push Docker Images (20-40 min)
- Push all 39 images
- 3 tags per repository
- Rate limiting delays (2s between pushes)

### Step 6: Verify Pushed Images (5 min)
- Verify images on Docker Hub
- Check via Docker Hub API
- List all uploaded images

### Step 7: Generate Report (2 min)
- Create detailed build report
- Docker Hub links
- Deployment examples

## 🐳 Build Script (`docker-build-push.sh`)

**Main script features:**

```bash
# Clone or update repositories
# Build Docker images (creates Dockerfile if missing)
# Login to Docker Hub with credentials
# Push all images with multiple tags
# Verify uploads
# Generate comprehensive report

bash ~/docker-build-chimera/docker-build-push.sh [github-user] [docker-user]
```

**Default users:**
- GitHub: amerhwitat
- Docker Hub: amerhwitat

## 🖥️ Windows Wrapper (`docker-build-push-wsl2.ps1`)

**PowerShell wrapper features:**

- WSL2 integration
- Pre-flight checks
- Build progress monitoring
- Automatic results display
- Configuration options

**Usage:**
```powershell
.\docker-build-push-wsl2.ps1 -GitHubUser amerhwitat -DockerUser amerhwitat
```

## 🚀 Deployment Options

### Option 1: Docker (Single Host)

**Pull and run:**
```bash
# Pull latest image
docker pull amerhwitat/chimeraiios:latest

# Run container
docker run -it amerhwitat/chimeraiios:latest bash

# Run with volumes
docker run -it -v $(pwd):/workspace amerhwitat/chimeraiios:latest bash

# Run in background
docker run -d amerhwitat/chimeraiios:latest
```

### Option 2: Docker Compose (Multi-Service)

**Deploy full stack:**
```bash
# Start all services
docker-compose -f docker-compose-full.yml up -d

# View logs
docker-compose -f docker-compose-full.yml logs -f

# Check status
docker-compose -f docker-compose-full.yml ps

# Stop all services
docker-compose -f docker-compose-full.yml down
```

**What's included:**
- 13 Chimera services
- PostgreSQL database
- Redis cache
- RabbitMQ message queue
- Nginx gateway
- Networking and volumes

### Option 3: Kubernetes (Multi-Node)

**Deploy to Kubernetes cluster:**
```bash
# Apply manifests
kubectl apply -f kubernetes-deployment.yaml

# Check deployment
kubectl get deployments -n chimera-system
kubectl get pods -n chimera-system
kubectl get svc -n chimera-system

# View logs
kubectl logs -n chimera-system deployment/chimera-core

# Scale deployment
kubectl scale deployment chimera-core -n chimera-system --replicas=5

# Delete deployment
kubectl delete namespace chimera-system
```

**What's included:**
- Namespace: chimera-system
- Deployments: chimera-core, nlp-service, business-service
- StatefulSets: PostgreSQL, Redis
- Services: LoadBalancer, ClusterIP
- HorizontalPodAutoscaler
- NetworkPolicy
- Ingress
- ConfigMaps and Secrets

## 📁 Output Files

```
~/docker-build-chimera/
├── repos/
│   ├── ChimeraIIOS/
│   ├── nlp/
│   ├── BizX/
│   └── ... (13 total)
├── docker-build.log
├── docker-push.log
└── DOCKER_BUILD_REPORT.txt
```

**Windows access:**
```
\\wsl$\Ubuntu\home\<user>\docker-build-chimera\
```

## 📊 Docker Hub Registry

**All images:** https://hub.docker.com/u/amerhwitat

**Pull examples:**
```bash
docker pull amerhwitat/chimeraiios:latest
docker pull amerhwitat/nlp:v1.0.0
docker pull amerhwitat/bizx:stable
```

## 🎯 Docker Compose File (`docker-compose-full.yml`)

**13 services included:**
1. chimera-core - Main OS service
2. nlp-service - NLP/AI service
3. business-service - BizX service
4. enterprise-service - BizXtreme service
5. cpu-simulator - CPU4096 service
6. cpu-simulator-web - CPU simulator web
7. crypto-service - keygen service
8. ethereum-service - Ethereum service
9. security-service - bruteforce service
10. pdf-service - PDF service
11. utils-service - general utilities
12. test-service - testing service
13. portfolio-service - portfolio service

**Plus infrastructure:**
- PostgreSQL database
- Redis cache
- RabbitMQ message queue
- Nginx gateway

**Usage:**
```bash
# Start all
docker-compose -f docker-compose-full.yml up -d

# Specific service
docker-compose -f docker-compose-full.yml up -d chimera-core

# View logs
docker-compose -f docker-compose-full.yml logs -f chimera-core

# Restart service
docker-compose -f docker-compose-full.yml restart chimera-core

# Stop all
docker-compose -f docker-compose-full.yml down

# Remove volumes
docker-compose -f docker-compose-full.yml down -v
```

## 🔒 Kubernetes Deployment (`kubernetes-deployment.yaml`)

**Components:**
- Namespace: chimera-system
- Deployments: Core, NLP, Business (with replicas)
- StatefulSets: PostgreSQL, Redis (persistent storage)
- Services: LoadBalancer for external, ClusterIP internal
- ConfigMaps: Shared configuration
- Secrets: Sensitive data
- HorizontalPodAutoscaler: Auto-scaling
- NetworkPolicy: Security
- Ingress: External routing

**Deploy:**
```bash
kubectl apply -f kubernetes-deployment.yaml

# Verify
kubectl get all -n chimera-system

# Check pods
kubectl get pods -n chimera-system

# View services
kubectl get svc -n chimera-system

# Scale
kubectl scale deployment chimera-core --replicas=5 -n chimera-system

# Logs
kubectl logs deployment/chimera-core -n chimera-system

# Delete
kubectl delete namespace chimera-system
```

## 📝 Example: Build, Push & Deploy

### Step 1: Build & Push Images (1-2 hours)
```powershell
cd C:\tmp\ChimeraIIOS
.\docker-build-push-wsl2.ps1
```

### Step 2: Verify Images on Docker Hub
```bash
docker search amerhwitat
docker pull amerhwitat/chimeraiios:latest
```

### Step 3: Deploy with Docker Compose
```bash
docker-compose -f docker-compose-full.yml up -d
docker-compose ps
docker-compose logs -f
```

### Step 4: Access Services
```
chimera-core:     http://localhost:8000
business:         http://localhost:3000
nlp:              http://localhost:8002
postgres:         localhost:5432
redis:            localhost:6379
```

### Step 5: Deploy to Kubernetes (Optional)
```bash
kubectl apply -f kubernetes-deployment.yaml
kubectl get svc -n chimera-system
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Build takes too long** | Normal (1-2 hours), don't interrupt |
| **Docker login fails** | Use PAT: https://hub.docker.com/settings/security |
| **Out of disk space** | Need 50GB+, clean: `docker system prune -a` |
| **Push rate limited** | Script has 2s delay, just wait |
| **Image not found** | Verify: `docker images` \| grep amerhwitat |
| **Kubernetes pod pending** | Check: `kubectl describe pod <pod-name>` |
| **Compose service fails** | Check logs: `docker-compose logs <service>` |

## 📞 Contact

**Author:** Amer Abdullah Suleiman Hwitat - عامر الحويطات

- 📧 Email: amer.hwitat@proton.me
- 📍 Amman 11814, Jordan
- 🔗 GitHub: https://github.com/amerhwitat
- 🐳 Docker Hub: https://hub.docker.com/u/amerhwitat
- 📦 Repository: https://github.com/amerhwitat/ChimeraIIOS

## 🏁 Next Steps

1. **Build & Push (1-2 hours)**
   ```powershell
   .\docker-build-push-wsl2.ps1
   ```

2. **Verify Images**
   ```bash
   docker pull amerhwitat/chimeraiios:latest
   docker run -it amerhwitat/chimeraiios:latest
   ```

3. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose-full.yml up -d
   ```

4. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f kubernetes-deployment.yaml
   ```

---

*Status: ✅ READY FOR PRODUCTION*

*All scripts pushed to GitHub: https://github.com/amerhwitat/ChimeraIIOS*
