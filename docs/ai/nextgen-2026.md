# Chimera II OS — Next-Generation AI, Parallel Computing, Computer Architecture and IoT

This layer is a provider-neutral integration surface for current 2025–2026 research and production technologies. It deliberately separates **planning/metadata** from optional hardware and network actions.

## AI algorithms and systems

The registry covers speculative decoding, Mixture-of-Experts routing, self-speculative MoE, KV-cache optimization, quantization, structured sparsity, state-space sequence models, adaptive batching, streaming inference, split inference, federated learning, and adaptive resource scheduling. Recent 2026 work reports active research in self-speculative MoE for memory-constrained edge inference and adaptive tensor parallelism across edge clusters. These are represented as strategies/adapters rather than copied implementations.

## Parallel and heterogeneous computing

Chimera now models task, data, tensor, pipeline, graph, heterogeneous and distributed parallelism. The hardware registry includes RISC-V Vector, matrix acceleration, GPU/NPU/FPGA/DSP classes, CXL memory expansion/pooling, NUMA affinity, sched_ext, io_uring and zero-copy I/O. MLIR is the compiler-IR integration point; IREE, TVM and ONNX Runtime are optional deployment/runtime adapters.

## Computer architecture

The design treats CPU, vector, matrix, GPU, NPU and FPGA devices as schedulable resources. CXL is represented as a capability for coherent memory/resource expansion and pooling rather than as a hard dependency. RISC-V Vector is represented as the portable data-parallel ISA layer, while matrix acceleration is a future accelerator capability. Hardware mutation, firmware updates and overclocking are never implicit.

## IoT and edge continuum

The IoT layer supports metadata and adapter targets for MQTT 5, OPC UA PubSub, Thread, Matter, CoAP, BLE, CAN, Modbus and LoRaWAN. MQTT is the default lightweight publish/subscribe target; OPC UA PubSub provides an industrial publish/subscribe model with MQTT/UDP mappings. Device discovery and telemetry buffering are safe by default; network connections, writes and remote commands require explicit configuration.

## AI + IoT continuum

A device can publish sensor telemetry, run a local AI plan, request cooperative edge inference, and return a compact result. The intended flow is:

`Sensor -> IoT adapter -> telemetry buffer -> feature extraction -> AI planner -> CPU/GPU/NPU/edge cluster -> policy/result -> optional MQTT/OPC UA publication`

For constrained devices, split inference and quantization are preferred planning candidates. For larger edge clusters, tensor/data/pipeline parallelism and adaptive scheduling can be selected. Privacy is improved by keeping raw sensor/audio/video data local unless the operator explicitly configures transport.

## Linux integration points

`sched_ext` is represented as an optional scheduler integration because Linux exposes a BPF-defined scheduler class. `io_uring` is represented as an I/O acceleration integration, including zero-copy receive where supported by the kernel/NIC stack. Chimera does not assume these facilities exist on every target.

## Safety and governance

- No automatic model downloads.
- No automatic generated-code execution.
- No automatic network connection.
- No automatic IoT device writes.
- No automatic firmware changes.
- No automatic hardware overclocking.
- Optional providers are detected/planned, not silently installed.

## Research provenance

The architecture is informed by MLIR documentation, Linux `sched_ext` and `io_uring` documentation, RISC-V Vector specifications, CXL specifications/materials, OASIS MQTT 5, OPC UA PubSub, 2026 surveys on parallel AI and edge AI, and 2026 work on self-speculative MoE and edge tensor parallelism.
