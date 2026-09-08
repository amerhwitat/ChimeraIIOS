# W2K-ASM import

The supplied `W2K-ASM.txt` is a large historical assembly corpus. It includes Windows-era x86 critical-section routines and Alpha/PowerPC dynamic-vtable/tearoff routines. The source is preserved as reference material, not silently relicensed or rewritten.

## Local import

```bash
mkdir -p legacy/w2k-asm
cp /path/to/W2K-ASM.txt legacy/w2k-asm/W2K-ASM.txt
sha256sum legacy/w2k-asm/W2K-ASM.txt > legacy/w2k-asm/W2K-ASM.txt.sha256
```

## Why it is separate

Historical assembly often depends on private headers, calling conventions, object layouts and build environments that are not present in Chimera II. The project can learn from patterns such as atomic critical-section acquisition, dynamic thunk dispatch and architecture-specific ABI handling, but those routines should not be copied into the kernel without a clean-room port, tests, and licensing review.

## Related Chimera locations

- `kernel/sched/` — scheduler/locking concepts
- `kernel/ipc/` — synchronization primitives
- `docs/MASTER_SOURCE_MAP.md` — source mapping
- `docs/PROVENANCE.md` — provenance policy
