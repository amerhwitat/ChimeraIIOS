# Windows application packaging

Chimera's Windows integration accepts two major distribution forms:

- **MSIX/AppX** for packaged Store-oriented distribution and clean install/update semantics.
- **EXE/MSI** for existing Win32 installers, including Store submission through Microsoft's supported installer path.

The Application Center stores package format and provider metadata separately from the execution layer. Windows applications running through compatibility infrastructure remain subject to their own licensing and runtime requirements.
