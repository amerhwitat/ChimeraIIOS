# Cloud/DevOps/VM Fabric Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the approved CVEL, VM/image, cloud/IaC, DevOps, CLI/Aurora, and CI/CD fabric.

**Architecture:** CVEL owns local VM execution. Provider adapters own Kubernetes, OpenShift, OpenStack, AWS, Azure, and GCP planning/apply gates. DevOps composes validation/build stages. Infrastructure mutation is always explicit.

**Tech Stack:** C++20, CMake/CTest, Python 3, JSON/YAML, Terraform, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-16-cloud-devops-vm-fabric-design.md`

## Global Constraints
- No automatic downloads, firmware flashing, destructive destroy, or credential discovery.
- Explicit guest-image paths and architecture validation.
- Credentials remain external and never enter plans/logs.
- Apply requires explicit invocation and validated plan.
- Process execution uses argv, never shell concatenation.
- Unsupported targets fail explicitly.
- TDD precedes production behavior.
- Completion requires fresh verification evidence.

## Tasks

1. **CVEL:** Test and implement architecture-aware QEMU executable mapping for x86/x86_64/arm/aarch64/riscv32/riscv64/mips/mips64/ppc/ppc64/sparc; fix firmware argument handling.
2. **Process runner:** Add tested no-shell process spawning with argv, timeout, stdout/stderr capture, and missing-executable errors.
3. **VM lifecycle:** Add tested Created/Running/Paused/Stopped/Error state model and lifecycle operations.
4. **Guest images:** Add tested Raw/ISO/ELF/PE/Mach-O inspection, SHA-256, and architecture matching.
5. **Acceleration:** Add tested KVM/WHPX/HVF detection with deterministic fallback.
6. **Artifacts:** Add tested VM snapshot/export/import metadata schema and checksum validation.
7. **Native Chimera:** Add C8192/R8192 backend using existing ISA/runtime entry points without duplication.
8. **Image tooling:** Add `tools/image/chimera_image.py` with inspect/manifest/validate and tests.
9. **Kubernetes:** Add argv-based adapter with context discovery, non-mutating plan, validated explicit apply, and tests.
10. **OpenShift:** Add `oc` adapter with the same plan/apply boundary and tests.
11. **OpenStack:** Expand Terraform with opt-in volume/security-group/floating-IP resources; keep credentials external; test statically and with Terraform when installed.
12. **Public cloud:** Add AWS/Azure/GCP adapter contracts using external CLIs/Terraform and credential-free plans; test without live credentials.
13. **DevOps:** Add pipeline schema/executor for `generate/validate/build/test/vm_validate/artifact/iac_plan/deploy_gate`, with ordering and failure-stop tests.
14. **CLI:** Expose provider and VM lifecycle commands with JSON output, including snapshot/export/import.
15. **Aurora:** Add cloud-fabric status/plan/apply integration contract and tested thin client.
16. **Install/package:** Integrate cloud registries/docs/tools/manifests into CMake and add cloud-tool verification script with installer tests.
17. **CI/CD:** Expand static Ubuntu/Windows validation and protected provider integration workflows; validate all adapters and artifacts.
18. **End-to-end:** Test VM profile -> image manifest -> provider plan -> DevOps plan without mutation; run full available CMake/CTest, Python, shell, JSON/YAML/Terraform checks; reconcile against the design before final documentation commit.

Every task uses RED -> GREEN -> REFACTOR, ends with an independently testable commit, and must not claim success without fresh verification output.