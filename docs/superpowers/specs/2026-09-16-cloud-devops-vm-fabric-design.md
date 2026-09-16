# Chimera II OS Cloud/DevOps/VM Fabric Design

**Date:** 2026-09-16
**Status:** Approved for implementation

## Goal
Extend Chimera II OS from provider discovery and planning into a testable, provider-neutral VM, image, IaC, DevOps, and cluster-management fabric while keeping infrastructure mutation explicit and credential boundaries visible.

## Scope
1. CVEL VM lifecycle and architecture-aware QEMU execution.
2. Safe process execution and guest-image validation/loading.
3. Native Chimera C8192/R8192 execution integration points.
4. Host acceleration discovery with deterministic fallback.
5. VM/image lifecycle operations: create, start, stop, pause, reset, snapshot, restore, export, import.
6. Chimera boot/image builder integration for ISO/cloud-image artifacts.
7. Kubernetes, OpenShift/OKD, and OpenStack adapters and provisioning plans.
8. AWS, Azure, and GCP provider-neutral IaC adapters without embedding credentials.
9. DevOps pipeline model connecting generation, validation, build, VM validation, artifact publication, and deployment gates.
10. CLI and Aurora-facing management APIs.
11. CI validation and provider integration jobs guarded by explicit secrets/environment configuration.

## Architecture
The fabric is layered: `CVEL -> VM/Image Fabric -> Provider Adapters -> DevOps Orchestrator -> CLI/Aurora`. CVEL owns local emulation and VM command construction. Provider adapters own platform-specific validation and plan/apply boundaries. DevOps consumes declarative plans and artifacts but never treats generated code or a successful plan as implicit authorization to mutate infrastructure.

### Core interfaces
- `MachineProfile`: architecture, CPU, memory, disk, firmware, graphics, networking.
- `CommandLine`: executable plus argument vector; no shell-concatenated execution.
- `Backend`: provider capability detection and command generation.
- `VmHandle` / `VmLifecycle`: lifecycle state and operations.
- `GuestImage`: format, architecture, checksum, path, bootability metadata.
- `AccelerationInfo`: host acceleration capabilities and fallback mode.
- `ProviderAdapter`: validate, plan, and explicitly gated apply operations.
- `PipelinePlan`: ordered validation/build/test/image/IaC/deploy stages.

## Safety and failure boundaries
- No automatic download, firmware flashing, destructive destroy, or credential discovery.
- Guest image paths must be explicitly supplied; image architecture must match the requested machine profile.
- Provider credentials are external to the repository and are never written to plans or logs.
- Apply operations require an explicit invocation and a validated plan; CI deployment jobs require protected environment/secrets.
- Subprocesses receive argument vectors rather than shell-concatenated command strings.
- Unsupported architectures/providers return structured errors instead of silently falling back to another target.

## Provider scope
- Local: CVEL/QEMU plus native Chimera execution.
- Kubernetes: manifest validation, context discovery, node/workload planning, and explicit apply.
- OpenShift/OKD: project/workload planning and installer/tool discovery; platform-specific installation remains explicit.
- OpenStack: Terraform-based compute/network/image/volume planning with explicit credentials and apply.
- AWS/Azure/GCP: provider registry and Terraform adapter contracts; concrete resource modules are added only where the provider contract and credential model are explicit.

## Testing strategy
Use TDD for production behavior. Unit tests cover architecture mapping, command arguments, lifecycle state transitions, image validation, acceleration detection, provider plans, and refusal of implicit mutation. Dependency-free validators check JSON/YAML/HCL shape where practical. CI performs CMake build/CTest plus Python validation and optional provider-specific integration jobs.

## Rollout order
1. Harden CVEL command/architecture layer.
2. Add lifecycle/image abstractions.
3. Add native/acceleration interfaces.
4. Add image builder and artifact metadata.
5. Add Kubernetes/OpenShift/OpenStack adapters.
6. Add public-cloud adapter contracts.
7. Add DevOps pipeline orchestration.
8. Integrate CLI/Aurora surfaces.
9. Expand CI and documentation.

## Non-goals
This phase does not silently create public-cloud accounts, obtain credentials, deploy production infrastructure without an explicit gate, or claim provider integration has been live-tested when only static/unit validation is available.
