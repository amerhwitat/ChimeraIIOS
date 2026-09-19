# Chimera II OS Docker builder

The repository Docker setup provides two related images from the same source tree:

- **builder** — complete Ubuntu-based development/build environment plus a configured CMake/Ninja build of the host-side Koronos and Chimera server targets.
- **runtime** — hosted Aurora GUI image containing the source tree and the compiled `chimera_kernel` and `chimera_server` binaries.

## GitHub Actions

`.github/workflows/docker-build.yml` uses Docker Buildx with the `docker-container` driver. Buildx creates an isolated BuildKit builder container for the workflow, so the old placeholder Docker Build Cloud endpoint is no longer required. Docker documents this driver for isolated and multi-platform builds. citeturn0search1turn0search4

The workflow builds `linux/amd64` and `linux/arm64` and publishes to GitHub Container Registry on pushes to `main` and version tags. Pull requests build without publishing. The images receive BuildKit provenance and SBOM metadata.

## Images

- `ghcr.io/amerhwitat/chimeraiios-builder:latest`
- `ghcr.io/amerhwitat/chimeraiios:latest`

The workflow also creates SHA and version-reference tags.

GitHub's container publishing guidance supports using `GITHUB_TOKEN` for GHCR authentication and Buildx for image builds. citeturn0search2

## Local builds

```bash
docker buildx build --target builder -t chimeraiios-builder:local .
```

```bash
docker buildx build --target runtime -t chimeraiios:local .
```

```bash
docker run --rm -p 8000:8000 --privileged chimeraiios:local
```

The source tree is not deleted or replaced by the Docker build. The builder compiles from the repository checkout and the runtime copies the resulting binaries into a separate runtime stage.