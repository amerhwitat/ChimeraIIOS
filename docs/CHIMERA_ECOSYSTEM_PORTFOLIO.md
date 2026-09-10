# Amer Hwitat — Public Repository Portfolio & Chimera II OS Ecosystem

**Canonical source:** [amerhwitat/ChimeraIIOS](https://github.com/amerhwitat/ChimeraIIOS)

This document is the public portfolio map for Amer Hwitat's GitHub repositories. It separates the canonical Chimera II OS implementation from supporting CPU, web, mobile, research, crypto, document-processing and experimental repositories.

## Repository map

| Repository | Purpose and functionality | Role in the ecosystem |
|---|---|---|
| [ChimeraIIOS](https://github.com/amerhwitat/ChimeraIIOS) | Native/source-of-record Chimera II OS research platform: Koronos kernel architecture, Spit Fire/Jasper boot, RegisterN, C8192/R8192 ISA, VFS/data fabric, Spotnik networking, Aurora desktop, Mobile Edition, toolchain/IDE, emulation, CI and provenance documentation. | **Canonical OS hub** |
| [CPU4096](https://github.com/amerhwitat/CPU4096) | Early 4096-bit fixed-width processor/register research, arithmetic and logic simulation concepts, wide-register architecture, memory/storage and concurrency ideas. | CPU architecture lineage |
| [CPU4096Simulator](https://github.com/amerhwitat/CPU4096Simulator) | Node.js/JavaScript web runtime for configurable 4096/8192-bit arithmetic, 1024-register CPU model, ISA catalogue/codec, memory/VM, kernel/runtime, networking, 128D research, robotics, assembler/compiler and browser dashboard. | **Web Edition / simulator** |
| [general](https://github.com/amerhwitat/general) | General/mobile integration tree containing Aurora integration metadata, installer integration, mobile runtime/package boundaries, Linux research and supporting Chimera integration material. | Mobile/integration layer |
| [test](https://github.com/amerhwitat/test) | Python host-side consolidation, integration and conformance target with boot/service orchestration, 8192-bit model, ISA codec/catalogue, memory/VM, kernel/network/brain/robotics models and web bridge. | Python integration/test layer |
| [keygen](https://github.com/amerhwitat/keygen) | Java 25/Koronos 128D semantic track with 8192-bit representation, concurrency, trusted-node federation, Linux/Windows/Unix/macOS compatibility catalogues, desktop/service integration and key-generation/security primitives. | Java implementation track |
| [eth-key-check](https://github.com/amerhwitat/eth-key-check) | Safe Ethereum private-key-to-address derivation and address/checksum verification for keys already possessed by the operator, with EIP-55/BIP-32 interoperability references and tests. | Crypto interoperability |
| [bruteforce](https://github.com/amerhwitat/bruteforce) | Historical cryptocurrency experimentation retained as a safe research/reference repository for deterministic key-to-address demonstrations, validation, test vectors and cryptographic benchmarking. | Crypto research/reference |
| [nlp](https://github.com/amerhwitat/nlp) | NLP/research workspace containing Python research utilities, datasets/text corpora, Aurora integration metadata, performance/concurrency material and historical Bitcoin-related research artifacts. | NLP/data research |
| [PDFreaderPY](https://github.com/amerhwitat/PDFreaderPY) | Python PDF reading/extraction utility and research integration surface, with PyMuPDF/PIL-oriented processing and Chimera/Aurora integration metadata. | Document-processing research |
| [BizX](https://github.com/amerhwitat/BizX) | Small experimental/integration repository containing Aurora UI, Chimera installer/UI integration and shared research metadata. | Experimental integration |
| [BizXtreme](https://github.com/amerhwitat/BizXtreme) | WebGL/test application repository used for browser graphics and UI experimentation. | Web/graphics experiment |
| [amerhwitat.github.io](https://github.com/amerhwitat/amerhwitat.github.io) | Public website/source for Chimera II discovery pages, native ASM/C/C++ research surfaces, documentation and portfolio navigation. | **Public web portal** |

### Private repository

`VanG` is currently private. It is intentionally excluded from public publication and is not described as a public mirror. Its visibility remains under the account owner's control.

## Chimera II architecture at a glance

```text
                         CHIMERA II OS
                              |
       +----------------------+----------------------+
       |                      |                      |
  MACHINE PLANE         COGNITIVE PLANE         WORLD PLANE
  R8192 / C8192         128D / vectors          Network / GPU
  RegisterN             Knowledge/runtime       Files / sensors
  ISA + emulator        Perception models       Storage / UI
       |                      |                      |
       +----------------------+----------------------+
                              |
                         KORONOS KERNEL
                              |
          ISA / MM / SCHED / IRQ / VFS / IPC / NET
                              |
                    AURORA / GPU / CEF / WEB
                              |
                    MOBILE / DESKTOP / TOOLS
```

## Public research surfaces

- **Native OS:** [ChimeraIIOS](https://github.com/amerhwitat/ChimeraIIOS)
- **CPU lineage:** [CPU4096](https://github.com/amerhwitat/CPU4096)
- **Web simulator:** [CPU4096Simulator](https://github.com/amerhwitat/CPU4096Simulator)
- **Python integration:** [test](https://github.com/amerhwitat/test)
- **Java track:** [keygen](https://github.com/amerhwitat/keygen)
- **Mobile/integration:** [general](https://github.com/amerhwitat/general)
- **NLP:** [nlp](https://github.com/amerhwitat/nlp)
- **PDF research:** [PDFreaderPY](https://github.com/amerhwitat/PDFreaderPY)
- **Crypto interoperability:** [eth-key-check](https://github.com/amerhwitat/eth-key-check) and [bruteforce](https://github.com/amerhwitat/bruteforce)
- **Graphics experiments:** [BizX](https://github.com/amerhwitat/BizX) and [BizXtreme](https://github.com/amerhwitat/BizXtreme)
- **Public web:** [amerhwitat.github.io](https://github.com/amerhwitat/amerhwitat.github.io)

## Publication and hosting policy

GitHub is the current canonical public forge. Git history is the portable source-history layer. GitLab, Codeberg/Forgejo, SourceHut, WordPress and image-hosting services are secondary publication targets only when a user-controlled account/repository is connected and the resulting write succeeds.

A search-engine result or a public URL is not treated as proof that material has been published or indexed. Publication records should contain the destination URL, publication date, asset name and source repository.

## Image assets

Chimera II visual assets should be stored in repository-controlled `web/` or `assets/` directories and referenced from the public website before optional mirroring to external image hosts. This provides a durable source even if a third-party host changes or removes an asset.

## Provenance and licensing

Third-party source is not copied merely because it is publicly accessible. Adaptations require compatible licensing and preservation of notices. Research references should link to upstream projects and standards. See `docs/CRYPTO_UPSTREAMS_AND_PROVENANCE.md` for the crypto-specific provenance and safety boundary.

## Security boundary

Crypto research in this ecosystem is limited to legitimate key material already possessed by the operator, deterministic derivation, validation, published test vectors, benchmarking and interoperability. No repository should implement public-address-to-private-key search, guessing, inference or wallet-targeted recovery.

## Related documentation

- [Ecosystem index](CHIMERA_ECOSYSTEM_INDEX.md)
- [Crypto upstreams and provenance](CRYPTO_UPSTREAMS_AND_PROVENANCE.md)
- [Author bibliography](AUTHOR_BIBLIOGRAPHY_AMER_HWITAT.md)
- [Library research archive](LIBRARY_RESEARCH_ARCHIVE_INDEX.md)
- [Public CI/CD plan](CI_CD_PUBLIC_RESEARCH_OS_PLAN.md)
