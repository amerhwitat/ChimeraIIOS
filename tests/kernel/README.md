# Vendored Koronos host tests

Run the bounded Koronos memory/ELF host regressions from the vendored source root:

```bash
bash tests/kernel/run-frame-allocator-host-tests.sh
```

The runner compiles with warnings-as-errors and executes:
- Multiboot2 frame ownership, reservation, double-free and above-4-GiB rejection tests;
- checked physical-mapping range and pre-initialization access tests;
- transactional ELF segment/BSS/stack, W^X, overlap and injected mapping-failure tests;
- the existing process-loader compatibility regression.

The canonical `kernel/build-koronos.sh` invokes this runner before the freestanding build. The tests use synthetic boot maps and mock mapping callbacks; QEMU boot-time address-space self-test remains a separate required check.
