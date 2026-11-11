# Perl runtime integration (Perl 5.44.0)

This integration adds a reproducible build recipe, a Perl smoke test, and CI-produced runtime packages for both OS repositories. Each CPAN source archive is pinned by SHA-256; CI runs Perl's upstream `make test` suite before publishing the staged interpreter.

- Production stable release: Perl 5.44.0 (released 2026-07-15).
  - Source: https://www.cpan.org/src/5.0/perl-5.44.0.tar.gz
  - SHA-256: `3b855066b92491cb40e86affb1ca57d1a388aa43e51b91c7806a32c2f65f96c3`
- Latest development release: Perl 5.45.3 (released 2026-09-24).
  - Source: https://www.cpan.org/src/5.0/perl-5.45.3.tar.gz
  - SHA-256: `f8aac25c3dc34abbaf0d84da132913f726c7faa27906b460cc442da417c2fdac`
- Stable 5.44.0 is the default; use `--version development` to build 5.45.3 for testing.

## Build locally

On a POSIX build host with a C compiler, make, tar, curl or wget, and a SHA-256 utility:

```sh
bash tools/perl-runtime/build-perl-runtime.sh --prefix "$PWD/build/perl-rootfs"
```

The build downloads the pinned source, verifies its digest, configures Perl for the build host, runs upstream tests, installs under the staging prefix, and runs `perl-runtime-smoke.pl`.

## CI runtime artifacts

The `Perl runtime smoke` workflow builds and tests both channels independently and uploads these 14-day artifacts after successful tests:

- `perl-stable-host-abi` — tarball containing the tested Perl 5.44.0 host-ABI staging tree.
- `perl-development-host-abi` — tarball containing the tested Perl 5.45.3 host-ABI staging tree.

Download these from the successful workflow run's **Artifacts** section. Artifacts are deliberately labeled host-ABI; do not install them into a target with a different ABI or treat their existence as native OS acceptance.

## Native OS execution gate

This produces a **host-ABI compatibility runtime**, not a native Koronos executable. The custom kernels do not yet demonstrate the full POSIX/libc surface Perl expects, including a compatible C runtime and dynamic loader, process and file APIs, memory mapping, and signal behavior. Accordingly, these artifacts are not inserted into production ISOs or advertised as native execution. Native integration remains blocked until a target-compatible build and booted in-OS Perl acceptance test pass.

The source pins, build script, smoke test, CI artifact contract, and manifest are mirrored in ChimeraIIOS and OctavianOS to prevent drift.
