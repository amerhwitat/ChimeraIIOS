# Building-block verification

The portable contracts are verified by the repository CI workflow using GCC and Clang on GitHub-hosted runners. GitHub documents that Actions workflows can build and test code on repository events and matrix multiple configurations. See the official GitHub Actions documentation for the workflow model.

This layer does not claim hardware validation. AArch64/RISC-V64 exception entry, MMU, interrupt controller, power-management and SoC drivers require target-specific validation.
