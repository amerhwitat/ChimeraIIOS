# Native tooling

The `src/tools/` programs are the canonical compiled replacements for Python utilities that participate in Chimera II OS build/metadata validation.

| Native executable | Replaces / supersedes | Purpose |
|---|---|---|
| `chimera_native_tools` | `tools/toolchain/validate_registry.py`, `tools/memory/validate_profiles.py` | Toolchain, ISA and memory metadata validation |
| `chimera_isa_generator` | `tools/isa/generate_isa_bitfields.py` (core generation path) | Native ISA CSV-to-JSON metadata generation |

Python remains available for research and optional data-processing tasks. It is no longer required for the core native metadata-validation path.

## Design rule

Native equivalents preserve the repository's data contracts rather than performing unsafe source-to-source translation. JSON/CSV manifests remain declarative inputs; native C++ performs validation/generation; architecture-specific operations remain in ASM.
