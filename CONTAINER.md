# Containerized development/build environment

Build and run the isolated build environment:

```bash
docker compose build
docker compose up
```

The container is for reproducible kernel/toolchain builds and emulator-side development. It does not replace booting Chimera II OS on real or virtual hardware.

Interactive shell:

```bash
docker compose run --rm chimera-build bash
```

The entrypoint configures a CMake build when a CMake project is present. Build artifacts use the persistent `chimera-build-cache` volume.
