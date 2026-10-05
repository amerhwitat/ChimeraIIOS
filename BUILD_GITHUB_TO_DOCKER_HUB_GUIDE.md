# Build Docker Hub from GitHub Repositories - Complete Guide

**Auto-discover, build, and push all your GitHub repositories as Docker images**

## 🎯 What This System Does

✅ **Discovers** all repositories in your GitHub account
✅ **Detects** application types (Web, Mobile, API, Library)
✅ **Generates** Dockerfiles automatically
✅ **Builds** Docker images for all repos
✅ **Pushes** all images to Docker Hub
✅ **Catalogs** complete registry with documentation

---

## 🚀 Quick Start (Choose Your OS)

### Windows PowerShell
```powershell
cd C:\tmp\ChimeraIIOS
.\build-all-github-repos.ps1
```

### Linux/WSL2 Bash
```bash
cd ~/ChimeraIIOS
bash build-all-github-repos.sh amerhwitat amerhwitat
```

### With GitHub Token (Optional - Higher API Rate Limit)
```bash
bash build-all-github-repos.sh amerhwitat amerhwitat ghp_xxxxxxxxxxxxx
```

---

## 📊 Features

### 🔍 Automatic Repository Discovery
- Discovers ALL repositories in your GitHub account
- Handles pagination (up to 100+ repos)
- Shows summary of all discovered repos

### 🔎 Smart Application Detection
Automatically detects:

**Web Applications**:
- Next.js
- React
- Vue.js
- Nuxt
- Django
- Static HTML/CSS/JS

**Mobile Applications**:
- React Native
- Flutter

**APIs & Services**:
- Express.js
- Flask
- FastAPI
- Go services

**Languages**:
- Node.js
- Python
- Go
- Java (Spring Boot)

### 📝 Automatic Dockerfile Generation
Creates optimized Dockerfiles for each app type:

**Next.js**:
```dockerfile
FROM node:18-alpine AS builder
# Build optimization with multi-stage build
```

**React**:
```dockerfile
# Multi-stage: build with Node, serve with Nginx
```

**Flask/FastAPI**:
```dockerfile
FROM python:3.11-slim
# Python API image
```

**React Native**:
```dockerfile
FROM node:18-alpine
# React Native development server
```

**Go**:
```dockerfile
# Multi-stage: compile with Go, run lightweight binary
```

### 🐳 Docker Image Building
- Builds all images with proper labels
- Tags with: latest, v1.0.0, stable
- One image per repository
- Skips if Dockerfile already exists

### 📤 Docker Hub Publishing
- Automated login to Docker Hub
- Pushes all image versions
- Verifies uploads
- Rate limiting for stability

### 📚 Registry Documentation
- Generates complete registry index
- Organizes by application type
- Creates clickable links
- Markdown formatted

---

## 📁 Output Structure

After execution:

```
docker-hub-build/
├── repos/                        # All cloned repositories
│   ├── repo-name-1/
│   ├── repo-name-2/
│   └── ... (all repos)
├── output/                       # Build artifacts
├── discovered_repos.txt          # List of repos
├── built_images.txt              # Successfully built images
├── build-all-repos.log           # Bash build log
├── build-all-repos-ps1.log       # PowerShell log
├── DOCKER_HUB_BUILD_REPORT.txt  # Build report
└── DOCKER_HUB_REGISTRY_INDEX.md # Registry documentation
```

---

## 🐳 Docker Hub Result

After execution, all your repositories are on Docker Hub:

```
https://hub.docker.com/u/amerhwitat

amerhwitat/chimeraiios:latest|v1.0.0|stable
amerhwitat/nlp:latest|v1.0.0|stable
amerhwitat/bizx:latest|v1.0.0|stable
... (all repositories)
```

---

## 🎓 How Application Detection Works

### Node.js Detection
```javascript
// Checks for:
- package.json (Node.js project)
- "next" → Next.js web app
- "react" → React web app
- "express" → Express.js API
- "vue" → Vue.js web app
- "nuxt" → Nuxt web app
```

### Python Detection
```python
# Checks for:
- requirements.txt / pyproject.toml / setup.py
- "flask" import → Flask API
- "django" import → Django web app
- "fastapi" import → FastAPI API
```

### Mobile Detection
```json
// React Native:
{
  "app.json": true,
  "package.json": true
}

// Flutter:
{
  "pubspec.yaml": true
}
```

### Go Detection
```bash
# Checks for:
- go.mod (Go module)
- main.go (Go application)
```

---

## ⏱️ Execution Times

| Step | Time |
|------|------|
| Discover repos | 1-2 min |
| Clone repos | 5-15 min |
| Build images | 30-120 min |
| Push to Hub | 15-45 min |
| Generate docs | 1 min |
| **TOTAL** | **1-3 hours** |

*Depends on number of repos and image sizes*

---

## 📋 Application Type Categories

### Web Applications (`web-*`)
- `web-nextjs` - Next.js with Node.js
- `web-react` - React with Nginx
- `web-vue` - Vue.js with Nginx
- `web-nuxt` - Nuxt with Node.js
- `web-django` - Django with Gunicorn
- `web-static` - Static HTML/CSS/JS

### Mobile Applications (`mobile-*`)
- `mobile-react-native` - React Native dev server
- `mobile-flutter` - Flutter web/desktop

### APIs & Services (`api-*`)
- `api-express` - Express.js REST API
- `api-flask` - Flask Python API
- `api-fastapi` - FastAPI Python API

### Applications (`app-*`)
- `app-nodejs` - Generic Node.js
- `app-python` - Generic Python
- `app-go` - Go application
- `app-java` - Java application
- `app-generic` - Unknown type
- `app-pre-dockerized` - Already has Dockerfile

---

## 🔧 Dockerfile Examples

### Next.js
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]
```

### React with Nginx
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### FastAPI
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### Go
```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o app .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/app .
EXPOSE 8080
CMD ["./app"]
```

---

## 💻 Usage Examples

### Example 1: Build All Repos (Default)
```bash
bash build-all-github-repos.sh
# Uses: amerhwitat / amerhwitat
```

### Example 2: Different GitHub User
```bash
bash build-all-github-repos.sh different-user amerhwitat
```

### Example 3: Different Docker Hub User
```bash
bash build-all-github-repos.sh amerhwitat different-docker-user
```

### Example 4: With GitHub Token (Higher Rate Limit)
```bash
bash build-all-github-repos.sh amerhwitat amerhwitat ghp_xxxxx
```

### Example 5: Windows with Custom Users
```powershell
.\build-all-github-repos.ps1 -GitHubUser amerhwitat -DockerUser amerhwitat
```

---

## ✅ Verification After Build

### 1. Check Docker Hub
```bash
# View all images
https://hub.docker.com/u/amerhwitat

# Pull a specific image
docker pull amerhwitat/chimeraiios:latest
```

### 2. Run a Container
```bash
# Test a built image
docker run -it amerhwitat/nlp:latest bash

# Run web app
docker run -p 3000:3000 amerhwitat/web-app:latest

# Run API
docker run -p 5000:5000 amerhwitat/api-service:latest
```

### 3. View Registry Index
```bash
cat docker-hub-build/DOCKER_HUB_REGISTRY_INDEX.md
```

### 4. Check Build Log
```bash
cat docker-hub-build/build-all-repos.log

# Or PowerShell log:
cat docker-hub-build/build-all-repos-ps1.log
```

---

## 🛠️ Troubleshooting

### Issue: "Docker not found"
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
bash get-docker.sh
```

### Issue: "Git not found"
```bash
# Install Git
sudo apt-get install -y git
```

### Issue: Docker Hub login fails
```bash
# Manual login
docker login

# Enter username and password when prompted
```

### Issue: "Repository not found" errors
- Verify GitHub user has public repositories
- Check internet connection
- Verify GitHub credentials

### Issue: Image build failures
- Check individual Dockerfile generated in repo
- Verify repo has required files (package.json, requirements.txt, etc.)
- Check Docker disk space: `docker system df`

### Issue: Out of disk space
```bash
# Clean up
docker system prune -a
docker volume prune
```

---

## 📊 Expected Output

```
╔════════════════════════════════════════════════════════════════╗
║     GITHUB → DOCKER HUB - COMPLETE REPOSITORY BUILDER         ║
╚════════════════════════════════════════════════════════════════╝

[INFO] Build system initialized
[SUCCESS] Docker: Docker version 20.10.x
[SUCCESS] Git: git version 2.x.x

[INFO] Discovering all GitHub repositories...
[SUCCESS] Discovered 45 repositories

[INFO] Cloning all repositories...
[SUCCESS] Cloned: repo-1
[SUCCESS] Cloned: repo-2
... (45 total)

[BUILD] Building Docker images...
[BUILD] [1/45] Building: repo-1
[SUCCESS] Built: repo-1

... (continuing for all repos)

[BUILD] Pushing images to Docker Hub...
[BUILD] [1/135] Pushing: amerhwitat/repo-1:latest
[SUCCESS] Pushed all images

ALL REPOSITORIES BUILT AND PUSHED!
Docker Hub: https://hub.docker.com/u/amerhwitat
```

---

## 📝 Generated Files

### build-all-repos.log
Real-time build log with detailed progress

### DOCKER_HUB_BUILD_REPORT.txt
Summary report with:
- All discovered repositories
- Build statistics
- Successfully built images
- Docker Hub URLs
- Verification steps

### DOCKER_HUB_REGISTRY_INDEX.md
Complete catalog with:
- Web applications list
- Mobile applications list
- APIs & services list
- Full image table
- Clickable Docker Hub links
- Pull commands

---

## 🚀 Next Steps After Build

1. **View your registry**:
   ```bash
   open https://hub.docker.com/u/amerhwitat
   ```

2. **Pull images**:
   ```bash
   docker pull amerhwitat/chimeraiios:latest
   docker pull amerhwitat/nlp:v1.0.0
   ```

3. **Run applications**:
   ```bash
   # Web app
   docker run -p 3000:3000 amerhwitat/web-app:latest
   
   # API service
   docker run -p 5000:5000 amerhwitat/api:latest
   
   # Mobile dev
   docker run -p 8081:8081 amerhwitat/mobile-app:latest
   ```

4. **Deploy to production**:
   - Use Docker Compose
   - Deploy to Kubernetes
   - Deploy to Docker Swarm
   - Use managed services (AWS, Azure, GCP)

---

## 📞 Support & Contact

**Creator**: Amer Abdullah Suleiman Hwitat - عامر الحويطات

- **Email**: amer.hwitat@proton.me
- **GitHub**: https://github.com/amerhwitat
- **Docker Hub**: https://hub.docker.com/u/amerhwitat
- **Location**: Amman 11814, Jordan

---

## 🎉 You're Ready!

Everything is set up to automatically build all your GitHub repositories as Docker images and push them to Docker Hub.

**Just run the command for your OS and watch as all your applications get containerized!**
