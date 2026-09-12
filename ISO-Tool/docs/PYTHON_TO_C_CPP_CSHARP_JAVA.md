# Python → C/C++/C#/.NET/Java parity

ISO-Tool uses Python as the behavioral reference and recursively inventories its Python implementation before compilation. `source_translator.py` performs AST inspection and emits deterministic C, C++, C# and Java parity units with SHA-256 source identity.

## Pipeline

`toolchain detection → dependency inventory → Python AST inspection → parity generation → recursive source scan → build planning → compile/link → artifact staging → Spit Fire → ISO/IMG verification`

Run:

```text
python -m iso_tool.source_translator <python-root> --output <output>/generated/python-parity
```

The normal build entry point performs this automatically after dependency detection.

## Target baselines

C11 metadata, C++17 native baseline (C++20 permitted), C# common .NET 6 / .NET Framework 4.8 API surface, and Java 8+.

## Semantic safety

The translator does not pretend that dynamic Python constructs can always be mechanically translated. It records imports, classes, functions and hashes. Native language implementations are considered complete only after behavior is implemented and contract tests pass.

## Generated layout

```text
<output>/generated/python-parity/
  c/*.c
  cpp/*.cpp
  csharp/*.cs
  java/*.java
  parity-manifest.json
```

The manifest is the synchronization authority for Python module coverage and source identity.
