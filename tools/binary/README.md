# Chimera binary tools

These tools identify binary formats passively and build the experimental NCB1
container. NCB1 output is a reference format; building it does not make the
payload executable on the host or prove ABI/runtime compatibility.

## Create and inspect a swap area

```sh
python3 tools/memory/chimera_swap.py create /tmp/chimera.swap --slots 16
python3 tools/memory/chimera_swap.py info /tmp/chimera.swap
```

Expected capacity: 16 pages × 4096 bytes = 65536 bytes (64 KiB). The swap
backend requires a regular file and is a finite-file reference implementation,
not a kernel page-fault handler.

## Build and inspect a sample NCB1 image

Run from the repository root:

```sh
python3 tools/binary/build_ncb.py tools/binary/manifest.example.json /tmp/chimera-example.ncb
python3 tools/binary/chimera_binary.py --json /tmp/chimera-example.ncb
```

The builder also works from another current working directory because it adds
its own directory to Python's module search path. Relative section `path`
values are resolved relative to the manifest file, not the current directory.
The manifest must exist and be valid JSON; there is no implicit `manifest.json`
in the working directory.

## Identify a binary

Pass a path to an existing regular file, not a directory:

```sh
python3 tools/binary/chimera_binary.py --json /path/to/file
```

Missing files and directories produce actionable command-line errors. This
tool only identifies and validates file structure; it never executes a file.
