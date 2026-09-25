# Chimera II OS Command Architecture

## Compatibility catalog

Chimera II OS includes a Linux/Bash command compatibility catalog based on the public SS64 A-Z Linux command-line index. The catalog records command names and categories, not copied SS64 prose.

Run:

```bash
chimera commands
chimera search network
chimera help ls
chimera which bash
```

The catalog is complemented by GNU Coreutils documentation for the core file, process, text, and filesystem utilities.

## Native Chimera commands

The native control-plane namespace is intentionally distinct from ordinary Linux utilities:

- `chimera` — command catalog and dispatcher
- `chmctl` / `chimeractl` — system control
- `koronosctl` — Koronos kernel control
- `spitfirectl` — Spit Fire boot control
- `jasperctl` — Jasper boot-manager control
- `spotnikctl` — Spotnik network control
- `nucleusctl` — Nucleus database control
- `hivectl` — Hive registry/environment control
- `korectl` — Kore service-manager control
- `aegisctl` — Aegis security control
- `auroractl` — Aurora desktop/session control
- `chimera-user`, `chimera-group` — identity management interfaces
- `chimera-service`, `chimera-network`, `chimera-storage` — OS administration interfaces
- `chimera-nbit`, `chimera-neural`, `chimera-biometric` — Chimera runtime subsystems
- `chimera-db`, `chimera-registry`, `chimera-security` — platform services
- `chimera-kernel`, `chimera-elf`, `chimera-asm`, `chimera-risc`, `chimera-cisc`, `chimera-hybrid` — native execution/toolchain interfaces
- `chimera-p2p`, `chimera-sync` — distributed-system interfaces

The catalog does not claim that every native namespace command already has a complete standalone implementation. The implemented `chimera` front-end provides discovery and explicit PATH dispatch; subsystem commands are registered as native API/CLI names as their implementations are added.

## Resumable ISO builds

`build-chimera-iso.sh --resume` reads `build/.chimera-build-state` and skips completed stages. A failure while mastering the ISO therefore resumes at ISO mastering rather than rebuilding Docker, rootfs, boot artifacts, and SquashFS.

Use `--clean-state` to discard the checkpoint and start a fresh build.

Example after an ISO mastering failure:

```bash
sudo bash ./build-chimera-iso.sh --resume
```

For a large external output filesystem:

```bash
sudo CHIMERA_ISO_OUTPUT_DIR=/mnt/d/chimera-output \
     bash ./build-chimera-iso.sh --resume
```

## Sources

- SS64 Linux command-line index: https://ss64.com/bash/
- GNU Coreutils manual: https://www.gnu.org/software/coreutils/manual/

These sources are used as documentation/compatibility references; Chimera II OS keeps its own command catalog and implementation boundary.
