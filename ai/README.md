# Chimera II OS AI Fabric

The Chimera AI Fabric maps AI disciplines into the OS/application/runtime layers:

- ML: classical statistical learning.
- DL: neural networks and transformers.
- RL: agent/environment/reward loops.
- Symbolic AI: rules, logic, ontology and knowledge graphs.
- CV: images, video and spatial/3D representations.
- NLP: language pipelines, embeddings, transformers and translation.
- Edge AI: local and cooperative inference across IoT/edge devices.
- Multimodal AI: audio, video, vision, speech and language pipelines.

The Fabric is provider-neutral and can route workloads to native C/C++, Python frameworks, containers, CVEL virtual machines, Kubernetes/OpenShift, or cloud adapters already present in the OS.

## Next-generation runtime

The `ai/nextgen/` registry and native `RuntimePlanner` model speculative decoding, Mixture-of-Experts, self-speculative MoE, KV-cache optimization, quantization, sparsity, state-space models, adaptive batching, streaming inference, split inference, federated learning and adaptive resource scheduling. Hardware planning covers CPU/SIMD, RISC-V Vector/matrix, GPU/NPU/FPGA/DSP, CXL memory, NUMA, sched_ext and io_uring integration points.

Parallel execution is exposed through the native `chimera::parallel::Executor`, while IoT/edge integration is represented through MQTT 5, OPC UA PubSub, Thread, Matter, CoAP, BLE, CAN, Modbus and LoRaWAN adapter targets.

AI jobs carry provenance and resource requirements. Model downloads, generated-code execution, hardware mutation, IoT writes and infrastructure mutation are explicit operations rather than automatic side effects.
