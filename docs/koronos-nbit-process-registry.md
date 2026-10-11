# Koronos arbitrary-width N-bit execution, ISA mapping, and process registry

## User-selectable width and execution contract

The virtual ABI accepts any positive integer width from 1 through 4,294,967,295 bits; it no longer restricts widths to powers of two or stops at 8192 bits. The upper bound is the current ABI's 32-bit width field, not mathematical infinity. Actual usable width is bounded by available memory, process policy, caller-provided buffer capacity, and runtime step limits. A width request never allocates memory implicitly.

Use `python3 tools/nbit/select_mode.py` for an interactive selection, or for a scripted profile. Build custom metadata variants with `CHIMERA_NBIT_EXTRA_WIDTHS="13 8193 100003" bash kernel/build-koronos.sh`; these image-note artifacts do not imply physical native execution:

```sh
python3 tools/nbit/select_mode.py --bits 8193 --backend chimera-virtual --isa chimera-nbit
python3 tools/nbit/select_mode.py --bits 32 --backend compatibility --compatibility linux --isa x86-32
python3 tools/nbit/select_mode.py --show
```

The CLI selection is stored in `config/nbit-mode.json`. Aurora Settings also exposes `isa.nbit.width`, `isa.nbit.backend`, `isa.nbit.guest`, and `isa.nbit.compatibility`, and writes the per-user profile to `~/.config/chimera/nbit-mode.json`. For example, `aurora-settings set isa.nbit.width 8193` followed by `aurora-settings set isa.nbit.backend chimera-virtual` selects the virtual ABI; select the guest ISA separately. For a Linux/x86-32 compatibility profile, set the guest to `x86-32`, the compatibility personality to `linux`, then select the `compatibility` backend. These files are requested profiles, not authorization tokens: the kernel must apply and validate them against the probed hardware and runtime policy before process admission. The kernel APIs are `chimera_nbit_set_default_profile`, `chimera_nbit_process_init_default`, `chimera_nbit_process_init_physical_native`, and `chimera_nbit_process_init_chimera`. The profile setters `chimera_nbit_set_default_profile` and `chimera_nbit_set_default_profile_ex` map installer choices to the kernel backend and guest-ISA policy. Profile JSON includes numeric `backend_id`, `guest_isa_id`, and `compatibility_target_mask` fields aligned with the kernel enums; the last explicitly selects the Chimera virtual ABI. The current generic ELF64 loader honors the selected process profile but rejects virtual or compatibility profiles rather than incorrectly transferring them into physical x86-64 ring 3. The JSON selector is a policy file, not yet a kernel-side JSON parser; installer/runtime integration must call the profile API before admitting processes.

**Physical native width is not user-configurable.** Only the detected CPU's `native_nbit_mode` can be reported as physical-native. The Chimera virtual N-bit mode is native to the OS-defined guest ABI and runs in the bounded software VM; it does not imply physical CPU registers or native instructions of arbitrary width.

## OOP runtime and performance properties

`ChimeraNBitArithmetic` in `kernel/core/nbit_runtime.cpp` implements allocation-free unsigned add/subtract, bitwise AND/OR/XOR/NOT, logical shifts, and unsigned compare over little-endian caller-owned buffers. Operations are linear in the number of bytes for these primitives. Views validate their width and capacity; unused high bits are masked. No exceptions, RTTI, heap allocation, or shared mutable arithmetic state are required.

`ChimeraNBitVM` implements a versioned, fixed-size 8-byte instruction format with LOAD_IMM32, MOV, ADD, SUB, AND, OR, XOR, NOT, SHL, SHR, CMP, JMP, JZ, and HALT. It runs over caller-provided register storage, rejects malformed opcodes/register indices/jumps, and enforces an instruction step limit. This makes small programs in the Chimera virtual bytecode runnable in the N-bit ABI. It is not yet a compiler, JIT, or complete implementation of every catalogued Chimera ISA candidate.

The arithmetic API is reentrant. `chimera_nbit_batch_add` lets a caller process disjoint ranges of independent values, so an SMP scheduler can dispatch separate ranges to different CPUs without shared scratch state. A single add/subtract carry chain remains sequential; no false claim of parallelizing a dependent arithmetic operation is made.

## CISC/RISC ISA inventory and compatibility boundary

`isa/isa_database.json` inventories 102 architecture/extension profiles and 168 instruction forms at this revision, with explicit source references and execution/conformance status. It includes x86-16/32/64 and extensions such as APX/AVX10, Arm32/AArch64 and SVE/SME, RISC-V 32/64/128 and vector/crypto/privileged profiles, plus MIPS, Power/PowerPC, LoongArch, SPARC, s390x, WebAssembly, and the project-defined Chimera profiles. Official references include the [Intel Software Developer Manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html), [Intel ISA extensions](https://www.intel.com/content/www/us/en/developer/tools/isa-extensions/overview.html), [Arm architecture documentation](https://developer.arm.com/architectures), and [RISC-V ratified specifications](https://docs.riscv.org/reference/isa/v20260120/index.html).

ISA profile selection and registry presence do not automatically execute foreign binaries. A working compatibility backend requires a correct decoder, semantics, ABI/syscall translation, binary loader/relocator, memory model, and conformance tests for each ISA/extension. Those full x86, Arm, RISC-V, MIPS, Power, LoongArch, SPARC, and s390x executable backends are not all implemented by this change. Unsupported operations must fail closed rather than being guessed from mnemonic similarity. AVX/SVE/vector widths are not general-purpose CPU native process widths.

## Process visibility and lifecycle

Every process admitted through `chimera_process_admit_elf` registers in the N-bit registry as an ELF64 process. Launchers that select a compatibility personality or virtual mode must call `chimera_process_set_execution_mode` before making the process runnable. Independent launch paths must register explicitly. Registry snapshots expose metadata, not a replacement for the scheduler's task inventory.

Process exit/fault removes mode metadata and cleans IPC endpoints and queued messages. The registry has a fixed capacity of 1024 process contexts. Registration failure must fail process admission rather than silently hiding a process.

## Cross-width IPC

`kernel/core/ipc.cpp` implements bounded endpoint queues with capability checks, per-message sender/receiver width metadata, FIFO delivery, cancellation, and process-exit cleanup. Queue depth is 16 messages per endpoint; payloads are limited to 1024 bytes. Sender data is copied into kernel-owned staging through `copy_from_user`, and receive delivery uses `copy_to_user`. These callbacks must validate address spaces and handle faults safely.

The current boot path does not yet install these callbacks or expose IPC through a complete protected ring-3 syscall path. Therefore this is a kernel-callable, host-testable service, not yet a complete production user-mode IPC facility.

## Verification boundary

CI now contains tests for arbitrary-width arithmetic, VM execution and step limits, profile selection, registry operations, IPC delivery/authorization/cancellation, and the freestanding kernel link. These tests must pass on the latest commit; they have not been run in this editing session. QEMU/ISO success is not claimed until a current workflow run provides the results.
