# Perl runtime integration (Perl 5.44.0)

This package adds a reproducible build recipe and acceptance test for upstream Perl.
It pins each CPAN source archive by SHA-256 and runs Perl's own `make test`
suite before staging the interpreter.

- Production stable release: Perl 5.44.0 (released 2026-07-15).
  - Source: https://www.cpan.org/src/5.0/perl-5.44.0.tar.gz
  - SHA-256: `3b855066b92491cb40e86affb1ca57d1a388aa43e51b91c7806a32c2f65f96c3`
- Latest development release: Perl 5.45.3 (released 2026-09-24).
  - Source: https://www.cpan.org/src/5.0/perl-5.45.3.tar.gz
  - SHA-256: `f8aac25c3dc34abbaf0d84da132913f726c7faa27906b460cc442da417c2fdac`
- Stable 5.44.0 remains the default; use `--version development` to build 5.45.3 for testing.

## Build

From the repository root on a POSIX build host with a C compiler, make, tar,
curl or wget, and a SHA-256 utility:

```sh
bash tools/perl-runtime/build-perl-runtime.sh --prefix "$PWD/build/perl-rootfs"
```

The build downloads the pinned source, verifies its digest, configures Perl for
the build host, runs the upstream tests, installs under the staging prefix,
and runs `perl-runtime-smoke.pl`.

## Important execution boundary

This produces a **host-ABI compatibility runtime**, not a native Koronos ELF.
The current custom kernels do not yet demonstrate the full POSIX/libc surface
Perl expects (including a compatible C runtime, process and file APIs, memory
mapping, signals, and dynamic-loader behavior). Therefore the build is
intentionally opt-in and is not inserted into the production ISO or advertised
as native execution. Native availability must remain blocked until the kernel
and userland provide that contract and a booted acceptance test executes Perl
inside the OS itself.

The same source pin, build script, smoke test, and CI contract are mirrored in
ChimeraIIOS and OctavianOS so the two projects do not drift.
