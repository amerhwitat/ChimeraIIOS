# Online ISA and Arabic command catalogs

The ISO builder supports an explicit online refresh:

```bash
./build-chimera-iso.sh --refresh-online-catalogs
```

Equivalent environment switch:

```bash
CHIMERA_REFRESH_ONLINE_CATALOGS=1 ./build-chimera-iso.sh
```

The refresh step checks a curated set of authoritative vendor/specification pages and
machine-readable LLVM instruction-definition sources covering x86, x86-64, ARM32,
AArch64, RISC-V, MIPS, Power ISA, SystemZ and SPARC. It also discovers command names
from POSIX, GNU, SS64, Microsoft and FreeBSD indexes. Each fetched source is recorded
with URL, timestamp, content type and SHA-256. TableGen definition identifiers are
candidate discovery data only; they are not asserted to be canonical mnemonics,
exhaustive ISA coverage, decoded/executed support, or conformance.

Generated outputs:

- `data/isa/online-isa-index.json`
- `system/commands/online-command-catalog.json`
- updated `system/commands/chimera-arabic.json`

The crawler stores names, links and hashes rather than copying proprietary manuals
or reference-page prose. Network errors are recorded per source and do not prevent
the catalog from showing which sources were unavailable. The normal ISO build stays
offline/reproducible unless online refresh is explicitly enabled.

Arabic command names are curated semantic aliases, not machine-translated guesses.
Only curated aliases are executable; catalog entries without a curated alias are
marked `untranslated` and keep their canonical command name. The alias registry maps
Arabic input back to canonical command names, preserving normal shell argument and
option semantics.
