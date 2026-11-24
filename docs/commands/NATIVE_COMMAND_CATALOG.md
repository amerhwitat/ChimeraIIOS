# Native command catalogue and CHMCMD v1 command-object format

## Scope and honesty policy

`tools/commands/generate_native_command_catalog.py` reads every relevant source
catalogue and emits `system/commands/native-command-catalog.json` with one row
per union command. A row is marked implemented **only** when the provider name
has:

1. a real dispatch comparison in `src/chimera-command-compat/chimera-cmd.c`,
2. a matching `static int <function>(` provider implementation, and
3. an installed alias in `tools/build-chimera-command-compat.sh`.

Catalog metadata such as `implementation: "native-source-implemented"` is never
used as proof. A test injects a forged metadata row and asserts it stays
`not_implemented`.

Official status is read but never modified: ISA `status=not-run`,
`conformance_tested=0`, `not_implemented=1613`; command capabilities remain
4144 records with 3905 compatibility-provider-required, 171
native-provider-required and 15 official native-backed commands. The 28
implemented providers below are engineering evidence, not a change to those
counts.

## Measured catalogue counts (this checkout)

| Input | Records |
| --- | ---: |
| `chimera-command-list.json` unique names | 931 |
| `command-isa-coverage.json` unique commands | 853 |
| `command-runtime-capabilities.json` records | 4144 |
| `native-command-candidates.json` records | 4084 |
| `ss64-command-catalog.json` index entries | 5299 |
| Union of all names (generated rows) | 4503 |
| Verified real providers | 28 |
| Explicitly `not_implemented` rows | 4475 |

The 28 providers are the original 15 (`pwd`, `echo`, `ls`, `cp`, `mv`, `touch`,
`mkdir`, `rm`, `cat`, `clear`, `whoami`, `hostname`, `date`, `true`, `false`)
plus 13 new real implementations (`basename`, `dirname`, `head`, `tail`, `wc`,
`seq`, `sleep`, `uname`, `readlink`, `rmdir`, `ln`, `printenv`, `env`).

## Row fields

Each row carries `name`, `namespace`, `isa_targets`, `operands`, `options`,
`implementation`, `implementation_reason`, `effects_on_registers`,
`register_effects_status`, `exit_codes`, `side_effects`, `permission_flags`,
source catalogues, platforms and source URLs. Commands with no real provider
have empty operand/option lists, empty ISA targets, no register effects, and an
explicit reason. No register effect is invented: these are userspace commands,
not ISA instruction backends.

## CHMCMD v1 binary format

`tools/commands/chmcmd_format.py` defines the layout; the builder emits one
record per catalogue command:

- file header: magic `CHMCMD01`, version `1`, record count, reserved;
- record header: magic `RECD`, record length, architecture id, implementation
  status, permission flags and ten length/count fields;
- payload: name, namespace, ISA target strings, operand descriptors
  (kind/required/type/name), option descriptors (flag/description), provider
  symbol table, exit-code description, side-effect description and, for
  unimplemented rows, a mandatory reason.

`tools/commands/validate_native_command_format.py` rejects bad magic/version,
length mismatches, unknown ids, duplicate names, trailing bytes, implemented
records without symbols, unimplemented records without a reason, row-order or
implementation mismatches against the catalogue, and any alteration of official
status. A corrupted-record test is part of the test suite.

## Conformance boundary

`tools/commands/run_command_conformance.py` executes the real multicall binary
through per-provider symlinks and records measured pass/fail counts per ISA.
Local x86_64: 39 cases executed, 39 passed, 0 failed. aarch64 and riscv64:
0 executed, `not-run`, because no cross-built executable/emulator was supplied.
These are partial engineering results only; `full_catalog_run=false`,
`conformance_claim=false`, `production_acceptance=false`.

The cross-build matrix reports x86_64 built and aarch64/riscv64 as real failures
in this environment because their compilers are unavailable. It records the
28 provider aliases actually linked per successful target.
