# Embedded knowledge database

The native images carry a structured knowledge base that the AI module and the
userspace tooling read at runtime. It lives at `config/ai/knowledge-db.json` in
the repository and is staged into every ISO at `/boot/ai/knowledge-db.json` as a
Multiboot2 module named `ai-knowledge-db`.

## What it is, precisely

- A **curated retrieval corpus**: 269 entries, each with a stable id, category,
  topic, one-paragraph summary, tags and a source.
- The kernel does **not** parse JSON and does **not** train anything at boot. It
  counts `"id"` keys in the staged module and reports:

  ```
  [AI  ] Knowledge database staged: 269 entries, 110668 bytes
  ```

  That line proves the corpus reached the runtime; it is not a quality claim.
- There are **no model weights** in the image. "Learning" here means ingestion:
  validate an entry, de-duplicate by id, append to the database, rebuild the ISO.

## Coverage today

| category | entries | example |
| --- | --- | --- |
| `arch` | 34 | `aarch64 user/kernel boundary` — `svc #0`, TTBR0/TTBR1, x0-x5/x8 ABI |
| `driver` | 29 | `virtio-blk`, `NVMe admin queue`, `IOMMU (VT-d)`, `ACPI S5` |
| `isa` | 148 | imported from `isa/isa_database.json` (CHM-ISA-DB-4) |
| `language` | 15 | C/C++ freestanding rules, Rust `no_std`, NASM vs GAS |
| `kernel` | 12 | paging, TSS/RSP0, SYSCALL/SYSRET, ELF64 W^X loading |
| `boot` | 6 | Multiboot2, UEFI, El Torito, cpio initramfs |
| `linux` | 7 | Linux 7.3 boot protocol, `start_kernel`, EEVDF, Kbuild |
| `fs` | 6 | ext4, FAT32, ISO9660, squashfs, cpio newc |
| `desktop` | 4 | Aurora shell, WebKitGTK kiosk, X11 session |
| `toolchain` | 6 | GCC freestanding flags, LLVM/lld, linker scripts |
| `userspace` | 2 | init contract, syscall ABI |

## Commands

```bash
python3 tools/ai/knowledge_db.py build       # regenerate from seeds + ISA catalogue
python3 tools/ai/knowledge_db.py validate    # schema, duplicate and count checks
python3 tools/ai/knowledge_db.py stats       # per-category counts
python3 tools/ai/knowledge_db.py query "riscv svc paging"
python3 tools/ai/knowledge_db.py append --json '{
  "category": "driver",
  "topic": "USB HID boot protocol",
  "summary": "A HID keyboard in boot protocol reports 8-byte reports on an interrupt IN endpoint; set_protocol(0) selects it.",
  "tags": ["usb", "hid", "keyboard"],
  "source": "user-request"
}'
python3 tools/ai/knowledge_db.py append --file new-entries.json
python3 tools/ai/knowledge_db.py export-c    # kernel/generated/knowledge_db_index.h
```

`append` re-validates, refuses duplicates by id and bumps `entry_count`, so the
next ISO build ships the larger corpus without any other change.

## Guardrails

- Every entry needs `category` from the fixed list, `topic`, `summary` and a
  `source`; user-appended entries default to `confidence: user-supplied`.
- Ids are `category:slug(topic)`, so the same topic cannot silently fork.
- The ISO builder runs `validate` against the *staged* copy and fails the build
  if it does not pass — a malformed database cannot ship.

## Relationship to Linux 7.x

The `linux` category records the reference behaviour (boot protocol,
`start_kernel`, driver model, VFS, EEVDF, Kbuild) that this project measures
itself against, and `docs/KORONOS_VS_LINUX_7X.md` maps each subsystem. Koronos
does not claim Linux ABI compatibility; the database says so in the entries
themselves rather than only in prose.
