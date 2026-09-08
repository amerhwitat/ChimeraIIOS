# Chimera II ISA Toolchain and UNIX Compatibility Layer

## 1. ABI invariant

The executable emulator ABI remains unchanged:

```text
opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]
```

The generated bitfield registry is metadata for logical instruction encodings and tooling. It does not silently replace the host packet.

## 2. Automatic bit-mask generation

`tools/isa/generate_isa_bitfields.py` reads:

- `tools/isa/chimera_isa_r8192_complete.csv` — canonical semantic instruction identity;
- `tools/isa/isa_opcodes_expanded_with_encodings.csv` — earlier encoding metadata;
- `tools/isa/isa_extension_0092_011c.csv` — supplied extension metadata.

For every instruction the generator emits explicit `start`, `end`, `width`, `mask`, and `shift` fields. Where a logical template is unavailable, it emits the canonical 16-byte ABI fields and labels the record `canonical_abi_only`. This is deliberate: missing hardware encodings are not fabricated.

Run:

```bash
python3 tools/isa/generate_isa_bitfields.py
python3 tools/isa/test_isa_conformance.py tools/isa/isa_bitfields.json
python3 tools/isa/chimera_asm.py --schema tools/isa/isa_bitfields.json assemble ADD 1 2 3
python3 tools/isa/chimera_asm.py --schema tools/isa/isa_bitfields.json disassemble 0x01010203
```

The generator therefore supplies the complete semantic ISA registry with automatically derived masks while retaining the distinction between canonical ABI and illustrative logical templates.

## 3. Conformance

The conformance layer verifies:

- unique mnemonic and 16-bit opcode identity;
- opcode range `0x0000..0xFFFF`;
- field width equals `end-start+1`;
- masks equal the declared width/shift;
- no field overlap;
- valid hexadecimal example vectors;
- canonical 16-byte ABI layout;
- generated instruction count consistency.

Known ambiguous records remain visible as validation data instead of being silently corrected. In particular, `ECC_POINT_ADD` has a separate `rt` field without a bit position, and several `0x0107..0x011C` templates use 8-bit opcode fields despite 16-bit opcode identities.

## 4. JSON reader

`include/chimera/isa_bitfields.hpp` and `src/isa/isa_bitfields.cpp` provide a dependency-free C++20 reader for the generated JSON registry. The reader exposes lookup by opcode/mnemonic and mask extraction/insertion helpers. It is linked into `chimera_machine` and tested by `chimera_isa_bitfields_test`.

## 5. UNIX/Linux command compatibility

Chimera II now has a command compatibility registry generator at `tools/shell/generate_command_registry.py` and source-family metadata at `tools/shell/chimera_command_sources.json`.

The design separates:

1. POSIX-standard utilities and shell language;
2. GNU/Linux utilities such as GNU Coreutils;
3. Linux-specific and multi-call families such as BusyBox/util-linux/systemd;
4. BSD families (FreeBSD/OpenBSD/NetBSD/DragonFly BSD);
5. Darwin/macOS;
6. Solaris/illumos/System V-derived systems;
7. AIX and HP-UX;
8. shell-specific builtins/features for Bash, Zsh, POSIX sh, dash and BSD shells.

The registry is generated from the host's `PATH` and installed shell builtins, then classified against source-family metadata. It intentionally records availability rather than assuming that an option or semantic extension is portable across UNIX variants.

POSIX defines the shell command language and command-search semantics; `command -v/-V` is itself a standardized way to query how a command name is interpreted. citeturn2search0turn2search11

Bash documents builtin commands and its command-resolution order, while Zsh maintains its own builtin/module/function surface. citeturn0search1turn0search2turn2search12

FreeBSD documents a distinct builtin index and maintains separate manuals for its userland and kernel interfaces; its manual-page archive also exposes multiple OS/release aliases. citeturn2search3turn2search5

GNU Coreutils is tracked as a separate implementation family rather than being treated as synonymous with POSIX. citeturn0search3

## 6. Safety boundary

The registry does **not** turn arbitrary host commands into privileged Chimera ISA instructions. Command execution remains subject to Chimera's capability and service-dispatch boundaries. Host filesystem, network, device, power-management and security effects must occur through explicit services.

## 7. Future expansion

The catalog generator can be run on target Linux/UNIX systems to capture the commands actually installed there. This is more reliable than attempting to claim a single static list is complete for every Linux distribution and UNIX release. Static portability metadata should be expanded only from authoritative manuals/specifications.
