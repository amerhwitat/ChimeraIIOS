# ISO-Tool Output and Dependency Storage

## User chooses the final save location

ISO-Tool must ask the user where the generated ISO should be saved before mastering begins. The GUI provides a directory picker and displays the selected destination. A default suggestion may be offered, but the application must not silently override the user's choice.

Recommended default suggestion on Windows:

```text
%USERPROFILE%\\Downloads\\Chimera-II-ISO-Tool
```

The selected directory is organized as:

```text
<selected-output>/
  iso/                         final ISO images
  boot-images/                 generated BIOS/UEFI/Spit Fire images
  binaries/
    executables/               EXE and executable binary artifacts
    libraries/                 DLL/LIB/A/SO artifacts
  logs/                        build and validation logs
  manifests/                   reproducibility and artifact manifests
```

## Dependency downloads

Dependency discovery may use trusted package-manager sources. Downloaded dependency installers/packages are stored in the current user's profile Downloads directory rather than the source repository:

```text
%USERPROFILE%\\Downloads\\Chimera-II-ISO-Tool\\dependencies
```

The dependency cache is independent of the user-selected ISO output directory. The GUI should show which dependencies are missing, which source/package manager will be used, and the download/cache location before an installation operation.

Installation remains explicit and authorized. ISO-Tool must not download and execute arbitrary remote scripts.

## Boot images and evidence

All generated boot images are retained in `boot-images/` and are also staged into the ISO when appropriate. Generated `.bin`, `.img`, and `.efi` files are retained as independent artifacts so they can be inspected or reused.

If a boot emulator is available, ISO-Tool may run BIOS/UEFI validation and save its logs/evidence beside the generated artifacts. Static generation alone must never be reported as proof that an image successfully booted.

When an assembled Chimera II Spit Fire first-stage binary is unavailable, the tool may create a clearly marked inert fallback container for packaging tests, but it must not label that container bootable.

## ISO contents

The ISO staging tree continues to include the complete selected source under `/src`, generated executables and binary images under `/bin`, libraries under `/lib`, boot assets under `/boot`/`/efi`, applications under `/applications`, and reproducibility information under `/metadata`.
