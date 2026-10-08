# Chimera II multi-ISA virtualization

## Design

Chimera II uses QEMU system emulation as the initial machine/device-model layer and chooses a host accelerator only after capability checks. KVM is a host-kernel acceleration interface, not a universal cross-ISA interpreter. Use KVM only for a compatible host/guest architecture and only when `/dev/kvm` and the selected QEMU target support it. Use QEMU TCG for supported cross-ISA guests. Backend availability does not guarantee a particular guest OS will boot.

The command-line integration is `tools/virtualization/chimera-hypervisor.py`; its allow-list and declared accelerator capabilities live in `tools/virtualization/hypervisor-backends.json`. The launcher uses argument arrays (never a shell), validates image paths, and rejects disabled backends.

## Current initial targets

| Target | QEMU system target | Planned accelerator policy |
|---|---|---|
| x86-64 / AMD64 | `qemu-system-x86_64` | KVM when supported, otherwise TCG |
| IA-32 / 8086-family machine compatibility | `qemu-system-i386` | KVM when supported, otherwise TCG |
| AArch64 | `qemu-system-aarch64` | KVM when supported, otherwise TCG |
| ARM32 | `qemu-system-arm` | KVM when supported, otherwise TCG |
| RISC-V RV64 | `qemu-system-riscv64` | KVM when supported, otherwise TCG |
| RISC-V RV32 | `qemu-system-riscv32` | TCG initially |
| MIPS | `qemu-system-mips` | target/host-dependent KVM or TCG |
| Power ISA | `qemu-system-ppc64` | target/host-dependent KVM or TCG |
| SPARC | `qemu-system-sparc` | TCG |
| Motorola 68000 | `qemu-system-m68k` | TCG |
| IBM System z | `qemu-system-s390x` | target/host-dependent KVM or TCG |
| DEC VAX | no backend enabled by this integration | blocked until a verified system backend is selected |
| Chimera N-bit | no backend enabled by this integration | blocked until its architecture and machine model are executable and tested |

These are backend candidates, not claims that every machine option, extension, device, or guest image is supported. At runtime, `list` reports which configured QEMU binaries are actually installed.

## Usage

```sh
python3 tools/virtualization/chimera-hypervisor.py list
python3 tools/virtualization/chimera-hypervisor.py run --backend qemu-x86_64 --cdrom build/chimera.iso --accel auto --dry-run
python3 tools/virtualization/chimera-hypervisor.py run --backend qemu-riscv64 --kernel path/to/Image --accel tcg --dry-run
```

Remove `--dry-run` only when the selected QEMU binary, machine model, boot media, and host capabilities are known. The CLI currently offers generic QEMU arguments; architecture-specific machine/CPU/firmware profiles must be added and tested before promising arbitrary guest boot support.

## Native Chimera N-bit roadmap

1. Freeze a versioned N-bit architecture specification: register widths, address width, instruction encoding, endianness, privilege levels, traps/interrupts, atomics, memory model and ABI.
2. Implement a deterministic reference interpreter and assembler/decoder with illegal-instruction tests.
3. Define a machine model and boot ABI shared by Koronos, the ISO builder, and the emulator.
4. Add memory/MMU and device models plus snapshot/debug hooks.
5. Integrate as a dedicated QEMU CPU/system target or a separately isolated backend adapter. Do not masquerade as x86/RISC-V or claim KVM acceleration.
6. Add CI conformance and boot tests, then enable the registry entry only after they pass.

## Security and validation

Run untrusted guests as an unprivileged user, avoid host-device passthrough by default, use isolated networking, and do not expose the host bridge as a guest control plane. A real sandbox policy, resource quotas, disk formats and networking options should be hardened before this is used for hostile guest workloads.

Tests: `python3 -m unittest tools/virtualization/test_chimera_hypervisor.py`. QEMU execution and guest boot tests require the corresponding binaries and images and are not implied by unit tests.


## Machine profiles, Aurora and local bridge

Machine/CPU/firmware/device candidates are listed in `tools/virtualization/machine-profiles.json`. The launcher now accepts `--profile` and `--vcpus`; profile options are only candidates until tested against the exact installed QEMU version. QEMU's own machine help is authoritative for what a build actually supports. Some profile firmware names are optional lookups and may require an explicit firmware path or distro package.

Aurora's Hypervisor view uses the localhost bridge endpoints:
- `POST /hypervisor/profiles` — enumerate profiles and detected QEMU targets.
- `POST /hypervisor/guests` — show tracked guest processes.
- `POST /hypervisor/guests/start` — start a selected profile, with RAM limited to 128–1024 MiB and vCPUs limited to 1–2 at the UI bridge.
- `POST /hypervisor/guests/stop` — terminate a tracked process.
- `POST /hypervisor/nbit/demo` — run a bounded interpreter self-test, not a guest OS.

These are local orchestration limits, not a hardened resource sandbox: QEMU's process overhead is not capped by these values, and the current bridge keeps process state in memory (restart loses the list). Do not expose the bridge to untrusted networks. The existing bridge binds to loopback; production isolation should add OS-level cgroups/job objects, an origin allow-list, authenticated local control, timeouts, and an unprivileged account.

## CI and guest boot evidence

The virtualization CI validates profile schema, runs the reference CPU tests, and checks machine names for QEMU targets installed on the runner. That is not the same as booting a guest OS. No per-architecture guest images/firmware artifacts were supplied as part of this change, so successful guest boot cannot be claimed yet. To enable boot tests, add redistributable minimal test images or build reproducible kernel/initramfs artifacts per architecture, pin their hashes and firmware versions, and run each under a time limit with serial-console assertions and exit status checks. Architecture profiles must be narrowed to targets that pass those tests.

Coverage is tracked separately in `tools/virtualization/execution-coverage.json`: catalog, execution, guest-boot and official-conformance are distinct fields. RISC-V ACT and x86 vendor architectural conformance suites are not run by this CI.
