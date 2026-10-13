# DOS compatibility adapter and legacy software policy

The shared command dispatcher routes DOS MZ executables and registered DOS commands
through `chimera-dos-adapter.py`. DOSBox-X is preferred; DOSBox is the fallback.
The emulator provides the guest CPU, conventional/expanded memory, BIOS, interrupt
services, VGA/SVGA, timers, sound and legacy device models supported by that emulator.
This is the supported route for applications that write to DOS memory, invoke BIOS
interrupts, program VGA/sound hardware, or expect a DOS-era memory map.

**Guest memory is not host memory.** Direct writes to a guest address, I/O ports,
BIOS vectors, or DOS kernel structures are emulated inside the virtual PC. Chimera
must never map an untrusted DOS program onto the live Koronos/host kernel address
space or pass raw hardware access through to the host. Software that depends on
undocumented hardware behavior must be tested against the selected machine profile;
some titles may require DOSBox-X, PCem/86Box, QEMU, or a real licensed OS/device model.

## Provider installation and command execution

- Install `dosbox-x` or `dosbox` in the target rootfs; the provider installer tries
  both packages when available from the configured package repositories.
- DOS `.COM`, `.EXE`, and `.BAT` launch targets are passed to the emulator with
  their containing folder mounted as guest drive C:.
- Host folders are mounted read-only by default. Setting `CHIMERA_DOS_WRITABLE=1`
  explicitly opts into guest writes to the selected application/command folder.
  Do not point this at system directories or sensitive user data.
- Named external DOS commands are looked up in `CHIMERA_DOS_BIN` (default
  `/usr/share/chimera/dos/bin`) and executed inside the emulator. Missing commands
  return a clear error; a registry entry is not proof of an installed binary.
- Disk-changing commands must run only against disposable guest disk images, never
  host block devices. The adapter does not expose physical disk devices.
- The adapter does not fetch or execute remote binaries at runtime.

## Legacy games and legal ISO payloads

The game registry is an index, not a blanket redistribution license. The initial
catalog includes FreeDOS repository candidates such as BlockDrop, Bolitaire, Boom,
DOS Defender, Dungeons of Noudar 3D, Eliza, and Emeritus Pong. Their package index is
at https://delphi.icm.edu.pl/pub/dos/freedos/repositories/latest/html/en/games/index.html.
These entries are discovery leads only and are deliberately marked `cataloged`, not
bundled or tested. The FreeDOS project also warns that its linked game sites are
convenience links and not endorsements: https://www.freedos.org/about/games/.

For every payload to be bundled, record its exact source URL, upstream version,
license, SHA-256, architecture/format, emulator profile, and smoke-test status.
Do not bundle commercial game executables, BIOS/ROM images, or proprietary data merely
because they are old or downloadable. Prefer individually license-reviewed releases;
use a separate opt-in downloader/build job to fetch, verify, and stage approved
payloads into the ISO. Never label an untested game as verified.

Suggested acceptance matrix: MZ header validation; .COM/.EXE/.BAT launch; DOS command
payload lookup; argument/metacharacter rejection; guest memory/BIOS/VGA access
contained within the emulator; no host block-device passthrough; ISO payload hashes;
boot-and-launch smoke tests for each bundled title.
