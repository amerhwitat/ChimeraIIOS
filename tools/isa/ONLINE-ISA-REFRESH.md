# Online ISA discovery, semantics metadata, and execution status

Run from the repository root:

```sh
python3 tools/isa/refresh_isa_catalog.py --refresh
python3 tools/isa/refresh_isa_catalog.py --offline
python3 tools/isa/refresh_isa_catalog.py --self-test
python3 -m unittest tools/isa/test_refresh_isa_catalog.py -v
```

The generated catalog carries operand syntax, instruction width and encoding
masks, register classes, flag effects, memory effects, privilege requirements,
extensions/features, exceptions, source revision/hash/license, explicit native
and compatibility mappings, and execution-status fields. Unknown effects remain
unknown; discovery never synthesizes encodings or semantics from prose.

Status values are evidence gates: `not-implemented` means no backend is claimed;
`implemented-unverified` means code exists without established conformance;
`conformance-tested` requires test evidence and is never auto-assigned by
discovery. Every processor family still requires source-backed importers and
architecture-specific execution/conformance work. This pipeline does not claim
to import every instruction from every processor revision or make every ISA
runnable automatically.
