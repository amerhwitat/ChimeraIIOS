# Next-Generation AI, Parallel Computing, Computer Architecture, and IoT Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add provider-neutral next-generation AI, heterogeneous parallel computing, modern computer architecture, and IoT/edge orchestration to Chimera II OS.

**Architecture:** Four interoperable planes: AI inference planning, parallel execution planning, heterogeneous hardware/resource discovery, and IoT/edge device orchestration. Native C++ remains dependency-light; Python exposes optional integrations. External algorithms are adapter targets, not copied source.

**Tech Stack:** C++20, CMake/CTest, Python 3, JSON, optional MLIR/IREE/TVM/ONNX Runtime, RISC-V V/matrix concepts, CXL metadata, sched_ext/io_uring integration points, MQTT 5, OPC UA PubSub, Thread/Matter/CoAP/BLE/CAN/Modbus/LoRaWAN adapters.

**Spec:** `docs/ai/nextgen-2026.md`

## Global Constraints
- Hardware discovery is read-only by default.
- No implicit firmware flashing, overclocking, device reconfiguration, or network mutation.
- IoT connections require explicit endpoint configuration.
- AI model download and generated-code execution remain disabled by default.
- CPU/GPU/NPU/FPGA paths degrade to CPU planning when optional runtimes are absent.
- Parallel APIs must be deterministic and safe with one worker.

## Tasks
1. Add research-backed algorithm, hardware, and IoT registries.
2. Add native AI runtime planning for MoE, speculative decoding, KV-cache, quantized/sparse, batched and streaming inference.
3. Add native parallel task/data execution plus tensor/pipeline/distributed metadata.
4. Add native IoT protocol/device/telemetry abstractions and endpoint validation.
5. Add Python orchestration tools for AI, parallelism, and IoT.
6. Integrate sources, tests, registries, headers, and tools into CMake/CTest/install rules without replacing existing targets.
7. Run focused C++ compilation/tests, Python syntax checks, and inspect the final diff.
