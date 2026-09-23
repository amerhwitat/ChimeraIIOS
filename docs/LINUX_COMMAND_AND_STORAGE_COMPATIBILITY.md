# Chimera II Linux Command and Storage Compatibility

Chimera II treats compatibility as a layered interface: a command may be a native Chimera program, a native service adapter, an installed external executable, shell syntax, or an editor shortcut. The command catalog records that distinction instead of pretending that every Linux/Windows command is implemented by Koronos.

## Storage commands

Chimera II provides native storage command entry points:

- `diskpart` -> `chm-diskpart`
- `parted` -> `chm-parted`
- `fdisk` -> `chm-fdisk`
- `gdisk` -> `chm-gdisk`

The native implementation operates on regular disk-image files without requiring privileged access. Raw block devices require the appropriate privilege and are protected by explicit destructive-operation confirmation. Inspection/listing is separated from write operations.

The design follows the documented DiskPart focus model, GNU Parted's disk-label/partition model, and libfdisk's separation of in-memory partition objects from on-disk label writes. Microsoft documents DiskPart as an administrator-oriented disk/partition/volume interpreter; GNU Parted documents partition tables as disk labels; libfdisk documents label-independent partition abstractions and explicit disklabel writes.

## Native safety model

1. Read-only inspection does not mutate the target.
2. Partition-table writes require an explicit write mode.
3. Destructive operations require `--yes-i-really-mean-it` and a regular-image or explicitly selected block-device target.
4. The default target is never guessed.
5. The implementation refuses to operate on mounted targets unless an explicit override is added by a future storage orchestrator.
6. GPT CRCs are validated before a write when GPT is detected.
7. MBR and GPT are read using fixed-width little-endian structures rather than host ABI structs.

## Regex compatibility

The regex catalog is based on the supplied DEV Community cheatsheet but corrects the common quantifier wording: `+` means one or more, while `*` means zero or more. It also records dialect dependence because regex syntax is not identical across JavaScript, POSIX ERE, PCRE2, Python, Perl, Java, and C++.

## References

- Microsoft DiskPart documentation: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/diskpart
- GNU Parted manual: https://www.gnu.org/software/parted/manual/parted.html
- Linux libfdisk reference: https://www.kernel.org/pub/linux/utils/util-linux/
- DEV Community regex article supplied by the operator: https://dev.to/tylerzey/my-regex-cheatsheet---25-example-regex-rules-38ka
