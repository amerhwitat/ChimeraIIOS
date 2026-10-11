# Enterprise services, GPU toolchains, N-bit registers, and Aurora events

## Optional enterprise services

The installer catalog at `installer/services/enterprise-services.json` groups identity, database, web, observability, container, file/print, backup, and messaging services. Profiles are optional and none are enabled by default. Review a service's package names, ports, secrets, storage, and configuration before selecting it.

`tools/services/enterprise_service_installer.py` prints a plan by default. With `--apply`, it attempts to download and extract packages into the chosen rootfs, never installing them into the running build host. It retries other available package managers if the first staging adapter fails. The adapters currently support safe rootfs extraction for apt/deb and dnf/yum with rpm2cpio/cpio; other package managers are detected but skipped when they cannot safely stage into a rootfs.

Source fallback is opt-in and requires both `--source-archive SERVICE=PATH` and `--source-sha256 SERVICE=HEX`. Archives are hash-checked and unsafe paths/links are rejected before extraction. Builds run with `DESTDIR` set to the target rootfs. A successful source build is not, by itself, proof of ABI compatibility, correct dependency closure, hardened service configuration, or operational readiness.

Example plan:

```sh
python3 tools/services/enterprise_service_installer.py
python3 tools/services/enterprise_service_installer.py --profile database --rootfs build/rootfs
```

Explicitly reviewed installation/staging example:

```sh
python3 tools/services/enterprise_service_installer.py \
  --service postgresql --rootfs build/rootfs --apply --enable
```

The boot dispatcher only considers the persisted plan when `user_review_confirmed` is true, and starts only service units that exist. A service still needs valid configuration, credentials, dependency resolution, and security review before production use.

## GPU programming and GPU ISA

`isa/gpu_isa_registry.json` records Vulkan/SPIR-V, OpenCL, CUDA/PTX, HIP/ROCm, DirectCompute, and Metal as distinct programming models. It catalogs NVIDIA PTX and generation-specific NVIDIA machine code, AMD GCN/RDNA/CDNA, Intel Xe, Arm Mali, and Qualcomm Adreno families. Catalog membership is not a claim that Chimera has a native decoder or emulator for those ISAs.

`tools/gpu/chimera_gpu_toolchain.py --inventory` probes for local compiler/runtime tools. Its compile adapters use installed vendor toolchains and never run GPU binaries on the CPU. Device execution remains unverified until the relevant device, driver, runtime, and target architecture are probed.

References:
- NVIDIA PTX ISA: https://docs.nvidia.com/cuda/parallel-thread-execution/
- NVIDIA CUDA programming guide: https://docs.nvidia.com/cuda/cuda-programming-guide/
- AMD machine-readable GCN/RDNA/CDNA ISA: https://gpuopen.com/machine-readable-isa/
- LLVM AMDGPU backend: https://llvm.org/docs/AMDGPUUsage.html
- Intel AVX/AVX-512 extended-state requirements: https://www.intel.com/content/dam/develop/external/us/en/documents/319433-024-697869.pdf

## N-bit register and cache model

The N-bit integer ABI accepts arbitrary positive widths within its 32-bit width field and supplied buffer/resource limits. The fixed-capacity instruction cache is caller-owned and direct-mapped; VM instances own their cache and must increment `code_generation` whenever program contents change. It caches instruction fetch/decode records, not CPU data or instruction caches, and is not a substitute for hardware cache-coherence protocols.

The N-bit vector FPU API currently implements IEEE binary32 and binary64 lane operations over arbitrary-width register views whose widths are multiples of the lane size. It is a software/host-FPU lane backend, not an implementation of arbitrary-precision floating-point formats. The freestanding kernel does not execute these host-FPU operations until per-thread x87/SSE/AVX state preservation is implemented. AVX/AVX-512 capabilities are only advertised when CPUID and the required OS-enabled XCR0 state agree.

## Aurora click and compatibility events

`desktop/aurora/aurora_event_loop.py` accepts newline-delimited JSON events from a compositor or compatibility adapter. It maps single click to selection, double click to open, triple click on text to select-all, title-bar double click to maximize/restore, and right-click/long-press/Shift+F10 to context menus. It validates event surfaces and uses a fixed action allowlist. External action dispatch is dry-run unless `CHIMERA_DESKTOP_DISPATCH=1` is explicitly set.

This is the event-dispatch contract and adapter entry point. A compositor or window-manager integration must actually forward pointer/keyboard events to it for desktop-wide click behavior to be active.
