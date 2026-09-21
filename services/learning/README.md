# Chimera Neural Learning Runtime

The learning runtime is deliberately a user-space service, not arbitrary neural code
inside interrupt context. Koronos exposes a tiny event ABI; Kore starts this service
in parallel with normal user-space services.

The runtime may observe scheduling, device, filesystem, network and application
events. Training must be sandboxed, rate-limited and persisted as a model/data
artifact. It must not silently alter security policy, boot configuration, firmware,
or destructive storage operations.

The initial implementation is an online feature/event collector. A later backend can
use ONNX Runtime, PyTorch, TensorFlow or a native Chimera tensor engine when the
corresponding toolchain is available.
