# CI scope

The building-block CI workflow is intentionally limited to portable C++ contracts. It is not a substitute for cross-compiling a bootable kernel image or validating real hardware.

The repository should add target runners/cross-toolchains only when the corresponding architecture implementation exists. This avoids reporting an architecture as supported merely because a header compiles on x86-64.
