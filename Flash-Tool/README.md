# Chimera II OS Flash-Tool

`Flash-Tool` is the native mobile-image validation and packaging frontend for Chimera II OS.

## What it does

- checks that a mobile image exists and is readable;
- reports image size and validation status;
- provides a dry-run fastboot command for an operator-controlled device;
- keeps destructive device writes outside the default program flow.

## Build

### Visual Studio 2022

Open `ChimeraFlashTool.sln`, or run:

```bat
build.bat Release
```

### GNU GCC / Clang

```bash
./build.sh Release
```

### Code::Blocks

Open `ChimeraFlashTool.cbp` and select Debug/Release with the configured GCC/MinGW toolchain.

## Run

```text
chimera_flash_tool inspect image.img
chimera_flash_tool verify image.img
chimera_flash_tool command image.img SERIAL
```

`command` only prints the proposed `fastboot` invocation. It does not execute the device write.

## Integration

The intended pipeline is:

```text
Mobile Microkernel build
        -> kernel / boot artifacts
        -> ISO/image packaging
        -> Flash-Tool inspect
        -> Flash-Tool verify
        -> operator-controlled dry-run command
        -> external verified flashing workflow
```
