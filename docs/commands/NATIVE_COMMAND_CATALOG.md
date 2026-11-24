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

### Populated descriptor counts (post-fix)

| Descriptor | Populated rows |
| --- | ---: |
| `operands` | 4503 / 4503 |
| `options` | 4503 / 4503 |
| `effects_on_registers` | 4503 / 4503 |
| `register_effects_status` (object) | 4503 / 4503 |

All source catalogues were inspected: they contain only command names,
platforms, source URLs and translation labels. They have **no** operand,
option/switch or register-effect fields. Consequently, unknown descriptors are
emitted explicitly rather than inventing syntax:

- For the 28 verified providers, operand and option descriptors are derived
  from `native-provider-engineering.json:provider_specs` and verified against
  the real C functions. Each descriptor carries `kind`, `name`/`flag`, `type`,
  `required`, `value_constraints`, `form`, `value_type`, `default`,
  `source_field` and `evidence`. A provider with no operands/options gets an
  explicit `none-declared` descriptor, never an empty array.
- For the other 4475 rows, descriptors are explicit structured unknowns with
  `kind: "unspecified"`, `name: "<unknown-from-source>"`, `required: null`,
  `type: "unknown"`, `value_constraints: "unknown-from-source"`,
  `source_field: "none (no operand/argument field in any source catalogue)"`
  and `evidence: "no operand metadata in source catalog"` (and the analogous
  option fields).
- `effects_on_registers` is a structured object for every row:
  `visibility: "not-isa-visible"`, empty `reads`/`writes`/`clobbers` lists,
  `status: "no-architectural-register-effects"`, a reason explaining that ISA
  instruction effects live in the separate ISA catalogue, plus source-field and
  evidence strings. No command row is a machine instruction, so no concrete
  register effects are claimed. `register_effects_status` is an object with the
  same evidence/status detail, not a bare string.

## CHMCMD v1 binary format

`tools/commands/chmcmd_format.py` defines the layout; the builder emits one
record per catalogue command:

- file header: magic `CHMCMD01`, version `1`, record count, reserved;
- record header: magic `RECD`, record length, architecture id, implementation
  status, permission flags and twelve length/count fields;
- payload: name, namespace, ISA target strings, **JSON operand descriptors**,
  **JSON option descriptors**, provider symbol table, exit-code description,
  side-effect description, reason (when unimplemented), **JSON
  `effects_on_registers` object** and **JSON `register_effects_status` object**.

The builder rejects any row with empty `operands`, `options`,
`effects_on_registers` or `register_effects_status`. The validator rejects bad
magic/version, length mismatches, unknown ids, duplicate names, trailing bytes,
missing symbols/reasons, empty or non-object descriptor sections, row-order or
implementation mismatches against the catalogue, descriptor mismatches, and any
alteration of official status. Corrupted-record, empty-descriptor and
string-instead-of-object status tests are part of the suite.

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
