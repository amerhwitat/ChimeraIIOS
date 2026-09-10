# All-in-one Chimera II ISO

The ISO is the distribution container for the current bootstrap stage.

It includes:

- Spit Fire/Jasper/GRUB2 boot configuration
- Chimera bootstrap kernel image
- GUI installer integration points
- Application Center catalog and provider metadata
- Linux/Windows/Android application integration metadata
- Mobile device profiles
- Provenance and licensing documentation

The ISO deliberately does not redistribute proprietary store binaries. The Application Center retrieves or launches official distribution channels when permitted.

The current CI artifact is a reproducible bootstrap ISO, not a claim that the entire future Koronos/Aurora stack is already production-complete on bare metal.
