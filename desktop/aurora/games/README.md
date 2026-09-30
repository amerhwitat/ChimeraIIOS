# Aurora Games

Aurora treats appcenter/catalog/game-registry.json as the trusted catalog and
exposes only packages that satisfy source, license, asset-license, checksum,
execution-layer, and Koronos hardware capability gates.

The UI may display CATALOGED and SOURCE_ONLY entries, but installation is
allowed only for registry entries promoted to a verified installable state.
Driver installation is never implicit.

Execution layers: native ELF, Windows PE through Wine/Proton, Godot,
Open 3D Engine, Armory, and emulation.

Hardware inputs are supplied by Koronos; Aurora consumes the capability
profile rather than inventing GPU/CPU support.
