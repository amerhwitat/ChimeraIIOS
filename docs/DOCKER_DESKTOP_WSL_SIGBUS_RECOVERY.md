# Docker Desktop / WSL SIGBUS and I/O recovery

The comprehensive ISO build now performs a Docker storage preflight before the expensive build and avoids automatically disabling the cache or pruning all BuildKit data.

The reported failure:

- SIGBUS during image unpacking
- errno 5 / Input/output error
- read-only filesystem
- failure while unpacking an image layer

is a Docker Desktop/WSL storage/backend failure class, not an Ubuntu package installation problem.

Docker documents that Docker Desktop's WSL2 engine stores its data under the Docker WSL data location by default and that WSL2 resource allocation and disk placement can be changed in Docker Desktop settings. Docker's Troubleshoot menu also provides restart, clean-up, diagnostics and factory-reset operations. citeturn0search0turn0search1

## Safe recovery order

1. Stop/quit Docker Desktop.
2. From an elevated PowerShell window run:

   `wsl --shutdown`

3. Start Docker Desktop again.
4. Confirm Docker is healthy:

   `docker info`

5. Confirm the Docker storage can write:

   `docker run --rm ubuntu:24.04 sh -c 'dd if=/dev/zero of=/tmp/test.bin bs=1M count=8 status=none && test -s /tmp/test.bin'`

6. Retry:

   `sudo ./build-chimera-iso.sh`

   Root is only needed by the later ISO/host operations; the Docker build itself no longer requires the script to start as root.

## Build controls

The script defaults to cache reuse and does not force a fresh base-image pull.

Optional controls:

- `CHIMERA_DOCKER_PULL=1` — force `--pull`.
- `CHIMERA_DOCKER_NO_CACHE=1` — force `--no-cache`.
- `CHIMERA_PRUNE=1` — explicitly prune BuildKit cache.
- `CHIMERA_DOCKER_RETRIES=2` — configured retry count.

Do not use `apt --fix-missing` or `apt-get -f install` as a response to Docker SIGBUS/errno 5. The comprehensive Dockerfile no longer invokes dependency repair in its optional-package failure path.

## Docker Desktop version

Docker Desktop 4.92.0 was released on 21 September 2026 and includes current Docker Desktop fixes. If the installed Docker Desktop is substantially older, update it before diagnosing a persistent backend failure. citeturn0search2

## Important distinction

If the small Docker write test fails, rebuilding Chimera's source code will not repair the backend. Repair Docker Desktop/WSL storage first.

If the write test succeeds but the comprehensive build still fails during image unpacking, capture Docker diagnostics using Docker Desktop's Troubleshoot/diagnostics facilities before repeatedly rebuilding. citeturn0search1
